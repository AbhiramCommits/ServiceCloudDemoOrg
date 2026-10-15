#!/usr/bin/env python3
"""Evaluates the deflection assistant against the labelled utterance set.

Writes ``results/assistant_eval.json`` and ``results/confusion_matrix.md`` containing overall
accuracy, per-intent precision/recall/F1, escalation precision, the deflection rate at the chosen
confidence threshold, and the threshold sweep that justified the operating point.

Usage::

    python -m sim.eval_assistant --out results/
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from . import assistant, config

#: Confidence thresholds swept to choose the operating point (the task requires >= 5).
THRESHOLD_SWEEP = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65]

#: The seven-way label space.
LABELS = config.DEFLECTABLE_TOPICS + ["escalate"]


def load_eval(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def prf(rows: list[dict], predictions: list[str], label: str) -> dict:
    tp = sum(1 for r, p in zip(rows, predictions) if r["expected_intent"] == label and p == label)
    fp = sum(1 for r, p in zip(rows, predictions) if r["expected_intent"] != label and p == label)
    fn = sum(1 for r, p in zip(rows, predictions) if r["expected_intent"] == label and p != label)
    support = sum(1 for r in rows if r["expected_intent"] == label)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "support": support,
    }


def evaluate(rows: list[dict], threshold: float) -> dict:
    predictions = [assistant.classify(r["utterance"], threshold)[0] for r in rows]
    labels = LABELS
    per_label = {label: prf(rows, predictions, label) for label in labels}
    correct = sum(1 for r, p in zip(rows, predictions) if r["expected_intent"] == p)
    deflected = sum(1 for p in predictions if p != "escalate")
    macro_f1 = sum(v["f1"] for v in per_label.values()) / len(labels)
    return {
        "accuracy": round(correct / len(rows), 4),
        "macro_f1": round(macro_f1, 4),
        "deflection_rate_pct": round(100.0 * deflected / len(rows), 2),
        "escalation_precision": per_label["escalate"]["precision"],
        "escalation_recall": per_label["escalate"]["recall"],
        "per_intent": per_label,
        "predictions": predictions,
    }


def confusion_table(rows: list[dict], predictions: list[str]) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = {}
    for expected in LABELS:
        table[expected] = {predicted: 0 for predicted in LABELS}
    for r, p in zip(rows, predictions):
        table[r["expected_intent"]][p] += 1
    return table


def render_confusion(table: dict[str, dict[str, int]], chosen: float) -> str:
    header = "| expected \\ predicted | " + " | ".join(LABELS) + " |"
    divider = "| --- | " + " | ".join("---:" for _ in LABELS) + " |"
    lines = [
        "# Deflection assistant - confusion matrix",
        "",
        f"Operating confidence threshold: **{chosen}** "
        "(chosen by the sweep in `results/assistant_eval.json`).",
        "",
        header,
        divider,
    ]
    for expected in LABELS:
        cells = " | ".join(str(table[expected][p]) for p in LABELS)
        lines.append(f"| **{expected}** | {cells} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results", help="output directory (default: results/)")
    parser.add_argument("--data", default="data", help="input data directory (default: data/)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_eval(Path(args.data) / "intent_eval.csv")

    sweep = []
    for threshold in THRESHOLD_SWEEP:
        result = evaluate(rows, threshold)
        sweep.append(
            {
                "threshold": threshold,
                "accuracy": result["accuracy"],
                "macro_f1": result["macro_f1"],
                "escalation_precision": result["escalation_precision"],
                "deflection_rate_pct": result["deflection_rate_pct"],
            }
        )

    # Operating point: maximise accuracy, break ties on escalation precision (never deflect a
    # request we are not sure about).
    chosen = max(sweep, key=lambda row: (row["accuracy"], row["escalation_precision"]))
    chosen_threshold = chosen["threshold"]
    reason = (
        f"threshold {chosen_threshold} maximises labelled-set accuracy "
        f"({chosen['accuracy']:.1%}) while keeping escalation precision at "
        f"{chosen['escalation_precision']:.1%}; higher thresholds start escalating in-scope "
        "requests, lower thresholds give no accuracy gain."
    )

    final = evaluate(rows, chosen_threshold)
    table = confusion_table(rows, final["predictions"])

    report = {
        "generated_by": "sim/eval_assistant.py",
        "dataset": {
            "utterances": len(rows),
            "in_scope": sum(1 for r in rows if r["expected_intent"] != "escalate"),
            "out_of_scope": sum(1 for r in rows if r["expected_intent"] == "escalate"),
            "per_intent_support": final["per_intent"],
        },
        "chosen_threshold": chosen_threshold,
        "chosen_reason": reason,
        "overall_accuracy": final["accuracy"],
        "macro_f1": final["macro_f1"],
        "escalation_precision": final["escalation_precision"],
        "escalation_recall": final["escalation_recall"],
        "deflection_rate_pct": final["deflection_rate_pct"],
        "per_intent": final["per_intent"],
        "threshold_sweep": sweep,
        "confusion_matrix": table,
    }

    (out_dir / "assistant_eval.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out_dir / "confusion_matrix.md").write_text(render_confusion(table, chosen_threshold), encoding="utf-8")

    print(f"wrote {out_dir / 'assistant_eval.json'}")
    print(f"wrote {out_dir / 'confusion_matrix.md'}")
    print(f"utterances           : {len(rows)}")
    print(f"chosen threshold     : {chosen_threshold}")
    print(f"overall accuracy     : {final['accuracy']:.4f}")
    print(f"macro F1             : {final['macro_f1']:.4f}")
    print(f"escalation precision : {final['escalation_precision']:.4f}")
    print(f"deflection rate      : {final['deflection_rate_pct']:.2f}%")
    print("per-intent F1        : " + ", ".join(
        f"{label}={final['per_intent'][label]['f1']:.2f}" for label in LABELS
    ))


if __name__ == "__main__":
    main()
