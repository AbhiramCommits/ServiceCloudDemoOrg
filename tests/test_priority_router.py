"""Tests for the priority router (Python port of PriorityRouter.cls)."""

from __future__ import annotations

import pytest

from sim import config, priority_router as pr


def test_score_is_monotonic_in_lifetime_value():
    scores = [
        pr.score_request(ltv, "Email", "Store Hours")
        for ltv in (0, 50, 150, 600, 1200, 2500, 9000)
    ]
    assert scores == sorted(scores), "Score must never fall as lifetime value rises"
    assert scores[0] < scores[-1], "Extreme LTV values must produce different scores"


def test_score_bounds_match_configuration():
    assert pr.score_request(0, "Email", "Store Hours") == config.MIN_SCORE
    assert pr.score_request(99999, "Phone", "Warranty") == config.MAX_SCORE
    assert pr.score_request(None, None, None) == 0


def test_high_value_urgent_beats_low_value_trivial():
    whale = pr.score_request(4200, "Phone", "Warranty")
    casual = pr.score_request(60, "Email", "Store Hours")
    assert whale > casual
    assert pr.sla_minutes_for_score(whale) < pr.sla_minutes_for_score(casual)


@pytest.mark.parametrize(
    "score,sla_minutes,band",
    [
        (0, 1440, "Minimal"),
        (14, 1440, "Minimal"),
        (15, 480, "Low"),
        (29, 480, "Low"),
        (30, 180, "Medium"),
        (49, 180, "Medium"),
        (50, 60, "High"),
        (69, 60, "High"),
        (70, 15, "Critical"),
        (85, 15, "Critical"),
    ],
)
def test_sla_matrix_bounds(score, sla_minutes, band):
    assert pr.sla_minutes_for_score(score) == sla_minutes
    assert pr.priority_band_for_score(score) == band


def test_sla_is_never_relaxed_as_score_rises():
    minutes = [pr.sla_minutes_for_score(s) for s in range(0, 86)]
    assert minutes == sorted(minutes, reverse=True)


def test_owner_assignment_is_balanced_within_tolerance():
    requests = [f"REQ-{i:04d}" for i in range(37)]
    agents = [f"agent{i:02d}" for i in range(1, 13)]
    assignment = pr.assign_owners(requests, agents)

    assert set(assignment) == set(requests)
    counts = [list(assignment.values()).count(a) for a in agents]
    assert max(counts) - min(counts) <= 1, f"Load imbalance too high: {counts}"


def test_owner_assignment_is_deterministic_and_handles_empty_input():
    requests = ["a", "b", "c"]
    first = pr.assign_owners(requests, ["agent02", "agent01"])
    second = pr.assign_owners(requests, ["agent01", "agent02"])
    assert first == second, "Tie-break must not depend on input agent order"
    assert pr.assign_owners([], ["agent01"]) == {}
