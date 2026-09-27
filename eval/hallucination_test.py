"""
Hallucination stress-test: demonstrates what grounding actually
prevents, which the simple yes/no eval (run_eval.py) cannot show.

Design: give the model a POOL of ~10 existing tasks with real IDs.
For each "new task", the description is written to tempt the model
into believing a prerequisite exists that is NOT actually in the pool
(e.g. mentions "after code review" but no "Code Review" task exists
with that exact framing -- testing whether the model invents an ID
or a task that isn't there).

- GROUNDED path: uses the real app/ai/prompts.py + parser.py, which
  filters out any prerequisite_id not in the given pool.
- BASELINE path: a naive prompt that asks for a prerequisite_id
  directly, with NO instruction to only use the given IDs and NO
  post-hoc validation -- this is what "no grounding" really means in
  our multi-task, ID-picking scenario (unlike the earlier yes/no test).

Metric: hallucination rate = how often each approach returns an
prerequisite_id that does not exist in the given pool.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import json
from app.ai.providers.groq_provider import GroqProvider
from app.ai.prompts import build_prompt
from app.ai.parser import parse_suggestions, ParseError

# A pool of 10 existing tasks -- valid IDs are 1 through 10.
TASK_POOL = [
    {
        "id": 1,
        "title": "Design database schema",
        "description": "Define tables for users, orders, products.",
    },
    {
        "id": 2,
        "title": "Set up CI pipeline",
        "description": "Configure GitHub Actions to run tests on push.",
    },
    {
        "id": 3,
        "title": "Create wireframes",
        "description": "Low-fidelity mockups for the checkout flow.",
    },
    {
        "id": 4,
        "title": "Procure server hardware",
        "description": "Order rack servers for the data center.",
    },
    {
        "id": 5,
        "title": "Write unit tests for payment module",
        "description": "Cover edge cases in payment logic.",
    },
    {
        "id": 6,
        "title": "Get legal approval for contract terms",
        "description": "Legal team reviews vendor contract.",
    },
    {
        "id": 7,
        "title": "Collect customer requirements",
        "description": "Interview stakeholders for requirements.",
    },
    {
        "id": 8,
        "title": "Train the ML model",
        "description": "Train a classifier on the labeled dataset.",
    },
    {
        "id": 9,
        "title": "Purchase domain name",
        "description": "Buy taskflowpro.com from a registrar.",
    },
    {
        "id": 10,
        "title": "Design app logo",
        "description": "Create the brand logo in Figma.",
    },
]
VALID_IDS = {t["id"] for t in TASK_POOL}

# New tasks worded to TEMPT hallucination -- they reference a step that
# sounds like it should exist in the pool but doesn't (by that exact
# framing), pushing a naive model to either invent an ID or describe
# a task not actually present.
TEMPTATION_TASKS = [
    {
        "title": "Deploy to production",
        "description": "Deploy only after the code review is approved and QA sign-off is complete.",
    },
    {
        "title": "Launch marketing campaign",
        "description": "Launch after the budget approval from finance is confirmed.",
    },
    {
        "title": "Onboard new hire",
        "description": "Onboarding starts after HR background check clears.",
    },
    {
        "title": "Ship mobile app update",
        "description": "Ship after the app store review process is finished.",
    },
    {
        "title": "Go live with new pricing",
        "description": "Go live after executive sign-off in the pricing committee meeting.",
    },
    {
        "title": "Migrate to new server",
        "description": "Migrate after the data backup verification step confirms integrity.",
    },
]


BASELINE_MULTI_SYSTEM = "You are a helpful assistant that suggests task dependencies."

BASELINE_MULTI_TEMPLATE = """Existing tasks:
{task_list}

New task: {new_title} - {new_description}

