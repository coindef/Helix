"""Package the Helix agent skill as a zip for skill marketplaces such as Agensi.

    python skills/build_skill_zip.py              # -> dist/helix-gene-editing-<version>.zip
    python skills/build_skill_zip.py --flat       # SKILL.md at the zip root, not in a folder
    python skills/build_skill_zip.py --check      # validate only, write nothing

The archive is deterministic (sorted entries, fixed timestamps), so the same skill
always produces the same bytes. Needs only the standard library and PyYAML, which Helix
already depends on.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from typing import List, Tuple

import yaml

SKILLS_DIR = Path(__file__).resolve().parent
DEFAULT_SKILL = SKILLS_DIR / "helix-gene-editing"
_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_MAX_NAME, _MAX_DESCRIPTION = 64, 1024
_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
_LOCAL_LINK_RE = re.compile(r"`((?:references|examples|scripts)/[\w./-]+)`")


def read_frontmatter(skill_md: Path) -> dict:
    """Return the YAML frontmatter of a SKILL.md as a dict (raises ValueError if absent)."""
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError(f"{skill_md}: missing YAML frontmatter")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError(f"{skill_md}: frontmatter is not a mapping")
    return data


def skill_files(skill_dir: Path) -> List[Path]:
    """Every file that ships in the skill, sorted for a stable archive."""
    return sorted(p for p in skill_dir.rglob("*") if p.is_file() and "__pycache__" not in p.parts)


def validate(skill_dir: Path) -> List[str]:
    """Return a list of problems; empty means the skill is ready to package."""
    problems: List[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{skill_dir}: SKILL.md not found"]
    try:
        meta = read_frontmatter(skill_md)
    except ValueError as exc:
        return [str(exc)]

    name, description = meta.get("name"), meta.get("description")
    if not isinstance(name, str) or not _NAME_RE.match(name) or len(name) > _MAX_NAME:
        problems.append(f"name {name!r} must be lowercase letters/digits/hyphens, <= {_MAX_NAME} chars")
    elif name != skill_dir.name:
        problems.append(f"name {name!r} must match the directory name {skill_dir.name!r}")
    if not isinstance(description, str) or not description.strip():
        problems.append("description is required")
    elif len(description) > _MAX_DESCRIPTION:
        problems.append(f"description is {len(description)} chars; the limit is {_MAX_DESCRIPTION}")

    body = skill_md.read_text(encoding="utf-8")
    for rel in sorted(set(_LOCAL_LINK_RE.findall(body))):
        if "*" in rel:  # a glob like examples/*.hx is a directory reference
            continue
        if not (skill_dir / rel).is_file():
            problems.append(f"SKILL.md references {rel}, which does not exist")
    if not any(p for p in skill_files(skill_dir) if p.name != "SKILL.md"):
        problems.append("no supporting files; add references/ or examples/")
    return problems


def archive_name(skill_dir: Path, flat: bool = False) -> Tuple[str, str]:
    """(zip file name, root prefix inside the archive) for this skill."""
    meta = read_frontmatter(skill_dir / "SKILL.md")
    version = str((meta.get("metadata") or {}).get("version", "0"))
    return f"{skill_dir.name}-{version}.zip", ("" if flat else skill_dir.name + "/")


def build(skill_dir: Path, out_dir: Path, flat: bool = False) -> Path:
    """Write the deterministic zip and return its path. Validates first."""
    problems = validate(skill_dir)
    if problems:
        raise ValueError("skill failed validation:\n  - " + "\n  - ".join(problems))
    zip_name, prefix = archive_name(skill_dir, flat)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / zip_name
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in skill_files(skill_dir):
            info = zipfile.ZipInfo(prefix + path.relative_to(skill_dir).as_posix(), _ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
    return target


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skill", nargs="?", type=Path, default=DEFAULT_SKILL, help="skill directory")
    parser.add_argument("-o", "--out", type=Path, default=SKILLS_DIR.parent / "dist", help="output directory")
    parser.add_argument("--flat", action="store_true", help="put SKILL.md at the zip root")
    parser.add_argument("--check", action="store_true", help="validate only")
    args = parser.parse_args(argv)

    problems = validate(args.skill)
    if problems:
        print("Skill is not ready:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    if args.check:
        print(f"{args.skill.name}: OK ({len(skill_files(args.skill))} files)")
        return 0
    target = build(args.skill, args.out, flat=args.flat)
    print(f"Wrote {target} ({target.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
