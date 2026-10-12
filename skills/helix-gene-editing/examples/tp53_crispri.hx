# Helix — CRISPRi: dCas9-KRAB silences a gene, no cut. Guides are scored by position
# relative to the TSS (strongest just downstream, ~ -50 to +300 bp).

helix "TP53_CRISPRi" {
  organism: human(GRCh38)
  cell_line: HEK293T

  target: gene(TP53) {
    sequence: "ACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGT"
    tss: 40                 # transcription start site (1-based) within the window
  }

  strategy { modality: crispri }   # enzyme is always dCas9

  constraints {
    on_target.min_efficiency: 0.0
    off_target.max_cfd: 0.3
    guides.count: 3
    avoid: [ homopolymer(>=5) ]
  }

  simulate { sequence_provider: inline; on_target: heuristic_gc; off_target: mock_seed }
  deliver: lnp
  validate: amplicon_seq
}