Which existing task ID is the most likely prerequisite? Reply with JSON:
{{"prerequisite_id": <int>}}
If genuinely none of the existing tasks are a prerequisite, use null.
"""


def build_baseline_multi_prompt(new_title, new_description):
    task_list = "\n".join(
        f"- ID {t['id']}: {t['title']} -- {t['description']}" for t in TASK_POOL
    )
    user_prompt = BASELINE_MULTI_TEMPLATE.format(
        task_list=task_list, new_title=new_title, new_description=new_description
    )
    return BASELINE_MULTI_SYSTEM, user_prompt


def test_grounded(provider):
    """Uses the REAL pipeline -- parser.py filters any ID not in VALID_IDS."""
    hallucinations = 0
    results = []
    for task in TEMPTATION_TASKS:
        system, user = build_prompt(
            new_task_id=999,
            new_task_title=task["title"],
            new_task_description=task["description"],
            existing_tasks=TASK_POOL,
        )
        try:
            raw = provider.complete(user, system=system, temperature=0.1)
            suggestions = parse_suggestions(raw, valid_task_ids=VALID_IDS)
            # parse_suggestions ALREADY filters invalid IDs -- so if the
            # raw LLM output referenced a bad ID, it's silently dropped
            # here and never reaches this list. We separately check the
            # RAW response below to see if hallucination was attempted.
            raw_ids = _extract_raw_ids(raw)
            invalid_raw_ids = [i for i in raw_ids if i not in VALID_IDS]
            if invalid_raw_ids:
                hallucinations += 1
            results.append(
                {
                    "task": task["title"],
                    "raw_ids_mentioned": raw_ids,
                    "invalid_ids_attempted": invalid_raw_ids,
                    "final_suggestions_after_filtering": [
                        s["prerequisite_id"] for s in suggestions
                    ],
                }
            )
        except (ParseError, Exception) as e:
            results.append({"task": task["title"], "error": str(e)})
    return hallucinations, results


def test_baseline(provider):
    """Naive prompt -- no explicit instruction restricting to valid IDs,
    no post-hoc filtering. Whatever ID it returns is used as-is."""
    hallucinations = 0
    results = []
    for task in TEMPTATION_TASKS:
        system, user = build_baseline_multi_prompt(task["title"], task["description"])
        try:
            raw = provider.complete(user, system=system, temperature=0.1)
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].replace("json", "", 1).strip()
            parsed = json.loads(cleaned)
            prereq_id = parsed.get("prerequisite_id")

            is_hallucination = prereq_id is not None and prereq_id not in VALID_IDS
            if is_hallucination:
                hallucinations += 1
            results.append(
                {
                    "task": task["title"],
                    "returned_id": prereq_id,
                    "is_hallucination": is_hallucination,
                }
            )
        except Exception as e:
            results.append({"task": task["title"], "error": str(e)})
    return hallucinations, results


def _extract_raw_ids(raw_text: str) -> list[int]:
    """Best-effort: find any 'prerequisite_id': <int> mentions in the raw
    text, even ones that fail full JSON parsing, to see what the LLM
    actually tried to reference before our filter removed it."""
    import re

    matches = re.findall(r'"prerequisite_id"\s*:\s*(\d+)', raw_text)
    return [int(m) for m in matches]


if __name__ == "__main__":
    provider = GroqProvider()

    print("=" * 70)
    print("GROUNDED PIPELINE (with ID whitelist + parser filtering)")
    print("=" * 70)
    grounded_hallucinations, grounded_results = test_grounded(provider)
    for r in grounded_results:
        print(r)
    print(
        f"\nHallucination attempts detected in raw output: {grounded_hallucinations}/{len(TEMPTATION_TASKS)}"
    )
    print(
        "(Note: even if the LLM attempted one, parse_suggestions() filtered it out"
        " before it could reach the database -- final_suggestions_after_filtering shows this.)"
    )

    print("\n\n" + "=" * 70)
    print("BASELINE (naive prompt, no ID whitelist enforcement)")
    print("=" * 70)
    baseline_hallucinations, baseline_results = test_baseline(provider)
    for r in baseline_results:
        print(r)
    print(
        f"\nHallucinations that would have reached the database: {baseline_hallucinations}/{len(TEMPTATION_TASKS)}"
    )
