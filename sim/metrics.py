"""The five success metrics from the discovery brief, plus load-balance diagnostics.

Every function takes plain sequences (or a scalar for capacity math) so it can be unit-tested on
tiny hand-computed fixtures. Definitions mirror ``SupportMetricsService.cls``.
"""

from __future__ import annotations

from typing import Iterable, Sequence

try:  # numpy ships with pandas, but keep a pure-python fallback so tests never hard-fail on import.
    import numpy as np
except Exception:  # pragma: no cover
    np = None


def _as_floats(values: Iterable[float]) -> list[float]:
    return [float(v) for v in values]


def first_response_minutes(values: Sequence[float]) -> dict:
    """M1 - mean and p90 first-response time in minutes."""
    data = _as_floats(values)
    if not data:
        return {"mean": 0.0, "p90": 0.0, "n": 0}
    ordered = sorted(data)
    mean = sum(ordered) / len(ordered)
    if np is not None:
        p90 = float(np.percentile(ordered, 90))
    else:  # pragma: no cover
        index = min(len(ordered) - 1, int(len(ordered) * 0.9))
        p90 = ordered[index]
    return {"mean": round(mean, 2), "p90": round(p90, 2), "n": len(ordered)}


def sla_compliance_pct(met_flags: Iterable[bool]) -> float:
    """M3 - percentage of responded requests whose first response beat the SLA target."""
    flags = [bool(f) for f in met_flags]
    if not flags:
        return 0.0
    return round(100.0 * sum(flags) / len(flags), 2)


def deflection_rate_pct(deflected_flags: Iterable[bool]) -> float:
    """M2 - percentage of requests resolved without a human touch."""
    flags = [bool(f) for f in deflected_flags]
    if not flags:
        return 0.0
    return round(100.0 * sum(flags) / len(flags), 2)


def cases_per_agent_per_day(total_cases: int, agent_count: int, working_days: int) -> float:
    """M4 - human-handled cases per agent per working day."""
    if agent_count <= 0 or working_days <= 0:
        return 0.0
    return round(total_cases / (agent_count * working_days), 2)


def backlog_age_hours(age_minutes: Iterable[float]) -> float:
    """M5 - mean age in hours of work sitting open (request age at resolution / snapshot)."""
    data = _as_floats(age_minutes)
    if not data:
        return 0.0
    return round(sum(data) / len(data) / 60.0, 2)


def agent_load_gini(counts: Iterable[float]) -> float:
    """Gini coefficient of per-agent case counts. 0 = perfectly even, 1 = maximally skewed."""
    data = sorted(_as_floats(counts))
    n = len(data)
    total = sum(data)
    if n == 0 or total == 0:
        return 0.0
    if np is not None:
        index = np.arange(1, n + 1)
        gini = (2.0 * float(np.sum(index * np.asarray(data)))) / (n * total) - (n + 1.0) / n
    else:  # pragma: no cover
        cumulative = 0.0
        weighted = 0.0
        for i, value in enumerate(data, start=1):
            weighted += i * value
            cumulative += value
        gini = (2.0 * weighted) / (n * cumulative) - (n + 1.0) / n
    return round(max(0.0, gini), 6)
