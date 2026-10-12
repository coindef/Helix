---
name: helix-gene-editing
description: Design reproducible CRISPR gene edits with the Helix compiler through its MCP server. Use when the user asks to design guide RNAs, plan a knockout, base edit (CBE/ABE), prime edit (pegRNA), HDR knock-in, dual-cut deletion, or CRISPRi/CRISPRa experiment, to check whether an edit is feasible under constraints (efficiency, off-target, GC, SNPs), to predict the protein consequence of an edit (silent, missense, premature STOP), or to turn a gene-editing goal into a versionable spec. Writes a declarative .hx spec, compiles it with the deterministic Helix compiler, and reports ranked, safety-screened, provenance-stamped guides.
license: Apache-2.0
compatibility: Requires Python 3.9+ and the helix-dsl package (pip install helix-dsl) registered as an MCP server. Works offline with inline sequences; Ensembl/NCBI gene lookup needs network access.
metadata:
  author: Alex Yu
  version: "0.1.1"
  homepage: https://github.com/coindef/Helix
---

# Helix gene-editing design

Helix treats a gene-editing experiment as source code. **You write a small declarative
spec; the deterministic Helix compiler produces the design.** You never score guides,
call bioinformatics tools, or invent sequences yourself. Everything you report comes
from `helix_compile`, so the result is reproducible and auditable.

## 1. Setup (once)

The skill needs the Helix MCP server. Check whether the `helix_compile` tool is
available. If it is not:

1. Install the package: `pip install helix-dsl`
2. Register the server with the MCP client:

   ```json
   { "mcpServers": { "helix": { "command": "helix", "args": ["mcp"] } } }
   ```

   Claude Code: `claude mcp add helix -- helix mcp`
3. Restart the client so the four tools appear: `helix_reference`, `helix_compile`,
   `helix_resolve_gene`, `helix_list_models`.

If the user cannot install anything, say so and stop. Do not hand-write guides.

## 2. Workflow

1. **Clarify the edit.** You need: gene or sequence, organism/genome build, the kind of
   edit (see the table below), and any hard constraints. Ask only for what is missing.
2. **Call `helix_reference` first** in a new session. It returns the exact grammar and
   authoring guide for the installed version. Trust it over this file if they differ.
3. **Get a target sequence** (see "Choosing a target" below).
4. **Write the `.hx` spec.** Start from the closest file in `examples/` and adapt it.
5. **Call `helix_compile`** with `source` set to the spec text.
6. **Check the verdicts in this order:** `safety.allowed`, then `feasible`, then
   `infeasibility_notes`. Only then read `top_guides`.
7. **Iterate.** If infeasible, loosen one constraint or change strategy, then recompile.
   Change one thing at a time and tell the user what you changed and why.
8. **Report** using the template in "Reporting results", and save the final spec so the
   user can version it.

## 3. Pick the modality

| User wants to... | `strategy.modality` | Also set |
|---|---|---|
| Knock a gene out with a cut | `crispr_ko` | `enzyme`, `target.goal: knockout` |
| Change one base (C>T or A>G) without a double-strand break | `base_edit` | `editor: CBE` or `ABE` (`CGBE` for C>G), `target.frame` |
| Install a templated substitution, insertion or deletion | `prime_edit` | `target.edit: "G>A @ 26"` |
| Knock in a point mutation or tag with a donor | `hdr` | `target.edit`, `donor: ssodn` or `dsdna`, `target.frame` |
| Remove a defined region with two cuts | `deletion` | `target.delete: "40..95"` |
| Silence a gene without cutting | `crispri` | `target.tss` |
| Activate a gene without cutting | `crispra` | `target.tss` |

Details, valid values and edit syntax: `references/modalities.md`.

## 4. Choosing a target

- **Offline and deterministic (preferred for drafts):** put the sequence inline,
  `sequence: "ACGT..."`, and set `simulate { sequence_provider: inline }`.
