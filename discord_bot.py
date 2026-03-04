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


async def _generate_image(prompt: str) -> str:
    base_url = os.getenv("OPENCLAW_API_URL", "http://api:8000").rstrip("/")
    url = f"{base_url}/generate-image"
    logger.info("Calling OpenClaw Image API: %s", url)
    timeout = aiohttp.ClientTimeout(total=90)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json={"prompt": prompt}) as response:
            if response.status != 200:
                detail = await response.text()
                raise RuntimeError(f"OpenClaw API error {response.status}: {detail}")
            data = await response.json()
            image_url = data.get("image_url")
            if not image_url:
                raise RuntimeError("No image_url returned from API")
            return image_url


async def _generate_video(prompt: str) -> str:
    base_url = os.getenv("OPENCLAW_API_URL", "http://api:8000").rstrip("/")
    url = f"{base_url}/generate-video"
    logger.info("Calling OpenClaw Video API: %s", url)
    timeout = aiohttp.ClientTimeout(total=90)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            url,
            json={"prompt": prompt, "duration": 5},
        ) as response:
            if response.status != 200:
                detail = await response.text()
                raise RuntimeError(f"OpenClaw API error {response.status}: {detail}")
            data = await response.json()
            video_url = data.get("video_url")
            if not video_url:
                raise RuntimeError("No video_url returned from API")
            return video_url


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


async def _send_response(target, payload: dict) -> None:
    image_url = payload.get("image_url")
    video_url = payload.get("video_url")
    text = payload.get("text")
    if text:
        logger.info("Sending text response (%d chars)", len(text))
        await target.send(text)
        return
    if video_url:
        logger.info("Sending video response")
        await _send_video(target, video_url)
        return
    if not image_url:
        logger.warning("No text, image_url, or video_url in response payload: %s", payload)
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


async def _send_video(target, video_url: str) -> None:
    if video_url.startswith("data:video/"):
        header, b64 = video_url.split(",", 1)
        data = base64.b64decode(b64)
        file = discord.File(fp=io.BytesIO(data), filename="openclaw.mp4")
        await target.send(file=file)
        return
    if "base64," in video_url:
        _, b64 = video_url.split("base64,", 1)
        data = base64.b64decode(b64)
        file = discord.File(fp=io.BytesIO(data), filename="openclaw.mp4")
        await target.send(file=file)
        return
    await target.send(video_url)


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


@tree.command(name="openclaw-video", description="Generate a video with OpenClaw (Sora)")
@app_commands.describe(prompt="Describe the video you want")
async def openclaw_video(interaction: discord.Interaction, prompt: str) -> None:
    logger.info("Slash command /openclaw-video invoked")
    await interaction.response.defer(thinking=True)
    try:
        video_url = await _generate_video(prompt)
        await _send_video(interaction.followup, video_url)
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
            lowered = prompt.lower()
            if lowered.startswith("video ") or lowered.startswith("video:"):
                video_prompt = prompt.split(" ", 1)[1].strip() if " " in prompt else ""
                if not video_prompt:
                    await message.channel.send("Please provide a prompt after 'video'.")
                    return
                video_url = await _generate_video(video_prompt)
                await _send_video(message.channel, video_url)
            elif lowered.startswith("image ") or lowered.startswith("image:"):
                image_prompt = prompt.split(" ", 1)[1].strip() if " " in prompt else ""
                if not image_prompt:
                    await message.channel.send("Please provide a prompt after 'image'.")
                    return
                image_url = await _generate_image(image_prompt)
                await _send_response(message.channel, {"image_url": image_url})
            else:
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
