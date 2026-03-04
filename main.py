from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from agents.claude_agent import generate_image_url, generate_response

load_dotenv()

app = FastAPI()


class PromptRequest(BaseModel):
    prompt: str


@app.post("/generate-image")
def generate_image(request: PromptRequest):
    image_url = generate_image_url(request.prompt)
    return {"image_url": image_url}


@app.post("/openclaw")
def openclaw(request: PromptRequest):
    return generate_response(request.prompt)
