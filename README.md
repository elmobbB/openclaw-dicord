# OpenClaw AI Backend (Minimal)

Minimal FastAPI backend scaffold with OpenAI as the reasoning agent and Sora (OpenAI-compatible) as the image tool.

## Quick start

```bash
cd openclaw-ai
# Add keys in .env

docker compose up --build
```

## Discord bot

The Discord bot exposes a `/openclaw` slash command (recommended) and also supports `@openclaw` mention prompts. It calls the API's `/openclaw` endpoint which returns either `image_url` or `text`.

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
- `POST /openclaw` with JSON `{ "prompt": "..." }` → returns `{ "image_url": "..." }` or `{ "text": "..." }`

## Local test

```bash
python scripts/test_openclaw.py "a neon fox in rain"
python scripts/test_openclaw.py "explain what a black hole is"
```
