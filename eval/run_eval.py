"""
Eval harness: runs the labeled dataset through the AI suggestion
pipeline and measures precision/recall against ground truth.

Two evaluations run:
1. GROUNDED -- using the real app/ai/prompts.py (evidence required,
   strict JSON, only real task IDs allowed).
2. BASELINE -- a naive plain prompt with no grounding rules, used only
   to show what grounding adds over a simple approach.

Usage: run from the project root with the venv activated:
    python eval/run_eval.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from app.ai.providers.groq_provider import GroqProvider
from app.ai.prompts import build_prompt
from app.ai.parser import parse_suggestions, ParseError
from eval.dataset import EVAL_DATASET
from eval.baseline_prompt import build_baseline_prompt


def evaluate_grounded(provider, dataset):
    """Uses the REAL suggestion pipeline (grounded prompt + parser/validator)."""
    tp = fp = fn = tn = 0
    details = []

    for item in dataset:
        existing = [
            {
                "id": 1,
                "title": item["existing_task"]["title"],
                "description": item["existing_task"]["description"],
            }
        ]

        system, user = build_prompt(
            new_task_id=2,
            new_task_title=item["new_task"]["title"],
            new_task_description=item["new_task"]["description"],
            existing_tasks=existing,
        )

        try:
            raw = provider.complete(user, system=system, temperature=0.1)
            suggestions = parse_suggestions(raw, valid_task_ids={1})
            predicted = len(suggestions) > 0
        except (ParseError, Exception):
            predicted = False
            suggestions = []

        actual = item["label"]

        if predicted and actual:
            tp += 1
            outcome = "TP"
        elif predicted and not actual:
            fp += 1
            outcome = "FP"
        elif not predicted and actual:
            fn += 1
            outcome = "FN"
        else:
            tn += 1
            outcome = "TN"

        details.append(
            {
                "id": item["id"],
                "existing": item["existing_task"]["title"],
                "new": item["new_task"]["title"],
                "actual": actual,
                "predicted": predicted,
                "outcome": outcome,
                "confidence": suggestions[0]["confidence"] if suggestions else None,
            }
        )

    return _compute_metrics(tp, fp, fn, tn, details)


def evaluate_baseline(provider, dataset):
    """Uses a NAIVE prompt with no grounding rules -- eval-only, for comparison."""
    tp = fp = fn = tn = 0
    details = []

    for item in dataset:
        system, user = build_baseline_prompt(
            item["existing_task"]["title"],
            item["existing_task"]["description"],
            item["new_task"]["title"],
            item["new_task"]["description"],
        )
        try:
            raw = provider.complete(user, system=system, temperature=0.1)
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].replace("json", "", 1).strip()
            parsed = json.loads(cleaned)
            predicted = bool(parsed.get("depends", False))
        except Exception:
            predicted = False

        actual = item["label"]

        if predicted and actual:
            tp += 1
            outcome = "TP"
        elif predicted and not actual:
            fp += 1
            outcome = "FP"
        elif not predicted and actual:
            fn += 1
            outcome = "FN"
        else:
            tn += 1
            outcome = "TN"

        details.append(
            {
                "id": item["id"],
                "existing": item["existing_task"]["title"],
                "new": item["new_task"]["title"],
                "actual": actual,
                "predicted": predicted,
                "outcome": outcome,
                "confidence": None,
            }
        )

    return _compute_metrics(tp, fp, fn, tn, details)


def _compute_metrics(tp, fp, fn, tn, details):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        (2 * precision * recall / (precision + recall))
        if (precision + recall) > 0
        else 0.0
    )
    accuracy = (tp + tn) / len(details) if details else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        "details": details,
    }


def print_report(provider_name, results):
    print(f"\n{'='*60}")
    print(f"Provider: {provider_name}")
    print(f"{'='*60}")
    print(
        f"TP={results['tp']}  FP={results['fp']}  FN={results['fn']}  TN={results['tn']}"
    )
    print(f"Precision: {results['precision']:.2%}")
    print(f"Recall:    {results['recall']:.2%}")
    print(f"F1 Score:  {results['f1']:.2%}")
    print(f"Accuracy:  {results['accuracy']:.2%}")
    print(
        f"\n{'ID':<4}{'Actual':<8}{'Pred':<8}{'Outcome':<8}{'Conf':<6} Existing -> New"
    )
    for d in results["details"]:
        conf = d["confidence"] if d["confidence"] is not None else "-"
        print(
            f"{d['id']:<4}{str(d['actual']):<8}{str(d['predicted']):<8}{d['outcome']:<8}{str(conf):<6} "
            f"{d['existing']} -> {d['new']}"
        )


def save_markdown_report(provider_name, results, filepath):
    lines = [
        f"# Eval Results: {provider_name}\n",
        f"- **Dataset size**: {len(results['details'])} labeled task pairs",
        f"- **Precision**: {results['precision']:.2%}",
        f"- **Recall**: {results['recall']:.2%}",
        f"- **F1 Score**: {results['f1']:.2%}",
        f"- **Accuracy**: {results['accuracy']:.2%}",
        f"- **Confusion**: TP={results['tp']} FP={results['fp']} FN={results['fn']} TN={results['tn']}\n",
        "## Per-item results\n",
        "| ID | Actual | Predicted | Outcome | Confidence | Existing Task | New Task |",
        "|---|---|---|---|---|---|---|",
    ]
    for d in results["details"]:
        conf = d["confidence"] if d["confidence"] is not None else "-"
        lines.append(
            f"| {d['id']} | {d['actual']} | {d['predicted']} | {d['outcome']} | {conf} | "
            f"{d['existing']} | {d['new']} |"
        )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    groq_provider = GroqProvider()

    print("Running GROUNDED eval on Groq (openai/gpt-oss-120b)...")
    grounded_results = evaluate_grounded(groq_provider, EVAL_DATASET)
    print_report("Groq GROUNDED (real pipeline)", grounded_results)
    save_markdown_report(
        "Groq GROUNDED (real pipeline)", grounded_results, "eval/results_grounded.md"
    )
    print("\nSaved grounded report to eval/results_grounded.md")

    print("\n\nRunning BASELINE (ungrounded) eval on Groq...")
    baseline_results = evaluate_baseline(groq_provider, EVAL_DATASET)
    print_report("Groq BASELINE (ungrounded)", baseline_results)
    save_markdown_report(
        "Groq BASELINE (ungrounded)", baseline_results, "eval/results_baseline.md"
    )
    print("\nSaved baseline report to eval/results_baseline.md")
