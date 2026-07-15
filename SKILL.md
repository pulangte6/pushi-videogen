---
name: video-gen
description: "Generate AI videos from text prompts, images, or keyframes using the Agnes-AI video generation API. Use when Codex needs to create videos from text descriptions, animate images into video clips, generate smooth transitions between multiple images (keyframe animation), create promotional video content, or convert text/image ideas into video format. Triggers on: video generation, text-to-video, image-to-video, keyframe animation, multi-image transition, AI video creation, prompt-to-video, video clip generation, animate image."
---

# Video Generation Skill

Generate stunning AI videos using the Agnes-AI video API.

## Quick Start

```powershell
# Text-to-video
python scripts/generate_video.py "your prompt here" [--output out.mp4]

# Image-to-video (animate a single image)
python scripts/generate_video.py "motion description" --image "https://example.com/image.png"

# Keyframe animation (smooth transition between multiple images)
python scripts/generate_video.py "cinematic transition" --keyframes "url1,url2[,url3]"
```

## API Endpoint

| Item | Value |
|------|-------|
| **URL** | `https://apihub.agnes-ai.com/v1/videos` |
| **Method** | `POST` (submit) / `GET` (poll status) |
| **Auth** | `Bearer` token in `Authorization` header |
| **API Key** | Stored in `scripts/.env` |

## Prerequisites

1. Ensure `scripts/.env` exists with:
   ```
   AGNES_API_KEY=your_api_key_here
   ```

2. Python 3.7+ required (uses only stdlib — no pip installs needed).

## Parameters

| Parameter | Flag | Default | Description |
|-----------|------|---------|-------------|
| Prompt | positional | required | Text description of desired video |
| Image | `--image` | — | Single source image URL for image-to-video |
| Keyframes | `--keyframes` | — | Comma-separated image URLs for keyframe animation (min 2) |
| Width | `--width` | `1152` | Video width in pixels |
| Height | `--height` | `768` | Video height in pixels |
| Frames | `--num-frames` | `121` | Number of frames (121 ≈ 5s at 24fps) |
| Frame Rate | `--fps` | `24` | Frames per second |
| Model | `--model` | `agnes-video-v2.0` | Video generation model |
| Output | `--output` | `output.mp4` | Output file path |

## Three Usage Modes

### 1. Text-to-Video
Generate a video entirely from a text description.

```powershell
python scripts/generate_video.py "A cat walking on the beach at sunset"
```

### 2. Image-to-Video
Animate a single still image using a motion prompt.

```powershell
python scripts/generate_video.py "The woman slowly turns around and looks back" --image "https://example.com/portrait.png"
```

### 3. Keyframe Animation
Create a smooth cinematic transition between multiple keyframe images.

```powershell
python scripts/generate_video.py "Smooth cinematic transition between keyframes" --keyframes "https://example.com/frame1.png,https://example.com/frame2.png"
```

## Request Payloads

### Text-to-Video

```json
{
  "model": "agnes-video-v2.0",
  "prompt": "A cinematic shot of a cat walking on the beach at sunset",
  "height": 768,
  "width": 1152,
  "num_frames": 121,
  "frame_rate": 24
}
```

### Image-to-Video

```json
{
  "model": "agnes-video-v2.0",
  "prompt": "The woman slowly turns around and looks back at the camera",
  "image": "https://example.com/image.png",
  "num_frames": 121,
  "frame_rate": 24
}
```

### Keyframe Animation

```json
{
  "model": "agnes-video-v2.0",
  "prompt": "Generate a smooth cinematic transition between the keyframes",
  "extra_body": {
    "image": [
      "https://example.com/keyframe1.png",
      "https://example.com/keyframe2.png"
    ],
    "mode": "keyframes"
  },
  "num_frames": 121,
  "frame_rate": 24
}
```

## Response Fields

The API returns JSON with the following fields (sync or async):

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Task ID (alias of `task_id`) |
| `task_id` | string | Task ID for status polling |
| `video_id` | string | Video ID — recommended for fetching results |
| `object` | string | Object type (usually `video`) |
| `model` | string | Model used for generation |
| `status` | string | Task status: `pending` / `in_progress` / `completed` / `failed` |
| `progress` | integer | Progress percentage (0–100) |
| `created_at` | integer | Unix timestamp of task creation |
| `seconds` | string | Video duration in seconds |
| `size` | string | Video resolution (e.g., `1152x768`) |
| `video_url` | string | Direct download URL (when ready) |

## Workflow

1. **Submit** — POST with prompt (+ image/keyframes) → receives `task_id`
2. **Poll** — GET `/v1/videos/{task_id}` until `status=completed`
3. **Download** — Fetch video from `video_url` or `metadata.url`
4. **Info** — Full task metadata printed at each step

## Example Prompts

- `A cinematic shot of a cat walking on the beach at sunset, soft ocean waves, warm golden lighting, realistic motion`
- `A colossal black hole tearing apart a red giant star, gravitational lensing, accretion disk glowing`
- `An ancient stone temple in an enchanted forest with bioluminescent vines and floating light particles`
- `The woman slowly turns around and looks back at the camera, natural facial expression, cinematic camera movement`
- `Camera pans slowly across a mountain landscape at sunrise, clouds drifting, volumetric lighting`
- `Generate a smooth cinematic transition between the keyframes, maintaining visual consistency and natural camera movement`
- `Time-lapse of a flower blooming in a garden, soft sunlight, macro photography style`

## Examples

```powershell
# Text-to-video: basic
python scripts/generate_video.py "A dragon flying through a thunderstorm"

# Text-to-video: custom resolution
python scripts/generate_video.py "Cyberpunk city at night" --width 1920 --height 1080

# Text-to-video: higher frame rate
python scripts/generate_video.py "Slow motion waterfall" --fps 30 --num-frames 181

# Image-to-video: animate a portrait
python scripts/generate_video.py "The woman slowly turns around and looks back" --image "https://example.com/portrait.png"

# Image-to-video: camera pan across landscape
python scripts/generate_video.py "Camera pans across the landscape, clouds moving" --image "https://example.com/scene.jpg" --output landscape.mp4

# Keyframe animation: two images
python scripts/generate_video.py "Smooth cinematic transition between keyframes" --keyframes "https://example.com/frame1.png,https://example.com/frame2.png"

# Keyframe animation: three images
python scripts/generate_video.py "Scene morphing through three stages" --keyframes "https://example.com/a.png,https://example.com/b.png,https://example.com/c.png" --output morph.mp4

# Keyframe with custom settings
python scripts/generate_video.py "Epic transformation sequence" --keyframes "https://example.com/start.png,https://example.com/end.png" --num-frames 181 --fps 30
```

## Troubleshooting

- **API key error**: Check `scripts/.env` or set `AGNES_API_KEY` env var
- **HTTP 429**: Rate limited — wait a moment and retry
- **No video URL after completion**: Check `metadata.url` or `output.video_url` in response
- **Long wait times**: Video generation typically takes 2–5 minutes
- **Image-to-video fails**: Ensure the image URL is publicly accessible and returns a valid image
- **Keyframe mode error**: Requires at least 2 image URLs, comma-separated with no spaces