"""Tests for the packaged agent skill (skills/helix-gene-editing).

The skill is what gets listed on skill marketplaces, so these guard the things that
silently rot: the frontmatter contract, the tool names it teaches, and the example
specs it ships (they must still compile against the current compiler).
"""

import importlib.util
import json
import re
import zipfile
from pathlib import Path

import pytest

from helix.mcp.server import TOOLS, build_response

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "helix-gene-editing"
SKILL_MD = SKILL_DIR / "SKILL.md"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_skill_zip", ROOT / "skills" / "build_skill_zip.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


builder = _load_builder()


def _compile(source, full=False):
    r = build_response({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": "helix_compile", "arguments": {"source": source, "full": full}}})
    return r["result"]


# ---- frontmatter / structure ----

def test_skill_passes_its_own_validation():
    assert builder.validate(SKILL_DIR) == []


def test_frontmatter_contract():
    meta = builder.read_frontmatter(SKILL_MD)
    assert meta["name"] == "helix-gene-editing" == SKILL_DIR.name
    assert 0 < len(meta["description"]) <= 1024
    assert meta["license"] == "Apache-2.0"


def test_description_states_when_to_use_it():
    # Marketplaces and agents match on the description, so it must name the triggers.
    desc = builder.read_frontmatter(SKILL_MD)["description"].lower()
    for phrase in ("use when", "guide", "knockout", "base edit", "prime edit", "mcp"):
        assert phrase in desc, phrase


def test_skill_version_tracks_the_package_version():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    pkg_version = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M).group(1)
    assert str(builder.read_frontmatter(SKILL_MD)["metadata"]["version"]) == pkg_version


def test_skill_teaches_exactly_the_servers_tools():
    body = SKILL_MD.read_text(encoding="utf-8")
    mentioned = set(re.findall(r"`(helix_[a-z_]+)`", body))
    assert mentioned == {t["name"] for t in TOOLS}


def test_no_dangerous_shell_patterns_in_shipped_files():
    # Marketplace scanners flag these; the skill has no reason to contain any.
    bad = [r"\bsudo\b", r"rm\s+-rf", r"curl[^\n|]*\|\s*(ba)?sh", r"wget[^\n|]*\|\s*(ba)?sh", r"\beval\b", r"chmod\s+777"]
    for path in builder.skill_files(SKILL_DIR):
        text = path.read_text(encoding="utf-8")
        for pattern in bad:
            assert not re.search(pattern, text), f"{path.name} matches {pattern}"


# ---- the examples it ships ----

EXAMPLES = sorted((SKILL_DIR / "examples").glob("*.hx"))


def test_every_modality_family_has_an_example():
    modalities = set()
    for path in EXAMPLES:
        d = json.loads(_compile(path.read_text(encoding="utf-8"))["content"][0]["text"])
        modalities.add(d["modality"])
    assert modalities == {"crispr_ko", "base_edit", "prime_edit", "hdr", "deletion", "crispri"}


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_example_compiles_offline_and_is_feasible(path):
    result = _compile(path.read_text(encoding="utf-8"))
    assert not result.get("isError"), result["content"][0]["text"]
    d = json.loads(result["content"][0]["text"])
    assert d["safety"]["allowed"] is True
    assert d["feasible"] is True
    assert d["top_guides"]
    assert d["target"]["source"].startswith("inline")  # resolved offline, no network needed


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_example_matches_the_canonical_copy(path):
    # The skill carries copies so the zip is self-contained; they must not drift.
    assert path.read_bytes() == (ROOT / "examples" / path.name).read_bytes()


def test_hdr_guidance_matches_the_full_output_shape():
    # SKILL.md tells agents to read these keys from the full HDR design.
    src = (SKILL_DIR / "examples" / "hdr_silent_pamblock.hx").read_text(encoding="utf-8")
    d = json.loads(_compile(src, full=True)["content"][0]["text"])
    hdr = d["guides"][0]["hdr"]
    for key in ("pam_disrupted", "recut_note", "silent_pam_block", "sequence"):
        assert key in hdr
    assert {g["hdr"]["silent_pam_block"] for g in d["guides"]} >= {True, False}  # the three-valued case is real


def test_documented_error_messages_are_still_what_the_compiler_says():
    ko = (SKILL_DIR / "examples" / "tp53_ko.hx").read_text(encoding="utf-8")
    cases = {
        ko.replace("modality: crispr_ko", "modality crispr_ko"): "expected ':' or '{' after key",
        ko.replace("crispr_ko", "crispr_zz"): "is not valid",
        ko.replace("HEK293T", "zygote"): None,  # blocked, not an error
    }
    for src, expected in cases.items():
        r = _compile(src)
        if expected:
            assert r["isError"] and expected in r["content"][0]["text"]
        else:
            d = json.loads(r["content"][0]["text"])
            assert d["safety"]["allowed"] is False and d["top_guides"] == []
            assert d["infeasibility_notes"] == ["Run blocked by biosecurity screen."]


# ---- packaging ----

def test_zip_is_deterministic_and_self_contained(tmp_path):
    a = builder.build(SKILL_DIR, tmp_path / "a")
    b = builder.build(SKILL_DIR, tmp_path / "b")
    assert a.read_bytes() == b.read_bytes()
    with zipfile.ZipFile(a) as zf:
        names = zf.namelist()
        assert "helix-gene-editing/SKILL.md" in names
        assert any(n.startswith("helix-gene-editing/references/") for n in names)
        assert any(n.endswith(".hx") for n in names)
        assert zf.testzip() is None


def test_flat_zip_puts_skill_md_at_the_root(tmp_path):
    with zipfile.ZipFile(builder.build(SKILL_DIR, tmp_path, flat=True)) as zf:
        assert "SKILL.md" in zf.namelist()


def test_validation_catches_a_broken_skill(tmp_path):
    bad = tmp_path / "bad-skill"
    bad.mkdir()
    (bad / "SKILL.md").write_text("---\nname: Wrong Name\n---\nSee `references/missing.md`.\n", encoding="utf-8")
    problems = builder.validate(bad)
    assert any("name" in p for p in problems)
    assert any("description is required" in p for p in problems)
    assert any("missing.md" in p for p in problems)
    with pytest.raises(ValueError):
        builder.build(bad, tmp_path / "out")
