"""
Thin abstraction over the three model providers you mentioned:
Gemini Flash, Mistral, and Groq. All expose an OpenAI-ish or REST
interface; we normalize to a single `complete(system, user) -> str`.

Swap providers via LLM_PROVIDER in .env with no code changes elsewhere.
"""

from __future__ import annotations
import os
import json
import httpx


class LLMError(RuntimeError):
    pass


async def complete(system: str, user: str, *, json_mode: bool = False) -> str:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "gemini":
        return await _complete_gemini(system, user, json_mode=json_mode)
    if provider == "groq":
        return await _complete_groq(system, user, json_mode=json_mode)
    if provider == "mistral":
        return await _complete_mistral(system, user, json_mode=json_mode)
    raise LLMError(f"Unknown LLM_PROVIDER '{provider}'. Use gemini | groq | mistral.")


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

async def _complete_gemini(system: str, user: str, *, json_mode: bool) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    if not api_key:
        raise LLMError("GEMINI_API_KEY is not set.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": 0.4,
            **({"responseMimeType": "application/json"} if json_mode else {}),
        },
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload)
    if resp.status_code != 200:
        raise LLMError(f"Gemini error {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected Gemini response shape: {data}") from e


# ---------------------------------------------------------------------------
# Groq (OpenAI-compatible chat completions)
# ---------------------------------------------------------------------------

async def _complete_groq(system: str, user: str, *, json_mode: bool) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    if not api_key:
        raise LLMError("GROQ_API_KEY is not set.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.4,
        **({"response_format": {"type": "json_object"}} if json_mode else {}),
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise LLMError(f"Groq error {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected Groq response shape: {data}") from e


# ---------------------------------------------------------------------------
# Mistral (OpenAI-compatible chat completions)
# ---------------------------------------------------------------------------

async def _complete_mistral(system: str, user: str, *, json_mode: bool) -> str:
    api_key = os.getenv("MISTRAL_API_KEY")
    model = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
    if not api_key:
        raise LLMError("MISTRAL_API_KEY is not set.")

    url = "https://api.mistral.ai/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.4,
        **({"response_format": {"type": "json_object"}} if json_mode else {}),
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise LLMError(f"Mistral error {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected Mistral response shape: {data}") from e


def extract_json(text: str) -> dict:
    """LLMs sometimes wrap JSON in ```json fences even when asked not to."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMError(f"Model did not return valid JSON: {e}\n---\n{text[:800]}") from e
