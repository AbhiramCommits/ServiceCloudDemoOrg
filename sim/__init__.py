"""ServiceCloudDemoOrg local simulation harness.

This package mirrors, in Python, the business rules implemented in the deployable Salesforce
metadata under ``force-app/`` so that every before/after number in the README can be produced by
actually running code in this build, with no live org required.

Modules
-------
config            Shared constants: priority scoring weights, SLA matrix, agent model.
priority_router   Python port of ``PriorityRouter.cls`` (scoring, SLA, load-balanced assignment).
warranty          Python port of ``WarrantyService.isUnderWarranty``.
metrics           The five success metrics plus load-balance diagnostics.
assistant         Intent-routing case-deflection assistant (Agentforce-style).
run_simulation    CLI that runs BASELINE vs SALESFORCE over the same request set.
eval_assistant    CLI that scores the assistant against a labelled utterance set.
"""
