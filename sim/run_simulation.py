#!/usr/bin/env python3
"""Runs the BASELINE vs SALESFORCE scenarios over the same synthetic request set.

* **BASELINE** - today's process: shared inbox, no priority or SLA routing, no self-service, and a
  manual warranty lookup that adds handling time.
* **SALESFORCE** - triage-flow priority + SLA routing, the deflection assistant, and an automated
  warranty eligibility check.

Both scenarios are scored with the *same* priority/SLA rules from :mod:`sim.config`, so the SLA
compliance comparison is apples-to-apples. Results are written to ``results/``.

Usage::

    python -m sim.run_simulation --out results/
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from . import assistant, config, metrics, priority_router

WARRANTY_TOPICS = {"Warranty", "Return"}


def load_requests(data_dir: Path) -> pd.DataFrame:
    """Load the generated request set, sorted for deterministic processing."""
    path = data_dir / "requests_baseline.csv"
    if not path.exists():
        raise SystemExit(
            f"missing {path} - run `python data/generate_data.py` first"
        )
    df = pd.read_csv(path, keep_default_na=False)
    df["lifetime_value"] = pd.to_numeric(df["lifetime_value"].replace("", np.nan), errors="coerce")
    df = df.sort_values("request_id").reset_index(drop=True)
    return df


def annotate_triage(df: pd.DataFrame) -> pd.DataFrame:
    """Attach the priority score, band and SLA target every scenario is judged against."""
    df["priority_score"] = [
        priority_router.score_request(ltv, ch, topic)
        for ltv, ch, topic in zip(df["lifetime_value"], df["channel"], df["topic"])
    ]
    df["priority_band"] = df["priority_score"].map(priority_router.priority_band_for_score)
    df["sla_minutes"] = df["priority_score"].map(priority_router.sla_minutes_for_score)
    return df


def assistant_decisions(df: pd.DataFrame, order_lookup: dict) -> list[dict]:
    """Run the deflection assistant over every request (grounded, deterministic, no RNG).

    Grounding uses the request's own timestamp as "today" so order-status and warranty verdicts are
    historically accurate.
    """
    decisions = []
    for text, email, created in zip(df["request_text"], df["customer_email"], df["created_at"]):
        as_of = datetime.fromisoformat(str(created)).date()
        decisions.append(assistant.resolve(text, email, order_lookup, as_of=as_of))
    return decisions


def baseline_scenario(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Today's process: inbox latency, manual warranty lookup, duplicate-work rework, no deflection."""
    n = len(df)
    frt = rng.lognormal(np.log(config.BASELINE_FRT_MEDIAN_MIN), config.BASELINE_FRT_SIGMA, size=n)

    is_warranty_topic = df["topic"].isin(WARRANTY_TOPICS).to_numpy()
    handle = (
        config.BASELINE_HANDLE_MIN
        + np.where(is_warranty_topic, config.BASELINE_MANUAL_WARRANTY_MIN, 0.0)
        + config.BASELINE_REWORK_MIN
    )
    followup = np.where(
        rng.random(n) < config.BASELINE_FOLLOWUP_PROB,
        rng.exponential(config.BASELINE_FOLLOWUP_MEAN_MIN, size=n),
        0.0,
    )

    out = df.copy()
    out["scenario"] = "BASELINE"
    out["frt_minutes"] = frt
    out["handling_minutes"] = handle
    out["age_minutes"] = frt + handle + followup
    out["deflected"] = False
    out["agent"] = df["baseline_agent"]
    out["sla_met"] = out["frt_minutes"] <= out["sla_minutes"]
    return out


def salesforce_scenario(df: pd.DataFrame, rng: np.random.Generator, order_lookup: dict) -> pd.DataFrame:
    """Routed process: priority/SLA triage, assistant deflection, automated warranty check.

    Deflection decisions come from the real assistant (``sim.assistant``), not a fixed fraction, so
    the reported deflection rate is an emergent property of intent routing.
    """
    n = len(df)
    decisions = assistant_decisions(df, order_lookup)
    deflected = np.array([d["deflected"] for d in decisions], dtype=bool)

    frt = np.empty(n)
    # Deflected requests are answered by the assistant almost instantly.
    lo, hi = config.ASSISTANT_RESPONSE_MIN_RANGE
    frt[deflected] = rng.uniform(lo, hi, size=int(deflected.sum()))
    # Everything else is routed by priority band.
    for band, model in config.BAND_FRT_MODEL.items():
        mask = (~deflected) & (df["priority_band"] == band).to_numpy()
        count = int(mask.sum())
        if count == 0:
            continue
        if model[0] == "uniform":
            frt[mask] = rng.uniform(model[1], model[2], size=count)
        else:
            frt[mask] = rng.lognormal(np.log(model[1]), model[2], size=count)

    handle = np.where(deflected, 0.0, config.SALESFORCE_HANDLE_MIN)
    followup = np.where(
        (~deflected) & (rng.random(n) < config.SALESFORCE_FOLLOWUP_PROB),
        rng.exponential(config.SALESFORCE_FOLLOWUP_MEAN_MIN, size=n),
        0.0,
    )

    # Load-balanced assignment across the agent pool for human-handled work only.
    human_ids = df.loc[~deflected, "request_id"].tolist()
    assignment = priority_router.assign_owners(human_ids)

    out = df.copy()
    out["scenario"] = "SALESFORCE"
    out["frt_minutes"] = frt
    out["handling_minutes"] = handle
    out["age_minutes"] = frt + handle + followup
    out["deflected"] = deflected
    out["intent"] = [d["intent"] for d in decisions]
    out["confidence"] = [d["confidence"] for d in decisions]
    out["action_taken"] = [d["action_taken"] for d in decisions]
    out["agent"] = ["assistant" if is_deflected else assignment.get(rid, "unassigned")
                    for rid, is_deflected in zip(df["request_id"], deflected)]
    out["sla_met"] = out["frt_minutes"] <= out["sla_minutes"]
    return out


