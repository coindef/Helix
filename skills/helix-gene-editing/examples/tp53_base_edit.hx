# Helix — cytosine base edit (CBE, C->T) in a synthetic TP53 window.
# Base editors convert a target base within the protospacer window (positions 4-8);
# no double-strand break. `editor` selects the chemistry (CBE or ABE).

helix "TP53_CBE_HEK293" {
  organism: human(GRCh38)
  cell_line: HEK293T

  target: gene(TP53) {
    sequence: "ACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGT"
  }

  strategy {
    modality: base_edit
    enzyme:   SpCas9
    editor:   CBE          # cytosine base editor (C -> T); use ABE for A -> G
  }

  constraints {
    on_target.min_efficiency: 0.0
    guides.count: 3
    avoid: [ homopolymer(>=4) ]
  }

  simulate {
    sequence_provider: inline
    on_target: heuristic_gc     # rule_set_1 also works for SpCas9
    off_target: mock_seed
    repair_outcome: mock_indel  # unused for base editing
  }

  deliver: rnp
  validate: amplicon_seq
}
