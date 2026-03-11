import json
import logging
import os
import time
from typing import Any, Optional


def _is_enabled() -> bool:
    return os.getenv("LITELLM_LOG", "0") == "1"


def _redact_headers(text: str) -> str:
    # Basic redaction to avoid leaking keys if they appear in traces
    for key_name in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"]:
        value = os.getenv(key_name)
        if value:
            text = text.replace(value, "***REDACTED***")
    return text


def logged_completion(
    *,
    model: str,
    messages: list[dict[str, str]],
    reasoning_effort: Optional[str] = None,
    api_base: Optional[str] = None,
    **kwargs: Any,
):
    """Wrapper around litellm.completion with optional logging.

    Logging is enabled when LITELLM_LOG=1.
    Logs are written to stdout via logging and optionally to a jsonl file.
    """

    from litellm import completion  # lazy import

    start = time.time()
    response = completion(
        model=model,
        messages=messages,
        reasoning_effort=reasoning_effort,
        api_base=api_base,
        **kwargs,
    )
    elapsed_ms = int((time.time() - start) * 1000)

    if _is_enabled():
        record: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "elapsed_ms": elapsed_ms,
            "model": model,
            "messages": messages,
        }

        content = None
        try:
            content = response.choices[0].message.content
        except Exception:
            content = None
        record["response_text"] = content

        usage = getattr(response, "usage", None)
        if usage is not None:
            record["usage"] = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }

        hidden = getattr(response, "_hidden_params", None)
        if hidden is not None:
            record["cost"] = hidden.get("response_cost")

        out = _redact_headers(json.dumps(record, ensure_ascii=False))
        logging.info(out)

        log_path = os.getenv("LITELLM_LOG_PATH")
        if log_path:
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(out + "\n")
            except Exception:
                pass

    return response
