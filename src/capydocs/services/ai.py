"""AI text refinement service using OpenAI."""

import os
from typing import Any

PRESETS: dict[str, str] = {
    "concise": "Make this text more concise while preserving the meaning.",
    "fix": "Fix grammar, spelling, and punctuation errors. Keep the original tone.",
    "translate_en": "Translate this text to English. Preserve formatting.",
    "translate_ko": "Translate this text to Korean. Preserve formatting.",
    "formal": "Rewrite this text in a more formal, professional tone.",
    "casual": "Rewrite this text in a more casual, friendly tone.",
}

MODEL = "gpt-5-mini"


async def refine_text(
    text: str,
    instruction: str,
    preset: str | None = None,
) -> dict[str, Any]:
    """Refine text using OpenAI gpt-5-mini."""
    from openai import AsyncOpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No API key configured. Set OPENAI_API_KEY environment variable.")

    if preset and preset in PRESETS:
        instruction = PRESETS[preset]

    if not instruction:
        instruction = "Improve this text."

    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a writing assistant. "
                    "The user will give you text and an instruction. "
                    "Return ONLY the refined text, nothing else. "
                    "Do not add explanations, preamble, or formatting wrappers."
                ),
            },
            {"role": "user", "content": f"Instruction: {instruction}\n\nText:\n{text}"},
        ],
    )
    return {
        "refined": response.choices[0].message.content,
        "model": MODEL,
    }
