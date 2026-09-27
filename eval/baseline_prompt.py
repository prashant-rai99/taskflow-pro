"""
A deliberately "naive" prompt -- no grounding instructions, no evidence
requirement, no strict validation rules. Used ONLY to demonstrate, via
the eval harness, what the grounded approach (app/ai/prompts.py) adds
over a plain prompt. This file is NOT used anywhere in the real
suggestion pipeline -- eval-only.
"""

BASELINE_SYSTEM_PROMPT = "You are a helpful assistant that suggests task dependencies."

BASELINE_USER_TEMPLATE = """Existing task: {existing_title} - {existing_description}

New task: {new_title} - {new_description}

Does the new task depend on the existing task? Reply with JSON:
{{"depends": true or false}}
"""


def build_baseline_prompt(
    existing_title, existing_description, new_title, new_description
):
    user_prompt = BASELINE_USER_TEMPLATE.format(
        existing_title=existing_title,
        existing_description=existing_description or "(no description)",
        new_title=new_title,
        new_description=new_description or "(no description)",
    )
    return BASELINE_SYSTEM_PROMPT, user_prompt
