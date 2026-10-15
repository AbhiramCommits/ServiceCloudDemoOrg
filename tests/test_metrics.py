"""Tests for the metric functions on tiny, hand-computed fixtures."""

from __future__ import annotations

import pytest

from sim import metrics


def test_first_response_minutes_mean_and_p90():
    result = metrics.first_response_minutes([10, 20, 30])
    assert result["mean"] == pytest.approx(20.0)
    assert result["p90"] == pytest.approx(28.0)  # numpy linear interpolation
    assert result["n"] == 3


def test_first_response_minutes_empty_is_zero():
    assert metrics.first_response_minutes([]) == {"mean": 0.0, "p90": 0.0, "n": 0}


def test_sla_compliance_pct_hand_computed():
    assert metrics.sla_compliance_pct([True, True, False, True]) == pytest.approx(75.0)
    assert metrics.sla_compliance_pct([]) == 0.0


def test_deflection_rate_pct_hand_computed():
    assert metrics.deflection_rate_pct([True, False]) == pytest.approx(50.0)
    assert metrics.deflection_rate_pct([True, True]) == pytest.approx(100.0)
    assert metrics.deflection_rate_pct([]) == 0.0


def test_cases_per_agent_per_day_hand_computed():
    assert metrics.cases_per_agent_per_day(100, 10, 5) == pytest.approx(2.0)
    assert metrics.cases_per_agent_per_day(4000, 12, 21) == pytest.approx(15.87, abs=0.01)
    assert metrics.cases_per_agent_per_day(10, 0, 5) == 0.0


def test_backlog_age_hours_hand_computed():
    assert metrics.backlog_age_hours([60, 120]) == pytest.approx(1.5)
    assert metrics.backlog_age_hours([]) == 0.0


def test_agent_load_gini_bounds():
    assert metrics.agent_load_gini([3, 3, 3]) == pytest.approx(0.0)
    # Perfectly concentrated: gini = 2 - 4/3 = 0.6667
    assert metrics.agent_load_gini([0, 0, 10]) == pytest.approx(0.666667, abs=1e-5)
    assert metrics.agent_load_gini([]) == 0.0
    assert metrics.agent_load_gini([0, 0, 0]) == 0.0
