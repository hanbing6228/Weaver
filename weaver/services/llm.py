"""Shared LLM JSON completion for storyboard and fate-board UI."""

from __future__ import annotations

import json
import os
from typing import Any


def _google_api_key() -> str | None:
    for name in (
        "WEAVER_GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
        "GOOGLE_AI_API_KEY",
        "GOOGLE_API_KEY",
    ):
        raw = os.environ.get(name)
        if raw and raw.strip():
            return raw.strip()
    return None


def _anthropic_api_key() -> str | None:
    raw = os.environ.get("WEAVER_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    return raw.strip() if raw and raw.strip() else None


def parse_json_text(text: str) -> dict[str, Any] | None:
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def complete_json(system: str, user: str, max_tokens: int = 800) -> dict[str, Any] | None:
    provider = (os.environ.get("WEAVER_LLM_PROVIDER") or "").strip().lower()
    google_key = _google_api_key()
    anthropic_key = _anthropic_api_key()

    if provider in {"google", "gemini"}:
        return _gemini_json(system, user, max_tokens, google_key) if google_key else None
    if provider == "anthropic":
        return _anthropic_json(system, user, max_tokens, anthropic_key) if anthropic_key else None

    if google_key:
        result = _gemini_json(system, user, max_tokens, google_key)
        if result is not None:
            return result
    if anthropic_key:
        return _anthropic_json(system, user, max_tokens, anthropic_key)
    return None


def _gemini_json(
    system: str,
    user: str,
    max_tokens: int,
    api_key: str,
) -> dict[str, Any] | None:
    try:
        import httpx
    except ImportError:
        return None

    models = (
        os.environ.get("GEMINI_MODEL")
        or os.environ.get("WEAVER_GEMINI_MODEL")
        or "gemini-2.0-flash,gemini-1.5-flash"
    )
    for model in [m.strip() for m in models.split(",") if m.strip()]:
        try:
            response = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": 0.7,
                    },
                },
                timeout=60.0,
            )
            response.raise_for_status()
            payload = response.json()
            text = (
                payload.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            parsed = parse_json_text(str(text))
            if parsed is not None:
                return parsed
        except Exception:
            continue
    return None


def _anthropic_json(
    system: str,
    user: str,
    max_tokens: int,
    api_key: str | None,
) -> dict[str, Any] | None:
    if not api_key:
        return None

    try:
        import httpx
    except ImportError:
        return None

    try:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=60.0,
        )
        response.raise_for_status()
        payload = response.json()
        text = "".join(
            block.get("text", "")
            for block in payload.get("content", [])
            if block.get("type") == "text"
        )
        return parse_json_text(text)
    except Exception:
        return None
