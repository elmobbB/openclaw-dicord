import os

from openai import OpenAI


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def sora_image(prompt: str) -> str:
    client = _client()
    model = os.getenv("SORA_IMAGE_MODEL", "gpt-image-1")
    response = client.images.generate(
        model=model,
        prompt=prompt,
    )
    image = response.data[0]
    if image.url:
        return image.url
    if image.b64_json:
        return f"data:image/png;base64,{image.b64_json}"
    raise RuntimeError("No image data returned from Sora")
