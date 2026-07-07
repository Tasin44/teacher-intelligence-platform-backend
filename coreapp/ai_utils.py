"""
Centralized OpenAI client utilities.

Provides a singleton client (connection reuse), shared retry logic with
exponential backoff, and token-usage logging for cost monitoring.
All AI services across the project should use these helpers instead of
creating their own OpenAI client instances.
"""
import json
import logging
import time

from django.conf import settings
from openai import OpenAI, OpenAIError

logger = logging.getLogger("classroom_app")

# ─── Singleton client ─────────────────────────────────
_client_instance: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """
    Return a shared OpenAI client (connection reuse across requests).
    Raises AIServiceError if OPENAI_API_KEY is not configured.
    """
    global _client_instance
    if _client_instance is None:
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            raise AIServiceError("OPENAI_API_KEY is not configured in settings / .env")
        _client_instance = OpenAI(api_key=api_key, timeout=30.0)
    return _client_instance


class AIServiceError(Exception):
    """Raised when an AI service call fails after all retries."""
    pass


# ─── Retry helper ─────────────────────────────────────
def call_openai_with_retry(
    *,
    messages: list[dict],
    model: str | None = None,
    response_format: dict | None = None,
    temperature: float = 0.5,
    top_p: float = 0.9,
    max_tokens: int = 1200,
    max_retries: int = 3,
    initial_backoff: float = 1.0,
) -> dict:
    """
    Call OpenAI chat completions with exponential-backoff retry.

    Returns the parsed JSON content dict on success.
    Raises AIServiceError after exhausting all retries.
    """
    client = get_openai_client()
    model = model or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format=response_format or {"type": "json_object"},
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )

            raw_content = response.choices[0].message.content
            parsed = json.loads(raw_content)

            # Log token usage for cost monitoring
            usage = response.usage
            if usage:
                logger.info(
                    "OpenAI usage — model=%s prompt_tokens=%d completion_tokens=%d total_tokens=%d",
                    model,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    usage.total_tokens,
                )

            return parsed

        except (OpenAIError, json.JSONDecodeError, KeyError, IndexError) as exc:
            last_exception = exc
            if attempt < max_retries:
                backoff = initial_backoff * (2 ** (attempt - 1))
                logger.warning(
                    "OpenAI call attempt %d/%d failed: %s — retrying in %.1fs",
                    attempt,
                    max_retries,
                    exc,
                    backoff,
                )
                time.sleep(backoff)
            else:
                logger.error(
                    "OpenAI call failed after %d attempts: %s",
                    max_retries,
                    exc,
                )

    raise AIServiceError(
        f"AI call failed after {max_retries} retries: {last_exception}"
    )
