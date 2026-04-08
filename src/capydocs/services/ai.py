"""AI text refinement service using OpenAI."""

import os
from typing import Any

PRESETS: dict[str, str] = {
    "compact": (
        "Summarize and compact this text. Remove unnecessary filler, redundancy, "
        "and verbose phrasing. Keep only the core information and key points. "
        "Preserve the original structure (headings, lists) where useful."
    ),
    "fix": (
        "Polish this text. Fix grammar, spelling, punctuation, and awkward phrasing. "
        "Make it read naturally while keeping the original meaning and tone."
    ),
    "translate_en": "Translate this text to English. Preserve markdown formatting.",
    "translate_ko": "Translate this text to Korean. Preserve markdown formatting.",
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
