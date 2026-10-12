<div align="center">

<img src="https://raw.githubusercontent.com/coindef/Helix/main/docs/logo.svg" width="78" height="78" alt="Helix logo" />

# Helix

**A declarative DSL &amp; compiler for reproducible gene-editing design.**

[![PyPI](https://img.shields.io/pypi/v/helix-dsl?color=5b53e0&label=pypi)](https://pypi.org/project/helix-dsl/)
[![License](https://img.shields.io/github/license/coindef/Helix?color=5b53e0)](https://github.com/coindef/Helix/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-5b53e0)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-261%20passing-0b7a5d)](https://github.com/coindef/Helix/tree/main/tests)
[![MCP](https://img.shields.io/badge/MCP-server-5b53e0)](#mcp-server)
[![Accessibility](https://img.shields.io/badge/a11y-WCAG_2.1_AA-0b7a5d)](#web-ui)

[Quickstart](#quickstart) · [Highlights](#highlights) · [The language](#the-language) · [Architecture](#architecture) · [MCP server](#mcp-server) · [Deep dive](https://github.com/coindef/Helix/blob/main/ARCHITECTURE.md)

</div>

Most agentic gene-editing tools are chat interfaces that produce a one-off answer.
**Helix treats an editing experiment as source code:** you write a small declarative
spec (the *intent*), and a deterministic **compiler** — assisted by narrowly-scoped
LLM agents — turns it into a fully resolved, provenance-stamped **design** you can
diff, version, review, and re-run. The bench scientist reading a protocol and the
computational biologist tuning constraints work from the same reviewable artifact.

<p align="center">
  <img src="https://raw.githubusercontent.com/coindef/Helix/main/docs/hero.png" width="900"
       alt="Helix web UI — a syntax-highlighted spec editor on the left; on the right the compiled design with ranked guides and protein-consequence badges (premature-STOP, missense, silent)." />
</p>

> **The key rule:** agents may only *emit or edit a spec*; only the deterministic
> compiler produces the design. That keeps the trust boundary auditable and every run
> reproducible — the same audit trail that protects a human protects an agent.

## Highlights

- **8 modalities** — knockout · base editing (CBE/ABE/CGBE) · prime editing · HDR knock-in · dual-cut deletion · CRISPRi / CRISPRa.
- **Constraints are first-class** — the compiler *solves* against them and reports infeasibility, instead of silently returning "the top N".
- **Protein-consequence aware** — every coding edit is called *silent · missense · premature-STOP (iSTOP) · stop-loss · frameshift*, with **guaranteed-synonymous** HDR PAM-blocks.
- **Variant-aware guides** — flags common population SNPs in the seed/PAM (a SNP there abolishes binding in carriers).
- **Injectable backends** — swap a heuristic for a real tool (Cas-OFFinder, inDelphi, BE-Hive, PRIDICT, Ensembl/NCBI, ESMFold) by editing the spec, *not* the code.
- **MCP server + LLM agents** — any agent can drive the compiler through the spec → compile boundary.
- **Web UI** — syntax-highlighting editor, interactive 3D helix, order-ready oligos, and results analysis; keyboard-navigable throughout.
- **Reproducible & auditable** — every design is provenance-stamped; diff and version it in git.

## Quickstart

```bash
pip install helix-dsl                                       # or: pip install -e '.[all]'

helix compile examples/tp53_ko.hx -o out                    # knockout (SpCas9)
helix compile examples/istop_base_edit.hx                   # base editing → iSTOP knockout
helix compile examples/tp53_prime_edit.hx                   # prime editing (pegRNA)
helix compile examples/tp53_knock_in.hx                     # HDR knock-in (cut + donor)
helix compile examples/tp53_ko_ensembl.hx                   # resolves TP53 from Ensembl (network)
helix validate examples/tp53_ko.hx                          # parse + safety screen only
```

`compile` prints a Markdown protocol and (with `-o`) writes `out/design.json` (the
reproducible record) and `out/protocol.md` (what a bench scientist reads). See all
eight modalities in [`examples/`](https://github.com/coindef/Helix/tree/main/examples).

## The language

A Helix spec can be written in the **Helix grammar** (`.hx`) or **YAML** — both compile
to the same validated `ExperimentSpec`.

```hx
helix "TP53_KO_HEK293" {
  organism: human(GRCh38)
  profile:  strict                                 # preset efficiency / off-target / GC / hairpin defaults
  target: gene(TP53) { goal: knockout; region: exon(2..4); frame: 0 }
  strategy { modality: crispr_ko; enzyme: auto }   # `auto` → the compiler picks (delivery-aware)
  constraints {
    on_target.min_efficiency: 0.5
    off_target.max_cfd: 0.2
    gc.min: 0.4                                     # spacer GC window
    guides.count: 3
    avoid: [ homopolymer(>=4), self_complementary(>=8), common_variant(>=0.01) ]
  }
  simulate { sequence_provider: ensembl; on_target: rule_set_1; variant_source: ensembl }
  deliver: rnp
  validate: amplicon_seq
}
```

- **Guide-quality constraints** — GC window, hairpin/self-complementarity, homopolymer, and restriction-site filters, each reported as a pass/fail check in the drill-down. `profile: strict | lenient | screen | quick` presets sensible defaults; anything you write overrides them.
- **`frame: 0`** unlocks the protein-consequence calls above and the guaranteed-synonymous HDR PAM-block.
- **`variant_source: ensembl`** + `avoid: [common_variant(>=0.01)]` reject guides with a common SNP in the seed/PAM.

Full grammar → [`GRAMMAR.md`](https://github.com/coindef/Helix/blob/main/helix/frontend/helix_lang/GRAMMAR.md).

## Architecture

<p align="center">
  <img src="https://raw.githubusercontent.com/coindef/Helix/main/docs/architecture.svg" width="820"
       alt="Helix architecture — three layers: Helix Studio (author &amp; review) feeds the deterministic compiler (compile pipeline, agents &amp; builders, design store), which draws on a Simulate &amp; score layer of injectable backends (sequence, on/off-target, edit outcome, variants, folding)." />
</p>

Three layers:

1. **Helix Studio** — author and review a spec via the **CLI**, **Web UI**, or **MCP** (agents). The spec is the reviewable artifact.
2. **Deterministic compiler** — a fixed pipeline (safety → strategy → target → guides → simulate → constraints → primers) plus narrowly-scoped LLM agents/builders and a provenance-stamped design store. *Agents only touch the spec; the compiler owns the design.*
3. **Simulate & score** — pluggable backends score each candidate. Heuristics run offline by default; a spec edit swaps in a real tool.

Everything routes through injectable adapter **Protocols**, so the whole spine is testable offline and a real tool drops in behind the same interface. Deep dive → [`ARCHITECTURE.md`](https://github.com/coindef/Helix/blob/main/ARCHITECTURE.md).

<a id="mcp-server"></a>
## MCP server — gene-editing design for agents

Agents are good at *writing a constrained spec* and bad at *safely orchestrating raw
bioinformatics tools* — exactly the split Helix is built around. So Helix ships as an
**MCP server**: any MCP-capable agent (Claude, etc.) drives the compiler, but **only
through the spec → compile boundary**.

```bash
helix mcp        # stdio JSON-RPC server, zero extra deps   (== python3 -m helix.mcp)
```

```jsonc
// register with an MCP client
{ "mcpServers": { "helix": { "command": "helix", "args": ["mcp"] } } }
```

Tools: **`helix_reference`** (grammar + guide + examples), **`helix_compile`** (spec →
ranked, safety-screened design summary), **`helix_resolve_gene`** (symbol → sequence +
locus), **`helix_list_models`** (selectable backends). MCP is simply a fourth transport
(alongside HTTP / subprocess / import) that connects agents to the compiler.

### Agent skill

The server gives an agent the *capability*; the bundled **agent skill** gives it the
*judgement* — which modality fits the request, how to write a valid spec, how to read
`feasible` / `safety` / `infeasibility_notes`, and what never to claim about a heuristic
score. It ships as [`skills/helix-gene-editing/`](https://github.com/coindef/Helix/tree/main/skills/helix-gene-editing)
(`SKILL.md` + reference docs + eight runnable specs).

```bash
pip install helix-dsl
claude mcp add helix -- helix mcp                            # the capability
cp -r skills/helix-gene-editing ~/.claude/skills/            # the judgement
```

`python skills/build_skill_zip.py` packages it as a deterministic zip for skill
registries. Details → [`skills/README.md`](https://github.com/coindef/Helix/blob/main/skills/README.md).

## Backends

The deterministic spine runs fully offline on honest, clearly-labelled heuristics; each
is a drop-in target for a real tool behind the **same Protocol** — selected by a spec edit.

| role | built-in | real tool (same interface) | status |
|---|---|---|---|
| sequence | `inline` | **`ensembl`**, **`ncbi`**, **`fallback`** (Ensembl→NCBI) | live + fallback |
| on-target | `heuristic_gc` | **`rule_set_1`** (Doench 2014) | **working**, no setup |
| off-target | `mock_seed` | **`cas_offinder_cfd`** (CFD; scan needs a genome) | **working** with a genome |
| repair outcome | `mock_indel` | **`indelphi`** (Shen 2018) | **working** with the package |
| base-edit outcome | `window_heuristic` | `behive` (Arbab 2020) | adapter stub — see below |
| prime-edit outcome | `pe_heuristic` | `pridict` (Mathis 2023) | adapter stub — see below |
| structure / folding | `esmfold` (real, no key) | **AlphaFold3 / Boltz** (`HELIX_FOLDING_BIN`) | ESMFold live |

The verified-real cores (Doench 2014, Doench 2016 CFD) are pure and always on; heavy
models sit behind injectable boundaries — configured in when a genome/tool is present,
and raising a clear error otherwise so the `mock_*` path always runs offline.

> **`behive` and `pridict` are not usable yet.** Both are registered, so
> `helix_list_models` lists them and a spec can name them, but their adapters call a
> signature the upstream packages do not expose (`be_predict_efficiency` wants
> `init_model(...)` then `predict(seq)` → `(df, stats)`; PRIDICT ships a CLI, not an
> importable `predict()`). With the package absent you get a clean `NotConfigured`
> error; with it installed you get a `TypeError`/`AttributeError` mid-compile. The
> existing tests pass because they inject fakes shaped like the adapter, so they cannot
> catch this — `tests/test_adapter_api_contract.py` pins it with strict xfails that will
> flip to XPASS the moment either adapter is corrected. **Until then, base editing stays
> on `window_heuristic` and prime editing on `pe_heuristic`.**

## Web UI

An interactive frontend (React + TypeScript, Vite) over a FastAPI backend — compile a
spec and inspect ranked guides/pegRNAs, outcome metrics, feasibility, safety, provenance,
and a delivery recommendation, in three views (**Table · 3D helix · Cas9 complex**). The
helix is **interactive**: click a base to place an edit, drag to sweep it, and the compiler
recompiles (a 3D → spec round-trip). **Batch** and **Library** modes, a **design compare**,
a design-aware **Models** page, and a server-persisted **run history** round it out.

Built to **WCAG 2.1 AA**: every result is keyboard-reachable — including the 3D helix, where
arrow keys move a base cursor and Enter places the edit — no status is carried by colour
alone, and `prefers-reduced-motion` stops the viewers spinning.

```bash
# One-command product: build the UI once, then serve UI + API on one origin.
cd frontend && npm install && npm run build && cd ..
pip install -e '.[web]' && helix serve       # full app on http://localhost:8000
```

<details>
<summary><b>Advanced</b> — LLM agents · analysis loop · delivery · order export</summary>

<br>

- **LLM agents** (opt-in, `ANTHROPIC_API_KEY`) — `helix author` turns English into a `.hx` spec (validated by the real parser, self-repairing on error); `--strategy llm|rag` resolves `enzyme: auto` (RAG cites a literature corpus); `helix critique` flags weaknesses and proposes **IR-validated** constraint edits; `helix refine` runs critique → recompile autonomously until convergence. The LLM sits behind an injectable client, fully tested offline with a fake.
- **Design → validate → analyse loop** — `helix analyze` runs [CRISPResso2](https://github.com/pinellolab/CRISPResso2) on amplicon reads and **reconciles observed editing against the design's prediction**. In the UI, an *Analyze* card does the same with a pure-Python caller (no install needed).
- **Order-ready oligos** — every design exports guide cloning oligos (Golden Gate), pegRNA extensions, ssODN donors, and validation primers as a table + IDT CSV with a rough cost.
- **Delivery-aware strategy** — recommends RNP / plasmid / LNP / AAV from cargo size and context, honouring the single-AAV limit (an AAV knockout with `enzyme: auto` picks the compact SaCas9).
- **Gene database** — resolve a symbol to its edit window live from Ensembl / NCBI; the **Models** page lists every backend with a live *ready / needs-setup* status.

</details>

## License

[Apache-2.0](https://github.com/coindef/Helix/blob/main/LICENSE).
