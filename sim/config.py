"""Shared configuration for the simulation harness.

**Single source of truth** for the constants that are deliberately duplicated between the
deployable Apex / Flow metadata and this Python harness:

* the priority scoring weights (``PriorityRouter.cls``, ``Support_Request_Triage`` flow)
* the priority-band -> SLA matrix (same two artifacts)
* the agent pool, working-day model and loaded labor cost used by the value model

If a constant changes in Apex it must change here too, and ``tests/test_metadata.py`` guards the
obvious drift by asserting the Apex and Python values agree.
"""

from __future__ import annotations

# --------------------------------------------------------------------------------------------------
# Priority scoring (mirrors PriorityRouter.cls)
# --------------------------------------------------------------------------------------------------

#: (threshold, points) evaluated highest-first. Lifetime value in USD.
LTV_TIERS: list[tuple[float, int]] = [(2000, 40), (1000, 30), (500, 20), (100, 10)]

#: Intake channel urgency.
CHANNEL_POINTS: dict[str, int] = {"Phone": 20, "Chat": 15, "Web": 10, "Email": 5}

#: Topic urgency. Warranty and Return are the highest-stakes recurring questions.
TOPIC_POINTS: dict[str, int] = {
    "Warranty": 25,
    "Return": 20,
    "Order Status": 15,
    "Shipping": 10,
    "Other": 8,
    "Sizing": 5,
    "Store Hours": 0,
}

#: Scoring band boundaries.
MIN_SCORE = 5
MAX_SCORE = 85

# --------------------------------------------------------------------------------------------------
# SLA matrix: (score_threshold, minutes_allowed, band) evaluated highest-first.
# --------------------------------------------------------------------------------------------------
SLA_MATRIX: list[tuple[int, int, str]] = [
    (70, 15, "Critical"),
    (50, 60, "High"),
    (30, 180, "Medium"),
    (15, 480, "Low"),
    (0, 1440, "Minimal"),
]

# --------------------------------------------------------------------------------------------------
# The six recurring questions from pain P3.
# --------------------------------------------------------------------------------------------------
DEFLECTABLE_TOPICS: list[str] = [
    "Order Status",
    "Return",
    "Warranty",
    "Shipping",
    "Sizing",
    "Store Hours",
]
ALL_TOPICS: list[str] = DEFLECTABLE_TOPICS + ["Other"]

# --------------------------------------------------------------------------------------------------
# Support operation model.
# --------------------------------------------------------------------------------------------------
AGENTS: list[str] = [f"agent{i:02d}" for i in range(1, 13)]
AGENT_COUNT = len(AGENTS)
WORKING_DAYS_PER_MONTH = 21
LOADED_AGENT_COST_PER_HOUR = 38.0

#: Determinism.
SEED = 42

#: The single simulated month (fixed so results are reproducible regardless of run date).
MONTH_START_ISO = "2026-02-01T00:00:00"
MONTH_DAYS = 30

# --------------------------------------------------------------------------------------------------
# Scenario service models (documented in results/metrics.md and the README "Limitations").
# Minutes unless stated otherwise.
# --------------------------------------------------------------------------------------------------
BASELINE_FRT_MEDIAN_MIN = 300.0
BASELINE_FRT_SIGMA = 1.15
BASELINE_HANDLE_MIN = 11.0
BASELINE_MANUAL_WARRANTY_MIN = 3.5   # P5: manual store-admin lookup
BASELINE_REWORK_MIN = 3.5            # P1: duplicate work across inbox + spreadsheet
BASELINE_FOLLOWUP_PROB = 0.65
BASELINE_FOLLOWUP_MEAN_MIN = 2200.0

SALESFORCE_HANDLE_MIN = 11.0
SALESFORCE_FOLLOWUP_PROB = 0.25
SALESFORCE_FOLLOWUP_MEAN_MIN = 900.0
ASSISTANT_RESPONSE_MIN_RANGE = (0.2, 1.5)

#: First-response distribution per priority band in the routed (Salesforce) scenario.
#: Each value is ("uniform" | "lognormal", a, b) where lognormal uses (median, sigma).
BAND_FRT_MODEL: dict[str, tuple] = {
    "Critical": ("uniform", 2.0, 12.0),
    "High": ("lognormal", 22.0, 0.55),
    "Medium": ("lognormal", 65.0, 0.65),
    "Low": ("lognormal", 180.0, 0.70),
    "Minimal": ("lognormal", 450.0, 0.70),
}
