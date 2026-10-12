# Helix — dual-cut deletion: excise a region between two flanking cuts. Two guides
# are chosen so their cuts bracket the requested span; NHEJ rejoins the ends.

helix "TP53_del_40_95" {
  organism: human(GRCh38)
  cell_line: HEK293T

  target: gene(TP53) {
    sequence: "ACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGTACCTGCACGTAGCTGCTAGCTAGCTGGCGT"
    delete: "40..95"        # 1-based inclusive region to remove
  }

  strategy {
    modality: deletion
    enzyme:   SpCas9
  }

  constraints {
    on_target.min_efficiency: 0.0
    off_target.max_cfd: 0.3
    guides.count: 2
    avoid: [ homopolymer(>=5) ]
  }

  simulate { sequence_provider: inline; on_target: heuristic_gc; off_target: mock_seed }
  deliver: rnp
  validate: amplicon_seq
}
