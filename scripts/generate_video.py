"""
Agnes-AI Video Generator
Generate videos from text prompts, images, or keyframes using the Agnes-AI API.
Supports full response parsing: id, task_id, video_id, status, progress, seconds, size, etc.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

API_URL = "https://apihub.agnes-ai.com/v1/videos"
MODEL_NAME = "agnes-video-v2.0"


def load_api_key():
    """Load API key from .env file or environment variable."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    api_key = os.environ.get("AGNES_API_KEY")
    if api_key:
        return api_key
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip().replace("\r", "")
                if line.startswith("AGNES_API_KEY="):
                    api_key = line.split("=", 1)[1].strip('"').strip("'")
                    if api_key:
                        return api_key
    print("ERROR: API key not found. Set AGNES_API_KEY env var or create scripts/.env with AGNES_API_KEY=your_key")
    sys.exit(1)


def _extract_video_url(status_data):
    """Try multiple locations for the video URL in API response."""
    if "video_url" in status_data and status_data["video_url"]:
        return status_data["video_url"]
    metadata = status_data.get("metadata", {})
    if isinstance(metadata, dict) and metadata.get("url"):
        return metadata["url"]
    output = status_data.get("output", {})
    if isinstance(output, dict) and output.get("video_url"):
        return output["video_url"]
    return None


