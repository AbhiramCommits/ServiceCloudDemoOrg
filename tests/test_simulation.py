"""Tests for the end-to-end simulation: determinism, improvement, and the CLI contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from sim import assistant, config
from sim import eval_assistant as ev
from sim import run_simulation as rs

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

#: Every headline metric with the direction that counts as an improvement.
IMPROVEMENTS = [
    ("frt_mean", "lower"),
    ("frt_p90", "lower"),
    ("sla_compliance_pct", "higher"),
    ("deflection_rate_pct", "higher"),
    ("cases_per_agent_per_day", "lower"),
    ("backlog_age_hours", "lower"),
]


def _summaries() -> tuple[dict, dict]:
    df = rs.annotate_triage(rs.load_requests(DATA))
    order_lookup = assistant.load_order_lookup(DATA / "orders.csv")
    baseline = rs.summarize(rs.baseline_scenario(df, np.random.default_rng(config.SEED + 1)))
    salesforce = rs.summarize(
        rs.salesforce_scenario(df, np.random.default_rng(config.SEED + 2), order_lookup)
    )
    return baseline, salesforce


def test_scenarios_are_deterministic():
    baseline_a, sf_a = _summaries()
    baseline_b, sf_b = _summaries()
    assert baseline_a == baseline_b, "BASELINE scenario is not reproducible"
    assert sf_a == sf_b, "SALESFORCE scenario is not reproducible"


def test_salesforce_improves_every_headline_metric():
    baseline, salesforce = _summaries()
    for key, direction in IMPROVEMENTS:
        before, after = baseline[key], salesforce[key]
        if direction == "lower":
            assert after < before, f"{key} did not fall: {before} -> {after}"
        else:
            assert after > before, f"{key} did not rise: {before} -> {after}"


def test_cli_writes_numeric_values_for_all_five_metrics(tmp_path, monkeypatch):
    out = tmp_path / "results"
    monkeypatch.setattr(sys, "argv", ["run_simulation", "--out", str(out), "--data", str(DATA)])
    rs.main()

    payload = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    for key in [
        "first_response_minutes_mean",
        "first_response_minutes_p90",
        "sla_compliance_pct",
        "deflection_rate_pct",
        "cases_per_agent_per_day",
        "backlog_age_hours",
    ]:
        entry = payload["metrics"][key]
        assert isinstance(entry["baseline"], (int, float))
        assert isinstance(entry["salesforce"], (int, float))
        assert entry["direction"] in {"higher", "lower"}

    assert (out / "metrics.md").exists()
    assert (out / "deflection_by_topic.csv").exists()


def test_assistant_eval_cli_reports_real_scores(tmp_path, monkeypatch):
    out = tmp_path / "results"
    monkeypatch.setattr(sys, "argv", ["eval_assistant", "--out", str(out), "--data", str(DATA)])
    ev.main()

    report = json.loads((out / "assistant_eval.json").read_text(encoding="utf-8"))
    assert report["overall_accuracy"] > 0.85
    assert report["chosen_threshold"] in {row["threshold"] for row in report["threshold_sweep"]}
    assert len(report["threshold_sweep"]) >= 5
    for label in config.DEFLECTABLE_TOPICS + ["escalate"]:
        assert "f1" in report["per_intent"][label]
    assert (out / "confusion_matrix.md").exists()
