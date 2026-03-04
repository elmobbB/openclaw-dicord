import json
import os
from openai import OpenAI

from tools.image_tool import generate_image


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


_IMAGE_TOOL = [
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
                    "Otherwise, answer the question directly with text. "
                    "If asked about real-time data (like weather), say you don't have live access."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        tools=_IMAGE_TOOL,
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
        arguments = json.loads(tool_calls[0].function.arguments or "{}")
        tool_prompt = arguments.get("prompt", prompt)
        return {"image_url": generate_image(tool_prompt)}
    text = (message.content or "").strip()
    if not text:
        return {
            "text": "Sorry, I couldn't answer that. Try rephrasing or be more specific."
        }
    return {"text": text}
