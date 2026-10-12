# Helix — prime edit (a G>A substitution) in a synthetic TP53 window.
# Prime editing installs a templated edit via a pegRNA (nicking guide + PBS + RTT).
# `target.edit` names the desired change as REF>ALT @ POS (1-based window position).

helix "TP53_PE_G26A" {
  organism: human(GRCh38)
  cell_line: HEK293T

  target: gene(TP53) {
    edit: "G>A @ 26"
    sequence: "ACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGT"
  }

  strategy {
    modality: prime_edit
    enzyme:   SpCas9
  }

  constraints {
    on_target.min_efficiency: 0.0
    guides.count: 1
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
