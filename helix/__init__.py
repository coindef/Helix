"""Helix — a declarative DSL and compiler for reproducible gene-editing design.

Helix separates *intent* (a declarative spec: what edit you want, under what
constraints) from *orchestration* (a deterministic compiler plus LLM agents that
resolve ambiguity). The compiler turns an ``ExperimentSpec`` into a fully
resolved, provenance-stamped ``ResolvedDesign``.

The public entry point is :func:`helix.compiler.pipeline.compile_spec`.
"""

__version__ = "0.1.1"