def _metric_entry(label: str, unit: str, direction: str, baseline: float, salesforce: float) -> dict:
    delta = round(salesforce - baseline, 4)
    pct = round(100.0 * delta / baseline, 2) if baseline else 0.0
    return {
        "label": label,
        "unit": unit,
        "direction": direction,
        "baseline": round(baseline, 4),
        "salesforce": round(salesforce, 4),
        "delta": delta,
        "pct_delta": pct,
    }


def summarize(df: pd.DataFrame) -> dict:
    """Compute the five discovery metrics plus load-balance and volume diagnostics."""
    frt = metrics.first_response_minutes(df["frt_minutes"])
    handled = df[~df["deflected"]]
    counts = handled.groupby("agent").size().tolist() if len(handled) else []
    return {
        "frt_mean": frt["mean"],
        "frt_p90": frt["p90"],
        "sla_compliance_pct": metrics.sla_compliance_pct(df["sla_met"]),
        "deflection_rate_pct": metrics.deflection_rate_pct(df["deflected"]),
        "cases_per_agent_per_day": metrics.cases_per_agent_per_day(
            len(handled), config.AGENT_COUNT, config.WORKING_DAYS_PER_MONTH
        ),
        "backlog_age_hours": metrics.backlog_age_hours(df["age_minutes"]),
        "agent_load_gini": metrics.agent_load_gini(counts),
        "human_handled_requests": int(len(handled)),
        "deflected_requests": int(df["deflected"].sum()),
        "sla_breaches": int((~df["sla_met"]).sum()),
    }


def deflection_by_topic(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby("topic")
        .agg(
            total_requests=("request_id", "count"),
            deflected_requests=("deflected", "sum"),
            avg_confidence=("confidence", "mean"),
        )
        .reset_index()
    )
    grouped["deflection_rate_pct"] = (
        100.0 * grouped["deflected_requests"] / grouped["total_requests"]
    ).round(2)
    grouped["avg_confidence"] = grouped["avg_confidence"].round(4)
    return grouped.sort_values("total_requests", ascending=False).reset_index(drop=True)


