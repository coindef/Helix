"""Tests for the validated-backends skill (skills/helix-validated-backends).

This skill is sold, so the cost of it being wrong is someone else's failed experiment.
These tests pin the two claims that matter: the backends it tells you to enable really
do work, and the ones it tells you to avoid really are broken.
"""

import importlib.util
import json
import re
import sys
import types
from pathlib import Path

import pytest

from helix.mcp.server import build_response

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "helix-validated-backends"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCES = SKILL_DIR / "references"

# This skill is a commercial product and is deliberately NOT committed to this
# Apache-2.0 repository — publishing it here would license it away. It lives untracked in
# a working tree (or in a private repo) and is shipped as a zip. These tests therefore
# only run where it is present. The adapter findings it depends on are pinned publicly by
# tests/test_adapter_api_contract.py, which always runs.
#
# This skip must happen at MODULE level and before the loads below: the helper modules are
# imported at import time, so a function-level skipif would still hit a FileNotFoundError
# during collection and fail the whole suite on a fresh clone.
if not SKILL_MD.is_file():  # pragma: no cover - exercised only on a clone without the skill
    pytest.skip(
        "helix-validated-backends is not present in this checkout (untracked by design)",
        allow_module_level=True,
    )


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


builder = _load(ROOT / "skills" / "build_skill_zip.py", "build_skill_zip")
checker = _load(SKILL_DIR / "scripts" / "check_backends.py", "check_backends")


def _compile(source, full=False):
    return build_response({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                           "params": {"name": "helix_compile",
                                      "arguments": {"source": source, "full": full}}})["result"]


# ---- structure ----

def test_skill_passes_validation():
    assert builder.validate(SKILL_DIR) == []


