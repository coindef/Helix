# Modality recipes

Every recipe is the minimum that compiles offline. Add `constraints { ... }` and
`simulate { ... }` blocks from `examples/`. Valid values come from the Helix IR.

## Common values

| Field | Valid values |
|---|---|
| `strategy.modality` | `crispr_ko`, `base_edit`, `prime_edit`, `hdr`, `deletion`, `crispri`, `crispra` |
| `strategy.enzyme` | `auto`, `SpCas9` (NGG), `SaCas9` (NNGRRT), `Cas12a` (TTTV), `SpG` (NGN), `SpRY` (NRN), `Cas9-NG` (NG). CRISPRi/a always use dCas9. |
| `strategy.editor` | `CBE` (C>T), `ABE` (A>G), `CGBE` (C>G). Required for `base_edit`. |
| `strategy.donor` | `ssodn` (small edits, 50 nt arms), `dsdna` (cassettes, 300 nt arms). Required for `hdr`. |
| `deliver` | `rnp` (default), `plasmid`, `lnp`, `aav` |
| `validate` | `amplicon_seq`, `t7e1` |
| `profile` | `strict`, `lenient`, `screen`, `quick`. Presets for constraints; anything you write wins. |

`enzyme: auto` lets the compiler choose, taking delivery into account. For example an
AAV knockout picks the compact SaCas9.

## Constraints

```
constraints {
  on_target.min_efficiency: 0.5        # 0..1
  off_target.max_cfd: 0.2              # lower is stricter
  gc.min: 0.4                          # spacer GC window
  gc.max: 0.7
  guides.count: 3
  avoid: [ homopolymer(>=4), self_complementary(>=8),
           common_variant(>=0.01), restriction_site(BsaI) ]
}
```

`common_variant` only works with a database-resolved target and
`simulate { variant_source: ensembl }`.

## Knockout (`crispr_ko`)

```
target: gene(SYMBOL) { goal: knockout; sequence: "ACGT..." }
strategy { modality: crispr_ko; enzyme: SpCas9 }
```

Guides are ranked by on-target score, off-target CFD and predicted frameshift fraction.

## Base editing (`base_edit`)

```
target: gene(SYMBOL) { frame: 0; sequence: "ATG..." }
strategy { modality: base_edit; enzyme: SpCas9; editor: CBE }
```

The editor converts bases in the protospacer window (about positions 4-8). With
`frame: 0` each guide gets a consequence label such as `Q>* premature STOP`,
`D>N missense` or `silent (synonymous)`. A CBE that turns a Gln/Trp/Arg codon into a
stop is the "iSTOP" knockout without a double-strand break. See `examples/istop_base_edit.hx`.

## Prime editing (`prime_edit`)

```
target: gene(SYMBOL) { edit: "G>A @ 26"; sequence: "ACGT..." }
strategy { modality: prime_edit; enzyme: SpCas9 }
```

`edit` is `REF>ALT @ POS` with a 1-based position in the window. Insertion:
`->GATTACA @ 26`. Deletion: `REF>- @ POS`. The `REF` bases are checked against the window,
so a wrong one returns `edit ref 'AAA' does not match target at position 40 ('TAG')`;
copy the bases from the sequence rather than guessing. Output entries are pegRNAs (the
summary reports `spacer`, `edit`, `efficiency`). An edit that no pegRNA nick can reach
compiles but returns `feasible: false` with `Requested 1 pegRNAs but only 0 satisfy all
constraints`; try a different position or enzyme.

## HDR knock-in (`hdr`)

```
target: gene(SYMBOL) { edit: "C>T @ 50"; frame: 0; sequence: "ACGT..." }
strategy { modality: hdr; enzyme: SpCas9; donor: ssodn }
deliver: rnp
```

The compiler picks nuclease guides near the edit and builds the donor with homology arms
and a PAM-blocking change so the corrected allele is not re-cut. Recompile with
`"full": true` to read `hdr.sequence`, `hdr.pam_disrupted`, `hdr.recut_note` and
`hdr.silent_pam_block`. Efficiency falls with `cut_to_edit_distance`; prefer guides that
cut within a few bp of the edit.

## Dual-cut deletion (`deletion`)

```
target: gene(SYMBOL) { delete: "40..95"; sequence: "ACGT..." }
strategy { modality: deletion; enzyme: SpCas9 }
```

`delete` is a 1-based inclusive span. The top-level `deletion` block reports the actual
`deletion_size`, `junction` and the two cut positions; the cuts bracket the request, so
the real deletion can be a few bp larger than asked.

## CRISPRi / CRISPRa (`crispri`, `crispra`)

```
target: gene(SYMBOL) { tss: 40; sequence: "ACGT..." }
strategy { modality: crispri }          # or crispra
```

`tss` is the 1-based transcription start site inside the window. CRISPRi is strongest
just downstream of the TSS (about -50 to +300 bp); CRISPRa is strongest upstream (about
-400 to -50 bp). Each guide reports `tss_offset`. A window that does not span the right
side of the TSS will have few or no good guides.

## Simulate block

```
simulate {
  sequence_provider: inline     # inline | ensembl | ncbi | fallback
  on_target:  heuristic_gc      # heuristic_gc | rule_set_1
  off_target: mock_seed         # mock_seed | cas_offinder_cfd
  repair_outcome: mock_indel    # mock_indel | indelphi
  variant_source: none          # none | ensembl
}
```

`base_edit_model` (`window_heuristic` | `behive`) and `prime_edit_model`
(`pe_heuristic` | `pridict`) also exist. External tools (`cas_offinder_cfd`, `indelphi`,
`behive`, `pridict`) need their binary or package on the machine running the server;
call `helix_list_models` and check before selecting one.