- **Real coordinates:** omit `sequence`, keep `gene(SYMBOL)`, and set
  `sequence_provider: ensembl` (or `ncbi`). Or call `helix_resolve_gene` first, check the
  returned `locus`, and paste the window inline.
- **Never invent a gene sequence.** The sequences in `examples/` are synthetic
  placeholders, not real TP53 or HBB coordinates. If the user did not supply a sequence
  and there is no network, tell them the result is illustrative only.
- For any **coding** edit set `target { frame: 0 }` (codon phase of window position 0,
  window on the sense strand) so guides get a protein `consequence`. If you are not sure
  of the frame, leave it out and say that consequence calls were not made.

## 5. Reporting results

Always include these, in plain language:

- **Verdict:** safety allowed or blocked, feasible or not, and how many of the candidates
  passed (`selected_count` of `candidate_count`).
- **Top guides:** rank, spacer, PAM, strand, on-target score, off-target CFD, and
  `consequence` if present.
- **For HDR, recompile with `"full": true`.** The summary only carries
  `silent_pam_block`, which is three-valued: `true` = the PAM-block is synonymous,
  `false` = it changes an amino acid (flag this to the user), `null` = unknown or not
  needed. Read `guides[i].hdr.pam_disrupted` and `hdr.recut_note` to tell which, and
  take the donor from `hdr.sequence`. Never describe a guide as "re-cut protected" unless
  `pam_disrupted` is `true`.
- **For deletions,** report the top-level `deletion` block (`deletion_size`, `junction`,
  `left_cut`, `right_cut`), not just the guides.
- **Which backends scored them**: read `provenance.adapters`. The built-in scorers
  (`heuristic_gc`, `mock_seed`, `mock_indel`) are labelled heuristics, not validated
  predictors. Say so. Call `helix_list_models` to see what else is available and suggest
  `rule_set_1` (on-target) or `cas_offinder_cfd` (off-target, needs a genome) when the
  user needs more than a draft.
- **The final spec**, in a code block, so it can be committed to git.
- **Next step for the bench:** the user must validate by amplicon sequencing. Helix
  predicts; it does not replace the experiment.

## 6. Guardrails

- If `safety.allowed` is `false`, report the `reasons` and stop. Do not reword, split or
  disguise the spec to get past the screen (for example by changing `organism` or
  `cell_line` to unrelated text).
- `safety.allowed: true` is not clearance. The built-in screen is a minimal rule-based
  floor (a short regulated-organism watchlist and a germline cell-context check). Say so
  if the user asks whether the experiment is "approved", and point them to their
  institution's biosafety and ethics review.
- Do not present a heuristic score as an experimental result or a clinical claim.
- Do not claim a guide "will work". Say it is "predicted" and name the model.
- Helix is for research design. Do not use it to plan human germline edits or edits
  intended to enhance pathogens or toxin production.
- Never put API keys in a spec. The optional LLM commands read `ANTHROPIC_API_KEY` from
  the environment.

## 7. When something goes wrong

See `references/troubleshooting.md`. The common ones:

- `Error: ... (line N, col M)`: syntax error. Fix that line and recompile.
- `Internal error: Ensembl request failed`: no network or unknown symbol. Switch to an
  inline sequence and say the target is user-supplied.
- `feasible: false`: read `infeasibility_notes`; usually `guides.count` is too high or
  `on_target.min_efficiency` / `off_target.max_cfd` is too strict for the window.

## Supporting files

- `references/modalities.md`: per-modality spec recipes and valid values.
- `references/reading-results.md`: what every field in the compile output means.
- `references/troubleshooting.md`: errors and fixes.
- `examples/*.hx`: eight offline specs that compile as-is, covering knockout, base
  editing, prime editing, HDR, deletion and CRISPRi. For CRISPRa, copy `tp53_crispri.hx`,
  set `modality: crispra` and put `tss` downstream of the guides you want.
