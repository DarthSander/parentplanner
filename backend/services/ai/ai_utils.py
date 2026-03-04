import json
import logging
import re
from typing import TypeVar, Type

from pydantic import BaseModel, ValidationError

from core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AICallError(Exception):
    """Raised when an AI call fails after all retries."""
    pass


async def call_claude(
    system: str,
    user_message: str,
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 1000,
    messages: list[dict] | None = None,
) -> str:
    """
    Wrapper around the Claude API with retry logic.
    Uses claude-sonnet-4-5 by default for background tasks (cheaper).
    Uses claude-opus-4-6 only for chat (better conversation).
    """
    import anthropic
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
    )

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    if messages is None:
        messages = [{"role": "user", "content": user_message}]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((
            anthropic.RateLimitError,
            anthropic.APIConnectionError,
            anthropic.InternalServerError,
        )),
        before_sleep=lambda retry_state: logger.warning(
            f"AI call retry {retry_state.attempt_number}: {retry_state.outcome.exception()}"
        ),
    )
    async def _call():
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    try:
        return await _call()
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        raise AICallError(f"AI call failed: {e}") from e


def extract_json(text: str) -> str:
    """Extract JSON from an AI response, handling markdown code blocks."""
    # Try markdown code block first
    code_block = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block:
        return code_block.group(1).strip()

    # Try to find first [ or {
    for i, char in enumerate(text):
        if char in "[{":
            depth = 0
            for j in range(i, len(text)):
                if text[j] in "[{":
                    depth += 1
                elif text[j] in "]}":
                    depth -= 1
                if depth == 0:
                    return text[i : j + 1]

    return text.strip()


def parse_json_response(text: str) -> list | dict:
    """Parse JSON from an AI response with fallback."""
    cleaned = extract_json(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed. Raw text: {text[:500]}")
        raise AICallError(f"AI returned invalid JSON: {e}") from e


def validate_json_list(text: str, schema: Type[T]) -> list[T]:
    """
    Parse and validate a JSON array against a Pydantic schema.
    Invalid items are skipped with a warning (graceful degradation).
    """
    raw = parse_json_response(text)
    if not isinstance(raw, list):
        raw = [raw]

    valid_items = []
    for i, item in enumerate(raw):
        try:
            valid_items.append(schema.model_validate(item))
        except ValidationError as e:
            logger.warning(f"Item {i} failed validation: {e}")
            continue

    return valid_items
