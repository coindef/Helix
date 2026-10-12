# Reading `helix_compile` output

The default call returns a summary. Pass `"full": true` for the whole design
(`guides`, `prime_edits`, `selected`, HDR donors, per-guide `checks`, `variant_hits`).

## Summary fields

| Field | Meaning |
|---|---|
| `spec_name`, `modality`, `enzyme` | What was compiled, with `auto` resolved to a real enzyme. |
| `safety.allowed`, `safety.reasons` | Result of the built-in biosecurity screen. Check this first. |
| `feasible` | Whether the constraints could be met (for example, enough guides passed). |
| `infeasibility_notes` | Why not, and the most common blocking constraint. |
| `candidate_count`, `selected_count` | Guides found vs guides that passed every constraint. |
| `top_guides` | Up to five, best first by `rank`. |
| `target` | Gene, build, window length, sequence `source` and `locus` if resolved. |
| `delivery` | Recommended delivery, approximate cargo size in kb, and notes. |
| `validation_primers` | Forward/reverse primers and amplicon length for amplicon-seq. |
| `deletion` | Only for `deletion`: size, junction, and cut positions. |
| `provenance` | Compiler version and the exact adapter used for each role. |

## Guide fields (nuclease, base edit, HDR, CRISPRi/a)

| Field | Meaning |
|---|---|
| `spacer`, `pam`, `strand` | The 20-23 nt protospacer, its PAM, and which strand it is on. |
| `gc` | Spacer GC fraction. |
| `on_target` | Predicted efficiency, 0 to 1, from the selected `on_target` model. |
| `off_target_cfd` | Worst predicted off-target CFD score, 0 to 1. **Lower is better.** |
| `composite` | The ranking score combining the above. Only meaningful within one compile. |
| `passed` | Met every hard constraint. |
| `consequence` | Protein-level effect (needs `frame`): silent, missense, premature STOP. |
| `frameshift` | Predicted fraction of frameshifting indels (knockout). |
| `cut_to_edit_bp` | HDR: distance from cut to edit. |
| `silent_pam_block` | HDR, three-valued. `true` synonymous, `false` changes an amino acid, `null` unknown or not needed. Read `hdr.pam_disrupted` in the full design. |
| `tss_offset` | CRISPRi/a: signed bp from the TSS (negative is upstream). |

Prime editing entries have `spacer`, `strand`, `edit`, `efficiency`, `passed` and an
optional `consequence`.

## What the numbers are

With the default backends the scores are **heuristics**: `heuristic_gc` (on-target),
`mock_seed` (off-target) and `mock_indel` (repair). They keep the pipeline runnable
offline and give a sensible ranking, but they are not validated predictors. The real
models are `rule_set_1` (Doench 2014 on-target), `cas_offinder_cfd` (CFD off-target; needs
a genome), `indelphi`, `behive` and `pridict`. Always read `provenance.adapters` and tell
the user which were used.

## Blocked runs

When the screen blocks a spec, `safety.allowed` is `false`, `top_guides` is empty and
`infeasibility_notes` is `["Run blocked by biosecurity screen."]`.
