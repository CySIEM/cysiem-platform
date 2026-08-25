"""
Shared helper for calling Claude with a forced structured JSON output,
validated against a Pydantic model. This is the enforcement mechanism
mentioned earlier: agents don't just get asked nicely to include
source_host - it's a required field in the schema, and if Claude's
response doesn't validate, we retry once with the validation error fed
back before giving up and routing to DLQ.
"""
from __future__ import annotations
import json
import logging
from typing import Type, TypeVar
from anthropic import Anthropic
from pydantic import BaseModel, ValidationError
from CySIEM.common.config import settings

logger = logging.getLogger("kksiem.agents.base")

T = TypeVar("T", bound=BaseModel)

_client = Anthropic(api_key=settings.anthropic_api_key)


def call_claude_structured(
    system_prompt: str,
    user_prompt: str,
    output_model: Type[T],
    max_tokens: int = 1500,
) -> T:
    """
    Calls Claude, requests JSON-only output matching output_model's schema,
    validates it, retries once on validation failure with the error appended.
    """
    schema_hint = json.dumps(output_model.model_json_schema(), indent=2)
    full_system = (
        f"{system_prompt}\n\n"
        f"You MUST respond with ONLY a single valid JSON object matching this schema, "
        f"no prose, no markdown code fences:\n{schema_hint}"
    )

    for attempt in range(2):
        response = _client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=full_system,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            data = json.loads(text)
            return output_model(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Agent output validation failed (attempt {attempt + 1}): {e}")
            user_prompt = (
                f"{user_prompt}\n\nYour previous response failed validation with error:\n{e}\n"
                f"Return ONLY the corrected JSON object."
            )

    raise ValueError(f"Claude failed to produce valid {output_model.__name__} after 2 attempts")
