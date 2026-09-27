"""
Parse and validate the LLM's task-breakdown response.

Validation rules (grounding for THIS feature, since there's no existing
task list to check against):
- Every subtask must have a valid title, description, duration (1-10).
- depends_on_indices must only reference indices STRICTLY LOWER than
  the subtask's own index -- this is what makes cycles structurally
  impossible without even needing cycle.py: a later item can never be
  depended on by an earlier one, by construction.
- Any index reference outside the valid range is dropped, not the
  whole subtask -- partial recovery over total rejection.
"""

import json
import re
from typing import TypedDict


class ParsedSubtask(TypedDict):
    index: int
    title: str
    description: str
    duration_days: int
    depends_on_indices: list[int]


class BreakdownParseError(Exception):
    pass


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    return match.group(1) if match else text


def parse_breakdown(raw_text: str) -> list[ParsedSubtask]:
    cleaned = _strip_markdown_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise BreakdownParseError(f"LLM response was not valid JSON: {e}") from e

    if not isinstance(data, dict) or "subtasks" not in data:
        raise BreakdownParseError("LLM response missing 'subtasks' key")

    raw_subtasks = data["subtasks"]
    if not isinstance(raw_subtasks, list) or not raw_subtasks:
        raise BreakdownParseError("'subtasks' must be a non-empty list")

    if len(raw_subtasks) > 8:
        raw_subtasks = raw_subtasks[:8]  # hard cap, even if LLM ignores the rule

    validated: list[ParsedSubtask] = []

    for i, item in enumerate(raw_subtasks):
        if not isinstance(item, dict):
            continue

        title = item.get("title")
        description = item.get("description")
        duration = item.get("duration_days")
        depends_on = item.get("depends_on_indices", [])

        if not isinstance(title, str) or not title.strip():
            continue
        if not isinstance(description, str):
            description = ""
        if not isinstance(duration, (int, float)):
            duration = 1
        duration = max(1, min(10, int(duration)))

        if not isinstance(depends_on, list):
            depends_on = []

        # Grounding enforcement: only allow references to STRICTLY EARLIER
        # indices in the list we're building (using the loop position `i`,
        # not the LLM's self-reported "index" field, since that field
        # itself could be wrong/manipulated).
        valid_depends_on = [d for d in depends_on if isinstance(d, int) and 0 <= d < i]

        validated.append(
            {
                "index": i,
                "title": title.strip(),
                "description": description.strip(),
                "duration_days": duration,
                "depends_on_indices": valid_depends_on,
            }
        )

    if not validated:
        raise BreakdownParseError(
            "No valid subtasks could be extracted from LLM response"
        )

    return validated
