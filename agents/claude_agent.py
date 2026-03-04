import json
import os
from openai import OpenAI

from tools.sora_image import sora_image


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


_SORA_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "sora_image",
            "description": "Generate an image and return its URL.",
            "parameters": {
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
            },
        },
    }
]


def _chat(prompt: str):
    client = _client()
    return client.chat.completions.create(
        model=os.getenv("OPENAI_REASONING_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "If the user is asking for an image, call the sora_image tool. "
                    "Otherwise, answer the question directly with text."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        tools=_SORA_TOOL,
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
    return sora_image(tool_prompt)


def generate_response(prompt: str) -> dict:
    response = _chat(prompt)
    message = response.choices[0].message
    tool_calls = message.tool_calls or []
    if tool_calls:
        arguments = json.loads(tool_calls[0].function.arguments or "{}")
        tool_prompt = arguments.get("prompt", prompt)
        return {"image_url": sora_image(tool_prompt)}
    text = (message.content or "").strip()
    if not text:
        raise RuntimeError("No response content returned")
    return {"text": text}
