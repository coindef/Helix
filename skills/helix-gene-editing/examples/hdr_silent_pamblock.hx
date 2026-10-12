# Helix — HDR knock-in with a guaranteed-synonymous PAM-block. Installing a point
# mutation by HDR needs a second, silent mutation that stops the nuclease re-cutting
# the corrected allele. In a coding region that PAM-block must NOT change the protein.
# With `frame: 0`, Helix chooses a PAM-breaking base substitution that is synonymous
# and proves it — the guide detail shows "PAM-block: synonymous" (or flags it if no
# silent option exists). It also reports the consequence of the intended edit itself.

helix "GENE_HDR_silent_pamblock" {
  organism: human(GRCh38)
  cell_line: HEK293T

  target: gene(GENE) {
    goal: knockout
    frame: 0
    sequence: "ATGGCCAAGCTGACCGAGCTGCAGGACAAGCTGACCGAGTGGAAGCTGACCGAGCTGCAGGACAAGCTGACCGAGCTGCAGGACAAGCTGACCGAGTGGAAGCTGACCGAGCTG"
    edit: "G>A @ 75"
  }

  strategy { modality: hdr; enzyme: SpCas9; donor: ssodn }

  constraints {
    on_target.min_efficiency: 0.3
    guides.count: 3
  }

  simulate {
    sequence_provider: inline
    on_target: heuristic_gc
    off_target: mock_seed
    repair_outcome: mock_indel
  }

  deliver: rnp
  validate: amplicon_seq
}
