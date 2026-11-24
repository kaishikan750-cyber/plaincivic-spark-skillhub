"""Local OpenAI-compatible client for Spark-X2.6-4B running via llama.cpp server."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict
from typing import Any

import requests


@dataclass
class SparkResponse:
    thinking_mode: str
    model: str
    content: str
    reasoning_content: str
    raw_content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    wall_seconds: float
    tokens_per_sec: float
    finish_reason: str
    request_payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def split_think_blocks(raw_text: str) -> tuple[str, str]:
    """Split inline <think>...</think> reasoning from final answer if server did not separate them."""
    if not raw_text:
        return "", ""
    m = re.search(r"<think>([\s\S]*?)</think>", raw_text)
    if m:
        reasoning = m.group(1).strip()
        cleaned = (raw_text[: m.start()] + raw_text[m.end() :]).strip()
        return cleaned, reasoning
    # Handle truncated unclosed <think> gracefully
    if "<think>" in raw_text and "</think>" not in raw_text:
        idx = raw_text.find("<think>")
        return "", raw_text[idx + len("<think>") :].strip()
    return raw_text.strip(), ""


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Robustly parse the first JSON object from model output (handles markdown fences)."""
    if not text:
        return None
    s = text.strip()
    # Strip markdown code fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", s)
    if fence:
        s = fence.group(1).strip()
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Fallback: scan balanced braces
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = s[start : i + 1]
                    try:
                        obj = json.loads(candidate)
                        if isinstance(obj, dict):
                            return obj
                    except json.JSONDecodeError:
                        break
    return None


class LocalSparkClient:
    """HTTP client targeting local llama-server serving XHToken/Spark-X2.6-4B-GGUF."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        model: str = "Spark-X2.6-4B-Q4_K_M",
        timeout: int = 300,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        # Localhost only: bypass any ambient HTTP_PROXY so requests hit 127.0.0.1 cleanly
        self.session = requests.Session()
        self.session.trust_env = False

    def health(self) -> dict[str, Any]:
        r = self.session.get(f"{self.base_url}/health", timeout=10)
        r.raise_for_status()
        return r.json() if r.content else {"status": "ok"}

    def chat(
        self,
        messages: list[dict[str, str]],
        thinking_mode: str = "low",
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_tokens: int = 2048,
        seed: int = 42,
    ) -> SparkResponse:
        if thinking_mode not in {"none", "low", "high"}:
            raise ValueError(f"Unsupported thinking_mode: {thinking_mode}")

        chat_template_kwargs: dict[str, Any]
        if thinking_mode == "none":
            chat_template_kwargs = {"enable_thinking": False}
        elif thinking_mode == "low":
            chat_template_kwargs = {"enable_thinking": True, "reasoning_effort": "low"}
        else:
            chat_template_kwargs = {"enable_thinking": True, "reasoning_effort": "high"}

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "seed": seed,
            "chat_template_kwargs": chat_template_kwargs,
        }

        t0 = time.perf_counter()
        r = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        wall = time.perf_counter() - t0
        r.raise_for_status()
        data = r.json()

        choice = data["choices"][0]
        msg = choice.get("message", {})
        raw_content = msg.get("content") or ""
        reasoning = msg.get("reasoning_content") or ""

        if not reasoning and "<think>" in raw_content:
            cleaned, extracted_think = split_think_blocks(raw_content)
            content = cleaned
            reasoning = extracted_think
        else:
            content = raw_content.strip()

        usage = data.get("usage", {})
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))
        tps = round(completion_tokens / wall, 2) if wall > 0 and completion_tokens > 0 else 0.0

        return SparkResponse(
            thinking_mode=thinking_mode,
            model=data.get("model", self.model),
            content=content,
            reasoning_content=reasoning,
            raw_content=raw_content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            wall_seconds=round(wall, 3),
            tokens_per_sec=tps,
            finish_reason=choice.get("finish_reason", "unknown"),
            request_payload=payload,
        )