def render_markdown(metrics_json: dict, by_topic: pd.DataFrame) -> str:
    m = metrics_json["metrics"]
    lines = [
        "# Simulation results - BASELINE vs SALESFORCE",
        "",
        f"Generated by `{metrics_json['generated_by']}` (seed {metrics_json['seed']}) over "
        f"{metrics_json['dataset']['requests']:,} synthetic requests.",
        "",
        "## Headline metrics (the five from the discovery brief)",
        "",
        "| Metric | Baseline | Salesforce | Delta | % Delta | Better |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for entry in m.values():
        lines.append(
            f"| {entry['label']} | {entry['baseline']:,} | {entry['salesforce']:,} | "
            f"{entry['delta']:,} | {entry['pct_delta']:+.1f}% | {entry['direction']} |"
        )
    diag = metrics_json["diagnostics"]
    lines += [
        "",
        "## Diagnostics",
        "",
        "| Diagnostic | Baseline | Salesforce |",
        "| --- | ---: | ---: |",
        f"| Agent-load Gini | {diag['agent_load_gini']['baseline']} | {diag['agent_load_gini']['salesforce']} |",
        f"| Human-handled requests | {diag['human_handled_requests']['baseline']:,} | {diag['human_handled_requests']['salesforce']:,} |",
        f"| Deflected requests | {diag['deflected_requests']['baseline']:,} | {diag['deflected_requests']['salesforce']:,} |",
        f"| SLA breaches | {diag['sla_breaches']['baseline']:,} | {diag['sla_breaches']['salesforce']:,} |",
        f"| Agent-hours freed / month | - | {diag['agent_hours_freed_per_month']:,} |",
        "",
        "## Deflection by topic (Salesforce scenario, from the assistant)",
        "",
        "| Topic | Requests | Deflected | Deflection % | Avg confidence |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in by_topic.itertuples(index=False):
        lines.append(
            f"| {row.topic} | {int(row.total_requests):,} | {int(row.deflected_requests):,} | "
            f"{row.deflection_rate_pct:.2f}% | {row.avg_confidence:.3f} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results", help="output directory (default: results/)")
    parser.add_argument("--data", default="data", help="input data directory (default: data/)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = annotate_triage(load_requests(Path(args.data)))
    order_lookup = assistant.load_order_lookup(Path(args.data) / "orders.csv")

    baseline = baseline_scenario(df, np.random.default_rng(config.SEED + 1))
    salesforce = salesforce_scenario(df, np.random.default_rng(config.SEED + 2), order_lookup)

    base_summary = summarize(baseline)
    sf_summary = summarize(salesforce)

    # Agent-hours freed: the baseline handling time Northwind no longer spends on deflected work.
    deflected_mask = salesforce["deflected"].to_numpy()
    baseline_handle = baseline["handling_minutes"].to_numpy()
    hours_freed = round(float(baseline_handle[deflected_mask].sum()) / 60.0, 2)

    metrics_json = {
        "generated_by": "sim/run_simulation.py",
        "seed": config.SEED,
        "dataset": {
            "orders": int(pd.read_csv(Path(args.data) / "orders.csv").shape[0]),
            "requests": int(len(df)),
            "agents": config.AGENT_COUNT,
            "working_days": config.WORKING_DAYS_PER_MONTH,
        },
        "analysis_window": {
            "start": config.MONTH_START_ISO,
            "days": config.MONTH_DAYS,
        },
        "metrics": {
            "first_response_minutes_mean": _metric_entry(
                "First response time (mean)", "minutes", "lower",
                base_summary["frt_mean"], sf_summary["frt_mean"],
            ),
            "first_response_minutes_p90": _metric_entry(
                "First response time (p90)", "minutes", "lower",
                base_summary["frt_p90"], sf_summary["frt_p90"],
            ),
            "sla_compliance_pct": _metric_entry(
                "SLA compliance", "percent", "higher",
                base_summary["sla_compliance_pct"], sf_summary["sla_compliance_pct"],
            ),
            "deflection_rate_pct": _metric_entry(
                "Deflection rate", "percent", "higher",
                base_summary["deflection_rate_pct"], sf_summary["deflection_rate_pct"],
            ),
            "cases_per_agent_per_day": _metric_entry(
                "Human-handled cases per agent per day", "cases", "lower",
                base_summary["cases_per_agent_per_day"], sf_summary["cases_per_agent_per_day"],
            ),
            "backlog_age_hours": _metric_entry(
                "Backlog age", "hours", "lower",
                base_summary["backlog_age_hours"], sf_summary["backlog_age_hours"],
            ),
        },
        "diagnostics": {
            "agent_load_gini": {
                "baseline": base_summary["agent_load_gini"],
                "salesforce": sf_summary["agent_load_gini"],
            },
            "human_handled_requests": {
                "baseline": base_summary["human_handled_requests"],
                "salesforce": sf_summary["human_handled_requests"],
            },
            "deflected_requests": {
                "baseline": base_summary["deflected_requests"],
                "salesforce": sf_summary["deflected_requests"],
            },
            "sla_breaches": {
                "baseline": base_summary["sla_breaches"],
                "salesforce": sf_summary["sla_breaches"],
            },
            "agent_hours_freed_per_month": hours_freed,
            "baseline_handling_minutes_per_human_request": round(float(baseline_handle.mean()), 4),
        },
        "deflection_by_topic": deflection_by_topic(salesforce).to_dict(orient="records"),
        "assistant": {
            "source": "sim/assistant.py (intent router over the six P3 topics)",
            "threshold": assistant.DEFAULT_THRESHOLD,
            "deflection_rate_pct": sf_summary["deflection_rate_pct"],
        },
    }

    (out_dir / "metrics.json").write_text(json.dumps(metrics_json, indent=2) + "\n", encoding="utf-8")
    (out_dir / "metrics.md").write_text(
        render_markdown(metrics_json, deflection_by_topic(salesforce)), encoding="utf-8"
    )
    deflection_by_topic(salesforce).to_csv(out_dir / "deflection_by_topic.csv", index=False)

    # Per-request traceability artifact (both scenarios side by side).
    trace = df[["request_id", "topic", "channel", "priority_score", "priority_band", "sla_minutes"]].copy()
    trace["baseline_frt_minutes"] = baseline["frt_minutes"].round(2).to_numpy()
    trace["salesforce_frt_minutes"] = salesforce["frt_minutes"].round(2).to_numpy()
    trace["salesforce_deflected"] = salesforce["deflected"].to_numpy()
    trace["salesforce_intent"] = salesforce["intent"].to_numpy()
    trace["salesforce_confidence"] = salesforce["confidence"].to_numpy()
    trace["salesforce_agent"] = salesforce["agent"].to_numpy()
    trace.to_csv(out_dir / "requests_scored.csv", index=False)

    print(f"wrote {out_dir / 'metrics.json'}")
    print(f"wrote {out_dir / 'metrics.md'}")
    print(f"wrote {out_dir / 'deflection_by_topic.csv'}")
    print(f"wrote {out_dir / 'requests_scored.csv'}")
    print(render_markdown(metrics_json, deflection_by_topic(salesforce)))


if __name__ == "__main__":
    main()
