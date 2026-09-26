"""
Parse and validate the LLM's raw JSON response for dependency suggestions.

This is a critical safety layer: the LLM's output is UNTRUSTED input.
Even with grounding instructions, an LLM can:
- return malformed JSON
- hallucinate a prerequisite_id that doesn't exist
- return a confidence out of range
- wrap the JSON in markdown code fences despite instructions

This module strips/repairs common formatting issues, then strictly
validates every field. Anything that fails validation is dropped,
never silently "fixed" into something the LLM didn't actually say.
"""

import json
import re
from typing import TypedDict


class ParsedSuggestion(TypedDict):
    prerequisite_id: int
    evidence: str
    reason: str
    confidence: int


class ParseError(Exception):
    pass


def _strip_markdown_fences(text: str) -> str:
    """LLMs sometimes wrap JSON in ```json ... ``` despite instructions not to."""
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def parse_suggestions(
    raw_text: str,
    valid_task_ids: set[int],
) -> list[ParsedSuggestion]:
    """
    Parse the LLM's raw text into a validated list of suggestions.
    Invalid individual suggestions are silently dropped (not raised) --
    a partially-good response is still useful. Only a totally unparsable
    response raises ParseError.
    """
    cleaned = _strip_markdown_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ParseError(f"LLM response was not valid JSON: {e}") from e

    if not isinstance(data, dict) or "suggestions" not in data:
        raise ParseError("LLM response missing 'suggestions' key")

    raw_suggestions = data["suggestions"]
    if not isinstance(raw_suggestions, list):
        raise ParseError("'suggestions' must be a list")

    validated: list[ParsedSuggestion] = []

    for item in raw_suggestions:
        if not isinstance(item, dict):
            continue  # skip malformed entry

        prereq_id = item.get("prerequisite_id")
        evidence = item.get("evidence")
        reason = item.get("reason")
        confidence = item.get("confidence")

        # Type checks
        if not isinstance(prereq_id, int):
            continue
        if not isinstance(evidence, str) or not evidence.strip():
            continue
        if not isinstance(reason, str) or not reason.strip():
            continue
        if not isinstance(confidence, (int, float)):
            continue

        confidence = int(confidence)

        # Value checks -- this is the actual GROUNDING enforcement:
        # the LLM must only reference tasks that really exist.
        if prereq_id not in valid_task_ids:
            continue
        if not (0 <= confidence <= 100):
            continue

        validated.append(
            {
                "prerequisite_id": prereq_id,
                "evidence": evidence.strip(),
                "reason": reason.strip(),
                "confidence": confidence,
            }
        )

    return validated
