from __future__ import annotations

import json
import os
from typing import Any, Optional

try:
    from dotenv import load_dotenv
except Exception:  # optional dependency for rule-only execution
    def load_dotenv(*args, **kwargs):
        return False

load_dotenv()


class LLMClient:
    """Thin OpenAI Responses API wrapper.

    The app remains usable without an API key. In that case, all LLM calls return None
    and the deterministic rule engine still produces an audit report.
    """

    def __init__(self, model: Optional[str] = None, enabled: bool = True):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1")
        self.enabled = enabled and bool(os.getenv("OPENAI_API_KEY"))
        self._client = None
        if self.enabled:
            try:
                from openai import OpenAI

                self._client = OpenAI()
            except Exception:
                self.enabled = False
                self._client = None

    def complete_text(
        self,
        system: str,
        user: str,
        temperature: float = 0.1,
        max_output_tokens: int = 1400,
    ) -> Optional[str]:
        if not self.enabled or self._client is None:
            return None
        try:
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            # Newer SDKs expose output_text. Keep a defensive fallback for older shapes.
            if hasattr(response, "output_text") and response.output_text:
                return response.output_text
            data = response.model_dump() if hasattr(response, "model_dump") else response
            return _extract_output_text(data)
        except Exception as exc:  # noqa: BLE001
            return f"LLM_CALL_FAILED: {exc}"

    def complete_json(
        self,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_output_tokens: int = 1800,
    ) -> Optional[dict[str, Any]]:
        text = self.complete_text(
            system=system,
            user=user,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        if not text or text.startswith("LLM_CALL_FAILED"):
            return None
        return _parse_json_object(text)


def _extract_output_text(data: Any) -> Optional[str]:
    if isinstance(data, dict):
        if data.get("output_text"):
            return str(data["output_text"])
        parts: list[str] = []
        for item in data.get("output", []) or []:
            for content in item.get("content", []) or []:
                if content.get("type") == "output_text" and content.get("text"):
                    parts.append(content["text"])
        return "\n".join(parts) if parts else None
    return None


def _parse_json_object(text: str) -> Optional[dict[str, Any]]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                obj = json.loads(text[start : end + 1])
                return obj if isinstance(obj, dict) else None
            except json.JSONDecodeError:
                return None
    return None