def _print_task_info(status_data):
    """Print all available task/video info from the response."""
    print("\n  === Task Information ===")
    
    task_id = status_data.get("task_id") or status_data.get("id")
    video_id = status_data.get("video_id") or task_id
    obj_type = status_data.get("object", "video")
    model = status_data.get("model", MODEL_NAME)
    status = status_data.get("status", "unknown")
    progress = status_data.get("progress", None)
    
    print(f"  Object:    {obj_type}")
    print(f"  Task ID:   {task_id}")
    print(f"  Video ID:  {video_id}")
    print(f"  Model:     {model}")
    print(f"  Status:    {status}")
    if progress is not None:
        print(f"  Progress:  {progress}%")
    
    seconds = status_data.get("seconds")
    if seconds:
        print(f"  Duration:  {seconds}s")
    
    size = status_data.get("size")
    if size:
        print(f"  Resolution: {size}")
    
    created_at = status_data.get("created_at")
    if created_at:
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(int(created_at))
            print(f"  Created:   {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        except (ValueError, TypeError):
            print(f"  Created:   {created_at}")
    
    known_keys = {"id", "task_id", "video_id", "object", "model", "status", 
                  "progress", "seconds", "size", "created_at", "video_url", 
                  "metadata", "output", "message"}
    extra = {k: v for k, v in status_data.items() if k not in known_keys}
    if extra:
        print(f"  Extras:    {json.dumps(extra, ensure_ascii=False)}")
    
    print("  ========================\n")


def generate_video(prompt, width=None, height=None, num_frames=121, fps=24, 
                   model=None, output=None, image=None, keyframes=None):
    """Call the Agnes-AI video generation API and download the result.
    
    Supports three modes:
      1. Text-to-Video: prompt only
      2. Image-to-Video: prompt + single image (--image)
      3. Keyframe Animation: prompt + multiple images (--keyframes)
    
    Args:
        prompt: Text description of the video
        width: Video width in pixels (default: 1152)
        height: Video height in pixels (default: 768)
        num_frames: Number of frames (default: 121)
        fps: Frame rate (default: 24)
        model: Model name (default: agnes-video-v2.0)
        output: Output file path (default: output.mp4)
        image: Single source image URL for image-to-video
        keyframes: Comma-separated list of image URLs for keyframe animation
    """
    api_key = load_api_key()
    if model is None:
        model = MODEL_NAME
    if output is None:
        output = "output.mp4"

    # Detect mode
    if keyframes:
        mode = "Keyframe Animation"
        image_urls = [u.strip() for u in keyframes.split(",") if u.strip()]
        if len(image_urls) < 2:
            print("ERROR: Keyframe mode requires at least 2 image URLs (comma-separated)")
            sys.exit(1)
    elif image:
        mode = "Image-to-Video"
        image_urls = [image]
    else:
        mode = "Text-to-Video"
        image_urls = []

    payload = {
        "model": model,
        "prompt": prompt,
        "num_frames": num_frames,
        "frame_rate": fps,
    }
    
    # Add resolution if provided
    if width is not None:
        payload["width"] = width
    if height is not None:
        payload["height"] = height
    
    # Build extra_body for image-to-video and keyframe modes
    if image_urls:
        if keyframes:
            # Keyframe mode: use extra_body with image array + mode flag
            payload["extra_body"] = {
                "image": image_urls,
                "mode": "keyframes",
            }
        else:
            # Single image mode: put image at top level
            payload["image"] = image_urls[0]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"[1/3] [{mode}] Sending request to Agnes-AI API...")
    print(f"  Model: {model}")
    if width and height:
        print(f"  Resolution: {width}x{height}")
    print(f"  Frames: {num_frames} ({num_frames/fps:.1f}s @ {fps}fps)")
    
    if keyframes:
        print(f"  Keyframes: {len(image_urls)} images")
        for i, url in enumerate(image_urls, 1):
            print(f"    [{i}] {url}")
    elif image:
        print(f"  Source Image: {image}")
    
    short_prompt = prompt if len(prompt) <= 80 else prompt[:80] + "..."
    print(f"  Prompt: {short_prompt}")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"\nERROR: HTTP {e.code}")
        print(f"Response: {body}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    # --- Handle synchronous response (video ready immediately) ---
    if "video_url" in result and result["video_url"]:
        _print_task_info(result)
        video_url = result["video_url"]
        print(f"[2/3] Downloading video from: {video_url}")
        download_video(video_url, output)
        _print_task_info(result)
        print(f"\nSUCCESS! Video saved to: {os.path.abspath(output)}")
        return output

    # --- Handle async/task-based response ---
    task_id = result.get("task_id") or result.get("id")
    if task_id:
        video_id = result.get("video_id") or task_id
        print(f"\nVideo generation started (task_id: {task_id})")
        print("Polling for completion... (this may take a few minutes)")

        status_url = result.get("status_url") or result.get("result_url")
        if not status_url:
            status_url = f"{API_URL}/{video_id}"

        while True:
            time.sleep(5)
            try:
                status_req = urllib.request.Request(status_url, headers={"Authorization": f"Bearer {api_key}"})
                with urllib.request.urlopen(status_req, timeout=30) as resp:
                    status_data = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                print(f"Error checking status: {e}")
                return None

            _print_task_info(status_data)

            video_url = _extract_video_url(status_data)
            if video_url:
                print(f"[2/3] Downloading video from: {video_url}")
                download_video(video_url, output)
                _print_task_info(status_data)
                print(f"\nSUCCESS! Video saved to: {os.path.abspath(output)}")
                return output

            task_status = status_data.get("status", "").lower()
            
            if task_status in ("completed", "success"):
                print(f"Task completed but no video URL found.")
                _print_task_info(status_data)
                return None
            elif task_status in ("failed", "error"):
                msg = status_data.get("message", "Unknown error")
                print(f"\nFAILED: {msg}")
                _print_task_info(status_data)
                sys.exit(1)
            else:
                progress = status_data.get("progress", "?")
                print(f"  Status: {task_status} (progress: {progress}%)...")

    print(f"\nUnexpected response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return None


def download_video(url, output_path):
    """Download a video file from URL with progress bar."""
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 8192
            with open(output_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded / total * 100
                        print(f"  {downloaded}/{total} bytes ({pct:.1f}%)", end="\r")
            print()
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI videos with Agnes-AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  Text-to-Video   -- prompt only
  Image-to-Video  -- prompt + --image URL
  Keyframe Anim.  -- prompt + --keyframes "url1,url2[,url3]"

Examples:
  # Text-to-video
  python generate_video.py "A cat walking on the beach at sunset"
  python generate_video.py "Cyberpunk city at night" --width 1920 --height 1080

  # Image-to-video (animate a single image)
  python generate_video.py "The woman slowly turns around and looks back" \\
    --image "https://example.com/portrait.png"

  # Keyframe animation (smooth transition between multiple images)
  python generate_video.py "Smooth cinematic transition between keyframes" \\
    --keyframes "https://example.com/frame1.png,https://example.com/frame2.png" \\
    --output transition.mp4

  # Keyframe with 3 images
  python generate_video.py "Scene morphing through three stages" \\
    --keyframes "https://example.com/a.png,https://example.com/b.png,https://example.com/c.png"
"""
    )
    parser.add_argument("prompt", help="Text prompt describing the video")
    parser.add_argument("--width", type=int, default=1152, help="Video width (default: 1152)")
    parser.add_argument("--height", type=int, default=768, help="Video height (default: 768)")
    parser.add_argument("--num-frames", type=int, default=121, help="Number of frames (default: 121)")
    parser.add_argument("--fps", type=int, default=24, help="Frame rate (default: 24)")
    parser.add_argument("--model", default=None, help=f"Model name (default: {MODEL_NAME})")
    parser.add_argument("--output", default=None, help="Output file path (default: output.mp4)")
    parser.add_argument("--image", default=None, help="Source image URL for image-to-video (single image)")
    parser.add_argument("--keyframes", default=None, 
                        help="Comma-separated image URLs for keyframe animation (min 2 images)")
    args = parser.parse_args()

    generate_video(
        prompt=args.prompt,
        width=args.width,
        height=args.height,
        num_frames=args.num_frames,
        fps=args.fps,
        model=args.model,
        output=args.output,
        image=args.image,
        keyframes=args.keyframes,
    )


if __name__ == "__main__":
    main()