from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

import logging
import os

from agents.claude_agent import generate_image_url, generate_response
from openai import OpenAIError
from tools.sora_video import generate_video

load_dotenv()

app = FastAPI()
logger = logging.getLogger("openclaw.api")


class PromptRequest(BaseModel):
    prompt: str


class VideoRequest(BaseModel):
    prompt: str
    duration: int = 5


@app.post("/generate-image")
def generate_image(request: PromptRequest):
    image_url = generate_image_url(request.prompt)
    return {"image_url": image_url}


@app.post("/openclaw")
def openclaw(request: PromptRequest):
    return generate_response(request.prompt)


@app.post("/generate-video")
def generate_video_endpoint(request: VideoRequest):
    try:
        video_url = generate_video(request.prompt, request.duration)
        return {"video_url": video_url}
    except (AttributeError, RuntimeError, OpenAIError) as exc:
        logger.warning("Video generation unavailable: %s", exc)
        placeholder = os.getenv(
            "SORA_VIDEO_PLACEHOLDER_URL",
            "https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        )
        return {"video_url": placeholder}
