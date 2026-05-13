"""AI chat service — xAI (Grok) / Gemini integration with deterministic fallback."""

import random
from typing import Tuple

from app.config import get_settings

settings = get_settings()

DISCLAIMER = (
    "⚠️ This AI assistant provides general health information only. "
    "It does not diagnose conditions. Always consult a qualified healthcare professional."
)

FALLBACK_REPLIES = [
    (
        "Thank you for reaching out. Based on general medical knowledge, "
        "I recommend staying hydrated, getting adequate rest, and monitoring your symptoms. "
        "If symptoms persist or worsen, please schedule a consultation with a doctor."
    ),
    (
        "That's a great question. General wellness advice includes maintaining a balanced diet, "
        "regular exercise, and routine check-ups. For specific concerns, a healthcare professional "
        "can provide personalized guidance."
    ),
    (
        "I understand your concern. While I can't provide a diagnosis, common self-care measures "
        "include rest, adequate fluid intake, and over-the-counter remedies as appropriate. "
        "Please seek immediate care if you experience severe symptoms."
    ),
    (
        "Thank you for your question. Prevention is key in healthcare — regular screenings, "
        "vaccinations, and healthy lifestyle choices significantly reduce many health risks. "
        "Please consult your doctor for personalized recommendations."
    ),
    (
        "I'm here to help with general health information. Your described symptoms may have "
        "several possible causes. A proper clinical evaluation by a licensed physician is essential "
        "for accurate diagnosis and treatment."
    ),
]

SYSTEM_PROMPT = """You are MediAssist, a knowledgeable and compassionate AI medical assistant 
for a hospital management system. You provide general health information and guidance.

Important guidelines:
- Always clarify that you cannot provide medical diagnoses
- Encourage users to consult qualified healthcare professionals for serious concerns
- Provide evidence-based general health information
- Be empathetic and professional in all responses
- If someone describes an emergency, advise them to call emergency services immediately
- Keep responses concise but informative (2-4 paragraphs max)
"""


async def get_ai_reply(message: str) -> Tuple[str, str]:
    """
    Returns (reply_text, provider_name).
    Tries xAI (Grok) first, then Gemini, then falls back to canned replies.
    """
    import logging
    logger = logging.getLogger(__name__)

    # 1) Try xAI (Grok)
    if settings.xai_api_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.xai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.xai_model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": message},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1024,
                    },
                )
                if resp.status_code != 200:
                    logger.error(f"xAI HTTP {resp.status_code} [{settings.xai_model}]: {resp.text}")
                resp.raise_for_status()
                reply = resp.json()["choices"][0]["message"]["content"].strip()
                return reply, "xai"
        except Exception as exc:
            logger.error(f"xAI error [{settings.xai_model}]: {exc}")

    # 2) Try Gemini
    if settings.gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                system_instruction=SYSTEM_PROMPT,
            )
            response = model.generate_content(message)
            reply = response.text.strip()
            return reply, "gemini"
        except Exception as exc:
            logger.warning(f"Gemini error: {exc}")

    # 3) Fallback — deterministic based on message hash for consistency
    idx = hash(message[:50]) % len(FALLBACK_REPLIES)
    reply = FALLBACK_REPLIES[idx]
    return reply, "fallback"
