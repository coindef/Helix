"""Author-facing spec parsing + error formatting, shared by the HTTP API and MCP.

Both surfaces need to turn a raw ``.hx``/YAML string into an ``ExperimentSpec`` and,
on failure, a clean message (never a raw pydantic dump). Centralised here so the two
front doors behave identically.
"""

from __future__ import annotations

from typing import Optional

import yaml
from pydantic import ValidationError

from helix.frontend.helix_lang import HelixSyntaxError, parse_helix
from helix.frontend.loader import parse_spec
from helix.ir.spec import ExperimentSpec


class SpecError(ValueError):
    """A spec that could not be parsed/validated, with an author-facing message."""

    def __init__(self, message: str, kind: str = "spec", line: Optional[int] = None, col: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.kind = kind  # "syntax" (has line/col) | "spec" (validation/value)
        self.line = line
        self.col = col


def friendly_validation(exc: ValidationError) -> str:
    """Turn a pydantic ValidationError into plain, author-facing lines.

    The raw ``str(ValidationError)`` leaks internals ("1 validation error for
    ExperimentSpec … visit errors.pydantic.dev") — not something to show a user.
    """
    lines = []
    for e in exc.errors():
        loc = ".".join(str(p) for p in e.get("loc", ())) or "spec"
        etype = e.get("type", "")
        got = e.get("input")
        if etype == "enum":
            allowed = (e.get("ctx") or {}).get("expected", "one of the allowed values")
            lines.append(f"{loc}: {got!r} is not valid — expected {allowed}.")
        elif etype == "missing":
            lines.append(f"{loc}: this field is required.")
        elif etype == "extra_forbidden":
            lines.append(f"{loc}: unknown field.")
        else:
            msg = e.get("msg", "invalid value")
            suffix = f" (got {got!r})" if got not in (None, "") else ""
            lines.append(f"{loc}: {msg}{suffix}")
    return "\n".join(lines) if lines else str(exc)


def parse_source(source: str, fmt: str = "helix") -> ExperimentSpec:
    """Parse ``.hx`` (fmt='helix') or YAML (fmt='yaml') into a spec.

    Raises :class:`SpecError` with a clean message (and line/col for syntax errors).
    """
    try:
        if fmt not in {"helix", "yaml"}:
            raise ValueError(f"unsupported source format: {fmt!r}")
        return parse_spec(source) if fmt == "yaml" else parse_helix(source)
    except HelixSyntaxError as exc:
        raise SpecError(str(exc), kind="syntax", line=exc.line, col=exc.col) from exc
    except yaml.YAMLError as exc:
        # PyYAML's str() is a multi-line "<unicode string>" dump; extract the essentials.
        mark = getattr(exc, "problem_mark", None)
        problem = getattr(exc, "problem", None) or "could not parse YAML"
        line = (mark.line + 1) if mark else None
        col = (mark.column + 1) if mark else None
        raise SpecError(f"invalid YAML: {problem}", kind="syntax", line=line, col=col) from exc
    except ValidationError as exc:
        raise SpecError(friendly_validation(exc), kind="spec") from exc
    except ValueError as exc:
        raise SpecError(str(exc), kind="spec") from exc
