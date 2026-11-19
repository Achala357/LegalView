
# services/llm_client.py
import os

from openai import OpenAI


def generate_answer(
    prompt: str,
    model: str = "gpt-4o-mini"
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. "
            "Set this environment variable to use AI-generated answers."
        )

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a legal contract analysis assistant. "
                    "Answer strictly using the provided context. "
                    "You may briefly explain implications if clearly stated."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=500,
    )

    return (response.choices[0].message.content or "").strip()
