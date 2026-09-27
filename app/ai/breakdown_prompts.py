"""
Prompt for the task-breakdown generator: given a feature description,
propose a set of sub-tasks with dependencies between them.

Unlike the single-dependency suggester, there's no existing-task
grounding here (there ARE no existing tasks yet -- we're creating them).
Instead, grounding takes a different form: the LLM must keep dependency
references INTERNAL to its own proposed list (using 0-based indices),
never invent a reference outside the list it just generated. We
validate that separately in the parser.
"""

BREAKDOWN_SYSTEM_PROMPT = """You are a project planning assistant. Given a \
feature description, break it into a small number of concrete, ordered \
sub-tasks with dependencies between them.

Rules:
1. Propose between 3 and 8 sub-tasks. Do not over-decompose trivial features.
2. Each sub-task needs a short title, a one-sentence description, and an \
estimated duration in days (integer, 1-10).
3. Dependencies are expressed as indices INTO YOUR OWN proposed list \
(0-based). A sub-task can only depend on sub-tasks that appear EARLIER \
in your list (lower index) -- this guarantees no cycles.
4. Output ONLY valid JSON, no markdown, no explanation outside the JSON.
"""

BREAKDOWN_USER_TEMPLATE = """Feature description:
{feature_description}

Return your answer as JSON in exactly this shape:
{{
  "subtasks": [
    {{
      "index": 0,
      "title": "<short title>",
      "description": "<one sentence>",
      "duration_days": <int 1-10>,
      "depends_on_indices": [<indices of earlier subtasks this depends on, can be empty>]
    }}
  ]
}}
"""


def build_breakdown_prompt(feature_description: str) -> tuple[str, str]:
    user_prompt = BREAKDOWN_USER_TEMPLATE.format(
        feature_description=feature_description
    )
    return BREAKDOWN_SYSTEM_PROMPT, user_prompt
