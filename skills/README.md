# Helix agent skills

An **agent skill** is the companion to the MCP server. The server gives an agent the
*capability* (`helix_compile` and friends); the skill tells it *when to reach for it and
how to use it well* — which modality fits the request, how to write a valid spec, how to
read the verdicts, and what never to claim about a heuristic score.

| | |
|---|---|
| `helix-gene-editing/` | The free skill (Apache-2.0): `SKILL.md`, three reference docs, eight runnable example specs. |
| `build_skill_zip.py` | Validates any skill directory and packages it as a deterministic zip. |

A second, commercial skill (`helix-validated-backends`) covers switching a design onto
the validated models — Cas-OFFinder + a reference genome, inDelphi, `rule_set_1` — and
verifying through `provenance.adapters` that the real model actually ran. It is
**deliberately not in this repository**: this repo is public and Apache-2.0, so
committing it here would license it away. It lives untracked (see `.gitignore`) or in a
private repo, and ships as a zip built by the same script. `tests/test_skill_validated.py`
skips when it is absent; the adapter findings it relies on are pinned for everyone by
`tests/test_adapter_api_contract.py`.

## Install it

**Claude Code** — the skill directory is the unit of installation:

```bash
pip install helix-dsl
claude mcp add helix -- helix mcp              # the capability
mkdir -p ~/.claude/skills && cp -r skills/helix-gene-editing ~/.claude/skills/
```

Project-local instead of user-wide: copy it to `.claude/skills/` in the repo. Other
clients (Cursor, Copilot, and the agent-skill marketplaces) take the zip below; the
`SKILL.md` frontmatter is the portable part.

The skill needs the MCP server registered — without it there is nothing to drive, and
`SKILL.md` tells the agent to say so rather than hand-writing guides.

## Package it

```bash
python skills/build_skill_zip.py            # -> dist/helix-gene-editing-0.1.1.zip
python skills/build_skill_zip.py --check    # validate only
python skills/build_skill_zip.py --flat     # SKILL.md at the zip root
```

The archive is byte-for-byte reproducible (sorted entries, fixed timestamps), so the same
skill always yields the same zip. `--check` enforces what skill registries look for:
kebab-case `name` matching the directory, a non-empty trigger-style `description` within
1024 characters, every `references/` and `examples/` path in `SKILL.md` actually
existing, and at least one supporting file. Some registries want `SKILL.md` at the zip
root rather than inside a folder — that is `--flat`.

## Keep it honest

`tests/test_skill.py` runs in the normal suite and fails if the skill drifts:

- the frontmatter contract holds and the version tracks `pyproject.toml`;
- the tools `SKILL.md` teaches are exactly the tools the server advertises;
- all eight example specs still compile offline, pass safety, and come back feasible;
- the examples are byte-identical to the canonical `examples/` copies;
- the error messages and HDR output shape quoted in the docs are what the compiler
  actually produces;
- no shell patterns that marketplace scanners flag.

So a change to the compiler, the tool names or the examples breaks the suite rather than
shipping a skill that quietly lies about them. When you bump the package version, bump
`metadata.version` in `SKILL.md` too.
