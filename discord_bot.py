import base64
import io
import logging
import os

import aiohttp
import discord
from discord import app_commands
from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger("openclaw.bot")


def _env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


async def _generate_response(prompt: str) -> dict:
    base_url = os.getenv("OPENCLAW_API_URL", "http://api:8000").rstrip("/")
    url = f"{base_url}/openclaw"
    logger.info("Calling OpenClaw API: %s", url)
    timeout = aiohttp.ClientTimeout(total=90)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json={"prompt": prompt}) as response:
            if response.status != 200:
                detail = await response.text()
                raise RuntimeError(f"OpenClaw API error {response.status}: {detail}")
            return await response.json()


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


async def _send_response(target, payload: dict) -> None:
    image_url = payload.get("image_url")
    text = payload.get("text")
    if text:
        logger.info("Sending text response (%d chars)", len(text))
        await target.send(text)
        return
    if not image_url:
        logger.warning("No text or image_url in response payload: %s", payload)
        await target.send("No response returned from API.")
        return
    logger.info("Sending image response")
    if image_url.startswith("data:image/"):
        header, b64 = image_url.split(",", 1)
        mime = header.split(";")[0].split(":")[1]
        ext = mime.split("/")[-1]
        data = base64.b64decode(b64)
        file = discord.File(fp=io.BytesIO(data), filename=f"openclaw.{ext}")
        await target.send(file=file)
    else:
        await target.send(image_url)


@tree.command(name="openclaw", description="Generate an image with OpenClaw")
@app_commands.describe(prompt="Describe the image you want")
async def openclaw(interaction: discord.Interaction, prompt: str) -> None:
    logger.info("Slash command /openclaw invoked")
    await interaction.response.defer(thinking=True)
    try:
        payload = await _generate_response(prompt)
        await _send_response(interaction.followup, payload)
    except Exception as exc:
        await interaction.followup.send(f"Error: {exc}")


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot or not client.user:
        return
    logger.info("Message received: author=%s channel=%s", message.author, message.channel)
    if client.user not in message.mentions:
        return
    mention = f"<@{client.user.id}>"
    mention_nick = f"<@!{client.user.id}>"
    prompt = message.content.replace(mention, "").replace(mention_nick, "").strip()
    if not prompt:
        logger.info("Mention received without prompt")
        await message.channel.send("Please provide a prompt after the mention.")
        return
    status_msg = await message.channel.send("Working on it...")
    try:
        async with message.channel.typing():
            payload = await _generate_response(prompt)
            await _send_response(message.channel, payload)
    except Exception as exc:
        await message.channel.send(f"Error: {exc}")
    finally:
        try:
            await status_msg.delete()
        except Exception:
            pass


@client.event
async def on_ready() -> None:
    guild_id = os.getenv("DISCORD_GUILD_ID")
    if guild_id:
        guild = discord.Object(id=int(guild_id))
        await tree.sync(guild=guild)
        print(f"Synced commands to guild {guild_id}")
    else:
        await tree.sync()
        print("Synced commands globally")
    print(f"Logged in as {client.user}")


def main() -> None:
    token = _env("DISCORD_TOKEN")
    client.run(token)


if __name__ == "__main__":
    main()
