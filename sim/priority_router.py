"""Python port of ``PriorityRouter.cls``.

The scoring, SLA mapping and load-balanced assignment here are intentionally identical to the Apex
implementation so the harness and a deployed org produce the same triage decisions. Constants live
in :mod:`sim.config`.
"""

from __future__ import annotations

from . import config


def ltv_points(lifetime_value) -> int:
    """Points contributed by lifetime value. Monotonically non-decreasing in the input."""
    ltv = 0 if lifetime_value is None else float(lifetime_value)
    for threshold, points in config.LTV_TIERS:
        if ltv >= threshold:
            return points
    return 0


def channel_points(channel) -> int:
    """Points contributed by intake channel. Unknown channels score 0."""
    return config.CHANNEL_POINTS.get(channel, 0)


def topic_points(topic) -> int:
    """Points contributed by topic. Unknown topics score 0."""
    return config.TOPIC_POINTS.get(topic, 0)


def score_request(lifetime_value, channel, topic) -> int:
    """Composite priority score, 0..85. Higher means more urgent."""
    return ltv_points(lifetime_value) + channel_points(channel) + topic_points(topic)


def sla_minutes_for_score(score) -> int:
    """Minutes of first-response SLA allowed for a given score."""
    s = 0 if score is None else int(score)
    for threshold, minutes, _band in config.SLA_MATRIX:
        if s >= threshold:
            return minutes
    return config.SLA_MATRIX[-1][1]


def priority_band_for_score(score) -> str:
    """Priority band label for a given score (Critical/High/Medium/Low/Minimal)."""
    s = 0 if score is None else int(score)
    for threshold, _minutes, band in config.SLA_MATRIX:
        if s >= threshold:
            return band
    return config.SLA_MATRIX[-1][2]


def assign_owners(request_ids, agents=None) -> dict:
    """Greedy least-loaded owner assignment with a deterministic tie-break.

    Mirrors ``PriorityRouter.assignOwner``: the agent pool is sorted, then each request in input
    order goes to the currently least-loaded agent, ties broken by earliest position in the sorted
    pool. Returns a mapping of request id -> agent name.
    """
    pool = sorted(agents if agents is not None else config.AGENTS)
    load = {agent: 0 for agent in pool}
    assignment: dict = {}
    if not pool:
        return assignment

    for request_id in request_ids:
        chosen = pool[0]
        lowest = load[chosen]
        for agent in pool:
            if load[agent] < lowest:
                chosen = agent
                lowest = load[agent]
        assignment[request_id] = chosen
        load[chosen] = lowest + 1
    return assignment
