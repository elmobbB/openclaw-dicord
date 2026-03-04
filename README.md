# OpenClaw AI Backend (Minimal)

Minimal FastAPI backend scaffold with OpenAI as the reasoning agent and the OpenAI image tool (`gpt-image-1`).

## Quick start

```bash
cd openclaw-ai
# Add keys in .env

docker compose up --build
```

## Discord bot

The Discord bot exposes `/openclaw` (text-or-image) and `/openclaw-video` (video) slash commands, and supports `@openclaw` mentions. Mentions default to image generation, or use `@openclaw video <prompt>` for video.

### Required env vars

- `OPENAI_API_KEY`
- `DISCORD_TOKEN`
- `OPENCLAW_API_URL` (optional, default `http://api:8000` when using docker compose)
- `DISCORD_GUILD_ID` (optional, for faster command sync to a single guild)
 - Enable Message Content Intent in the Discord Developer Portal to use `@openclaw` mentions.

### Run bot + API

```bash
docker compose up --build
```

## Endpoint

- `POST /generate-image` with JSON `{ "prompt": "..." }`
- `POST /generate-video` with JSON `{ "prompt": "...", "duration": 5 }` → returns `{ "video_url": "..." }`
- `POST /openclaw` with JSON `{ "prompt": "..." }` → returns `{ "image_url": "..." }` or `{ "text": "..." }`

## Local test

```bash
python scripts/test_openclaw.py "a neon fox in rain"
python scripts/test_openclaw.py "explain what a black hole is"
```
