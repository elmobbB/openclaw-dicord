import json
import os
from openai import OpenAI, OpenAIError

from tools.image_tool import generate_image
from tools.sora_video import generate_video


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate an image and return its URL.",
            "parameters": {
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
            },
        },
    }
    ,
    {
        "type": "function",
        "function": {
            "name": "generate_video",
            "description": "Generate a short video and return its URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "duration": {"type": "integer"},
                },
                "required": ["prompt"],
            },
        },
    },
]


def _chat(prompt: str):
    client = _client()
    return client.chat.completions.create(
        model=os.getenv("OPENAI_REASONING_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "If the user is asking for an image, call the generate_image tool. "
                    "If the user is asking for a video, call the generate_video tool. "
                    "Otherwise, answer the question directly with text. "
                    "If asked about real-time data (like weather), say you don't have live access."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        tools=_TOOLS,
        tool_choice="auto",
    )


def generate_image_url(prompt: str) -> str:
    response = _chat(prompt)
    message = response.choices[0].message
    tool_calls = message.tool_calls or []
    if not tool_calls:
        raise RuntimeError("OpenAI did not request image generation")
    arguments = json.loads(tool_calls[0].function.arguments or "{}")
    tool_prompt = arguments.get("prompt", prompt)
    return generate_image(tool_prompt)


def generate_response(prompt: str) -> dict:
    response = _chat(prompt)
    message = response.choices[0].message
    tool_calls = message.tool_calls or []
    if tool_calls:
        tool = tool_calls[0].function.name
        arguments = json.loads(tool_calls[0].function.arguments or "{}")
        tool_prompt = arguments.get("prompt", prompt)
        if tool == "generate_video":
            duration = arguments.get("duration", 5)
            try:
                duration = int(duration)
            except (TypeError, ValueError):
                duration = 5
            try:
                return {"video_url": generate_video(tool_prompt, duration)}
            except (AttributeError, OpenAIError, RuntimeError):
                placeholder = os.getenv(
                    "SORA_VIDEO_PLACEHOLDER_URL",
                    "https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                )
                return {"video_url": placeholder}
        try:
            return {"image_url": generate_image(tool_prompt)}
        except OpenAIError:
            return {
                "text": (
                    "Your image request was blocked by the safety system. "
                    "Please try a different prompt."
                )
            }
    text = (message.content or "").strip()
    if not text:
        return {
            "text": "Sorry, I couldn't answer that. Try rephrasing or be more specific."
        }
    return {"text": text}
