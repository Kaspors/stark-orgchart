"""
OpenAI proxy for The Optimistic Weather App.

Handles ChatGPT calls server-side so the API key is never exposed
to the frontend. This is intentionally the most important part of
a joke app.
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/weather", tags=["weather-ai"])

# The system prompt that keeps ChatGPT playing along with the bit.
SYSTEM_PROMPT = """You are the AI backbone of The Optimistic Weather App — a deliberately
optimistic joke weather app. You take meteorology very seriously but present it
with dry, deadpan humour. The app is a parody. You are part of the parody.

You operate in two modes, determined entirely by the user message content:

MODE 1 — FOLLOW-UP QUESTIONS:
When asked to generate follow-up questions based on a user's answer about why
they checked the weather, return ONLY this exact JSON structure:
{"questions": ["First follow-up question?", "Second follow-up question?"]}

Make the questions warmly probe what the user is planning outdoors. Be curious
but not intrusive. Lean into the idea that their plans clearly depend on weather.

MODE 2 — FORECAST ADJUSTMENT:
When given all three Q&A pairs and asked to generate an adjustment, return ONLY:
{
  "temperatureAdjustmentCelsius": <integer, -10 to +10>,
  "precipitationAdjustmentPercentage": <integer, -50 to +20>,
  "summary": "<one dry, slightly sympathetic sentence describing the adjustment>",
  "tone": "<2–3 word editorial stance, e.g. 'cautiously optimistic' or 'legally non-binding'>",
  "activityHint": "<one of: skiing|festival|barbecue|beach|running|hiking — or empty string>"
}

Rules:
- Keep adjustments modest. The app already shows the most optimistic real data.
- Exception: barbecue-related answers. Maximise sunshine aggressively. This is non-negotiable.
- The summary should sound like a press release from a government meteorological department
  that is trying very hard not to get sued.
- activityHint must be exactly one of the listed keywords, or an empty string.
- Return valid JSON ONLY. No markdown, no code fences, no commentary. Pure JSON."""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def weather_chat(req: ChatRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            503,
            detail=(
                "Customise Weather is temporarily offline. "
                "The backend requires OPENAI_API_KEY to be set as an environment variable. "
                "See README for setup instructions."
            ),
        )

    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise HTTPException(
            503,
            detail="The 'openai' package is not installed. Run: pip install openai",
        )

    client = AsyncOpenAI(api_key=api_key)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend([{"role": m.role, "content": m.content} for m in req.messages])

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        return {"reply": response.choices[0].message.content}
    except Exception as exc:
        raise HTTPException(502, detail=f"AI service error: {exc}")
