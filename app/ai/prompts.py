"""
Prompt template for dependency suggestion.

Design choices (important for the "grounding" requirement in the
problem statement):
- The LLM is given ONLY the existing tasks' id/title/description --
  it cannot invent a task that doesn't exist.
- It's told to output STRICT JSON, nothing else, so we can parse
  deterministically without fragile string-matching.
- It must justify every suggestion with a short evidence quote from
  the task text -- this is the "explain grounding" requirement. A
  suggestion with no textual evidence is a hallucination signal.
- Low temperature (0.1) is set at the provider call level, reducing
  creative/random variation for this structured task.
"""

SYSTEM_PROMPT = """You are a project dependency analyst. Your job is to \
suggest which existing tasks a NEW task likely depends on, based ONLY on \
the text provided. You must never invent a task that isn't in the given list.

Rules:
1. Only suggest prerequisite_id values that appear in the "Existing tasks" list.
2. For each suggestion, give a short evidence quote (a phrase from the NEW \
task's own title/description) that justifies why it needs that prerequisite.
3. Give a confidence score from 0 to 100 for each suggestion.
4. If you are not confident about any dependency, return an empty list -- \
do NOT guess just to have an answer.
5. Output ONLY valid JSON, no markdown formatting, no explanation outside \
the JSON structure.
"""

USER_PROMPT_TEMPLATE = """Existing tasks:
{existing_tasks_block}

New task:
ID: {new_task_id}
Title: {new_task_title}
Description: {new_task_description}

Return your answer as JSON in exactly this shape:
{{
  "suggestions": [
    {{
      "prerequisite_id": <int, must be one of the existing task IDs>,
      "evidence": "<short quote from the NEW task's title/description>",
      "reason": "<one sentence explaining the dependency>",
      "confidence": <int 0-100>
    }}
  ]
}}

If there are no confident suggestions, return {{"suggestions": []}}.
"""


def build_prompt(
    new_task_id: int,
    new_task_title: str,
    new_task_description: str,
    existing_tasks: list[dict],
) -> tuple[str, str]:
    """
    existing_tasks: list of {"id": int, "title": str, "description": str}
    Returns (system_prompt, user_prompt).
    """
    existing_tasks_block = "\n".join(
        f"- ID {t['id']}: {t['title']} -- {t.get('description') or '(no description)'}"
        for t in existing_tasks
    )
    if not existing_tasks_block:
        existing_tasks_block = "(no existing tasks)"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        existing_tasks_block=existing_tasks_block,
        new_task_id=new_task_id,
        new_task_title=new_task_title,
        new_task_description=new_task_description or "(no description)",
    )
    return SYSTEM_PROMPT, user_prompt
