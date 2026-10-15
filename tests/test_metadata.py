"""Static checks on the deployable metadata: well-formedness, Apex hygiene and traceability."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from sim import config

ROOT = Path(__file__).resolve().parents[1]
FORCE_APP = ROOT / "force-app"
DOCS = ROOT / "docs"
PAIN_IDS = ["P1", "P2", "P3", "P4", "P5"]


def test_every_meta_xml_parses_as_xml():
    files = sorted(FORCE_APP.rglob("*-meta.xml"))
    assert len(files) >= 40, f"expected a rich metadata tree, found {len(files)} files"
    for path in files:
        ET.parse(path)  # raises ParseError on malformed XML


def test_every_apex_class_has_a_matching_meta_file():
    classes = sorted(FORCE_APP.rglob("*.cls"))
    assert classes, "no Apex classes found"
    for path in classes:
        meta = Path(str(path) + "-meta.xml")
        assert meta.exists(), f"missing meta for {path.name}"


def _soql_inside_for_loops(path: Path) -> list[tuple[int, str]]:
    """Brace-depth scan that flags a SOQL statement located inside a for-loop body."""
    depth = 0
    open_loops: list[int] = []
    offenders: list[tuple[int, str]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if re.search(r"\bfor\s*\(", line):
            open_loops.append(depth + 1)
        if re.search(r"\[\s*SELECT\b", line, re.IGNORECASE) and open_loops:
            offenders.append((lineno, line.strip()))
        depth += line.count("{") - line.count("}")
        open_loops = [body_depth for body_depth in open_loops if body_depth <= depth]
    return offenders


def test_no_soql_query_inside_a_for_loop():
    offenders = []
    for path in list(FORCE_APP.rglob("*.cls")) + list(FORCE_APP.rglob("*.trigger")):
        offenders.extend((str(path.relative_to(ROOT)), line, text) for line, text in _soql_inside_for_loops(path))
    assert not offenders, f"SOQL inside a loop: {offenders}"


def _traceability_rows() -> list[list[str]]:
    text = (DOCS / "requirements-traceability.md").read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) >= 5 and cols[0] in PAIN_IDS:
            rows.append(cols)
    return rows


def test_traceability_covers_every_pain_with_a_real_repo_path():
    rows = {row[0]: row for row in _traceability_rows()}
    for pain in PAIN_IDS:
        assert pain in rows, f"{pain} is missing from docs/requirements-traceability.md"
        where = rows[pain][3]
        assert "TODO" not in where, f"{pain} has no concrete repo path yet"
        assert "force-app/" in where or "sim/" in where, f"{pain} path does not point at this repo"


def test_discovery_brief_names_all_five_pains():
    text = (DOCS / "discovery-brief.md").read_text(encoding="utf-8")
    for pain in PAIN_IDS:
        assert f"**{pain}**" in text, f"{pain} missing from the discovery brief"


def test_traceability_has_no_remaining_todos():
    text = (DOCS / "requirements-traceability.md").read_text(encoding="utf-8")
    assert "TODO" not in text, "requirements-traceability.md still contains TODO placeholders"


def test_documented_numbers_trace_to_simulation_output():
    payload = json.loads((ROOT / "results" / "metrics.json").read_text(encoding="utf-8"))
    documented = "\n".join(
        (DOCS / name).read_text(encoding="utf-8")
        for name in ("requirements-traceability.md", "value-model.md", "slide-outline.md")
    ) + (ROOT / "README.md").read_text(encoding="utf-8")
    for key, entry in payload["metrics"].items():
        for side in ("baseline", "salesforce"):
            rendered = f"{entry[side]:,.2f}"
            assert rendered in documented, f"{key}.{side} = {rendered} is not traceable to docs/"


def test_apex_and_python_sla_matrix_agree():
    cls = (FORCE_APP / "main/default/classes/PriorityRouter.cls").read_text(encoding="utf-8")
    minutes_block = re.search(r"SLA_MINUTES\s*=\s*new List<Integer>\{([^}]*)\}", cls)
    thresholds_block = re.search(r"SLA_SCORE_THRESHOLDS\s*=\s*new List<Integer>\{([^}]*)\}", cls)
    assert minutes_block and thresholds_block, "could not find the SLA matrix in PriorityRouter.cls"

    apex_minutes = [int(x) for x in re.findall(r"\d+", minutes_block.group(1))]
    apex_thresholds = [int(x) for x in re.findall(r"\d+", thresholds_block.group(1))]

    assert apex_minutes == [minutes for _t, minutes, _band in config.SLA_MATRIX]
    assert apex_thresholds == [threshold for threshold, _m, _band in config.SLA_MATRIX]

    flow = (FORCE_APP / "main/default/flows/Support_Request_Triage.flow-meta.xml").read_text(encoding="utf-8")
    for minutes in apex_minutes:
        assert str(minutes) in flow, f"SLA minutes {minutes} missing from the triage flow"
