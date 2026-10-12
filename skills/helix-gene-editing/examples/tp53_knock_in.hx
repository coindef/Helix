# Helix — HDR knock-in: install a precise point mutation with a homology-arm donor.
# A nuclease cuts near the edit; a donor (ssODN here) carries homology arms plus a
# silent PAM-blocking mutation, and the cell copies in the change during repair.
#   `edit`  names the change, reusing the prime-edit grammar (sub / ins / del),
#           e.g. "C>T @ 50" (point mutation) or "->GATTACAAG @ 60" (insert a tag).
#   `donor` picks the template format: ssodn (small edits) or dsdna (larger cassettes).

helix "TP53_C50T_knock_in" {
  organism: human(GRCh38)
  cell_line: HEK293T

  target: gene(TP53) {
    sequence: "ACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGT"
    edit: "C>T @ 50"
  }

  strategy {
    modality: hdr
    enzyme:   SpCas9
    donor:    ssodn        # single-stranded oligo donor; use dsdna for larger inserts
  }

  constraints {
    on_target.min_efficiency: 0.0
    off_target.max_cfd: 0.3
    guides.count: 1
    avoid: [ homopolymer(>=5) ]
  }

  simulate {
    sequence_provider: inline
    on_target: heuristic_gc     # rule_set_1 also works for SpCas9
    off_target: mock_seed
  }

  deliver: rnp                  # RNP + ssODN nucleofection is the standard knock-in route
  validate: amplicon_seq
}
