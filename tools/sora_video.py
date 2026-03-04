import os

from openai import OpenAI


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def generate_video(prompt: str, duration: int) -> str:
    client = _client()
    model = os.getenv("SORA_VIDEO_MODEL", "sora")
    response = client.videos.generate(
        model=model,
        prompt=prompt,
        duration=duration,
    )
    video = response.data[0]
    if getattr(video, "url", None):
        return video.url
    if getattr(video, "b64_json", None):
        return f"data:video/mp4;base64,{video.b64_json}"
    raise RuntimeError("No video data returned from Sora")