def test_frontmatter_and_version():
    meta = builder.read_frontmatter(SKILL_MD)
    assert meta["name"] == "helix-validated-backends" == SKILL_DIR.name
    assert 0 < len(meta["description"]) <= 1024
    pkg = re.search(r'^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M).group(1)
    assert str(meta["metadata"]["version"]) == pkg


def test_paid_skill_is_not_apache_licensed():
    # The free skill is Apache-2.0; this one is sold, so it must not claim the same grant.
    assert builder.read_frontmatter(SKILL_MD)["license"] != "Apache-2.0"


# ---- the readiness checker ----

def test_checker_reports_the_always_on_models_ready():
    rows = {r["key"]: r for r in checker.collect(check_network=False)}
    assert rows["rule_set_1"]["status"] == checker.READY, rows["rule_set_1"]["detail"]
    assert rows["cfd (core)"]["status"] == checker.READY, rows["cfd (core)"]["detail"]


def test_checker_marks_the_broken_adapters_unsupported():
    rows = {r["key"]: r for r in checker.collect(check_network=False)}
    assert rows["behive"]["status"] == checker.UNSUPPORTED
    assert rows["pridict"]["status"] == checker.UNSUPPORTED


def test_checker_exits_zero_offline():
    assert checker.main(["--no-network"]) == 0


def test_checker_json_is_machine_readable(capsys):
    checker.main(["--json", "--no-network"])
    payload = json.loads(capsys.readouterr().out)
    assert {r["key"] for r in payload["backends"]} >= {"rule_set_1", "cas_offinder_cfd", "behive"}


# ---- the claims the skill makes about real backends ----

def test_rule_set_1_really_runs_offline_and_is_recorded_in_provenance():
    src = (SKILL_DIR / "examples" / "validated_offline.hx").read_text()
    result = _compile(src)
    assert not result.get("isError"), result["content"][0]["text"]
    d = json.loads(result["content"][0]["text"])
    assert d["feasible"] is True and d["safety"]["allowed"] is True
    assert d["provenance"]["adapters"]["on_target"] == "rule_set_1@doench2014"


def test_rule_set_1_changes_the_ranking_not_just_the_numbers():
    # The skill claims switching is not cosmetic. If this ever stops being true, the
    # skill's central selling point is wrong.
    base = (ROOT / "examples" / "tp53_ko.hx").read_text()
    heur = json.loads(_compile(base)["content"][0]["text"])
    real = json.loads(_compile(base.replace("on_target: heuristic_gc",
                                            "on_target: rule_set_1"))["content"][0]["text"])
    assert real["provenance"]["adapters"]["on_target"] == "rule_set_1@doench2014"
    assert [g["spacer"] for g in real["top_guides"]] != [g["spacer"] for g in heur["top_guides"]]


def test_cfd_core_is_exact_for_a_perfect_match():
    from helix.adapters.offtarget import cfd_score
    assert cfd_score("GTCGATCGATCGATCGATCG", "GTCGATCGATCGATCGATCGAGG") == pytest.approx(1.0)


def test_real_off_target_fails_loudly_without_a_genome(monkeypatch):
    # The skill promises Helix never silently downgrades to a heuristic.
    monkeypatch.delenv("HELIX_GENOME_DIR", raising=False)
    src = (ROOT / "examples" / "tp53_ko.hx").read_text().replace(
        "off_target: mock_seed", "off_target: cas_offinder_cfd")
    result = _compile(src)
    assert result.get("isError")
    assert "needs a genome" in result["content"][0]["text"]


def test_indelphi_adapter_matches_the_real_upstream_api(monkeypatch):
    """inDelphi is the one ML backend the skill says to install. Prove the adapter
    speaks the real package's API: init_model(celltype=) + predict(seq, cut) -> (df, stats)."""
    pd = pytest.importorskip("pandas")
    from helix.adapters.repair import InDelphiBackend

    mod = types.ModuleType("inDelphi")
    mod.init_model = lambda celltype=None: None
    mod.predict = lambda seq, cut: (
        pd.DataFrame({"Category": ["del", "ins"], "Length": [3, 1],
                      "Predicted frequency": [40.0, 20.0]}),
        {"Frameshift frequency": 66.7},
    )
    monkeypatch.setitem(sys.modules, "inDelphi", mod)
    pred = InDelphiBackend(celltype="HEK293").predict("ACGT" * 20, 40)
    assert pred.frameshift_fraction == pytest.approx(0.667, abs=1e-3)
    assert pred.genotypes[0].label == "3bp_deletion"


# ---- the claims the skill makes about the BROKEN backends ----

def test_behive_is_still_broken_against_the_real_upstream_api(monkeypatch):
    """If this test starts FAILING, someone fixed the adapter: update the skill to stop
    telling buyers to avoid BE-Hive."""
    pd = pytest.importorskip("pandas")
    from helix.adapters.base_edit_model import BEHiveBackend

    real = types.ModuleType("be_predict_efficiency")
    real.init_model = lambda base_editor=None, celltype=None: None
    real.predict = lambda seq: (pd.DataFrame({"Predicted logit score": [0.3]}),
                                {"Predicted efficiency": 0.42})
    monkeypatch.setitem(sys.modules, "be_predict_efficiency", real)
    with pytest.raises((TypeError, AttributeError)):
        BEHiveBackend().predict("ACGTACGTACGTACGTACGT", "CBE", [5])


def test_pridict_is_still_broken_against_the_real_upstream_api(monkeypatch):
    from helix.adapters.prime_edit_model import PridictBackend

    real = types.ModuleType("pridict")  # upstream ships a CLI, not an importable predict()
    monkeypatch.setitem(sys.modules, "pridict", real)
    with pytest.raises((TypeError, AttributeError)):
        PridictBackend().predict("ACGT", "pbs", "rtt", "A>G @ 1")


def test_skill_tells_the_agent_not_to_select_the_broken_backends():
    body = SKILL_MD.read_text()
    install = (REFERENCES / "model-install.md").read_text()
    assert "Do not use" in body
    for text in (body, install):
        assert "window_heuristic" in text and "pe_heuristic" in text
    # and it must not promise they are installable
    assert "pip install BE-Hive" not in body + install


def test_skill_never_tells_the_agent_to_trust_the_spec_over_provenance():
    body = SKILL_MD.read_text() + (REFERENCES / "verification.md").read_text()
    assert "provenance.adapters" in body
    assert "mock_seed@0.1.0" in body  # the exact string an agent must recognise


# ---- packaging ----

def test_both_skills_package_independently(tmp_path):
    free = builder.build(ROOT / "skills" / "helix-gene-editing", tmp_path)
    paid = builder.build(SKILL_DIR, tmp_path)
    assert free.name != paid.name
    assert builder.build(SKILL_DIR, tmp_path / "again").read_bytes() == paid.read_bytes()


def test_packaged_zip_contains_the_runnable_checker(tmp_path):
    import zipfile
    with zipfile.ZipFile(builder.build(SKILL_DIR, tmp_path)) as zf:
        assert "helix-validated-backends/scripts/check_backends.py" in zf.namelist()
