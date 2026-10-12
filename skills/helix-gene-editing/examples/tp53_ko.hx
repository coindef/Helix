# Helix grammar — knock out TP53 in HEK293T (offline, inline sequence).
# Compiles to the same IR as examples/tp53_ko.yaml.

helix "TP53_KO_HEK293" {
  organism: human(GRCh38)
  cell_line: HEK293T

  target: gene(TP53) {
    goal: knockout
    region: exon(2..4)
    # SYNTHETIC illustrative window (not real TP53 coordinates).
    sequence: "ATGGCCGATTACGGCTAACCGGATCGATCGGTTACCGGATCCTAGGCTAGCTAGGCTAACGGTTAACCGGTACGATCGATCGGCTAGCTAGCTAGGCCTTAAGGCTAGCGATCGATCGGATCCGGTTAACCGGCTAGCTAGCTAGGCTAGCATCGATCGGCTAGCTAGGCTAACCGGTTAACGGATCGATCGATCGGCTAGCTAGCTAGGCCTAGCTAGCTAGGCTAACCGGTTAACCGG"
  }

  strategy {
    modality: crispr_ko
    enzyme: auto            # strategy resolver -> SpCas9
  }

  constraints {
    on_target.min_efficiency: 0.5
    off_target.max_cfd: 0.2
    guides.count: 3
    avoid: [ homopolymer(>=4), restriction_site(BsaI) ]
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
