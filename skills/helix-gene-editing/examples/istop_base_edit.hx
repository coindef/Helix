# Helix — CBE "iSTOP" knockout. With `frame: 0`, Helix reads each guide's edited
# window in-frame and reports the protein consequence. A C>T that turns a Gln (CAG)
# codon into a STOP installs a premature stop — a clean knockout with no double-strand
# break. Guides that do this show a red "Q>* premature STOP" badge; guides whose edit
# is silent show a green "synonymous" badge. This is how you pick a base-editing KO.

helix "GENE_iSTOP_CBE" {
  organism: human(GRCh38)
  cell_line: HEK293T

  target: gene(GENE) {
    goal: knockout
    frame: 0                 # window position 0 is codon phase 0 (window = coding/sense strand)
    sequence: "ATGATCATCGGCACCTGGAAGAACCGAAAGATCGCCATCACCCAGGGCAACGACCAATGGCAG"
  }

  strategy { modality: base_edit; enzyme: SpCas9; editor: CBE }

  constraints {
    on_target.min_efficiency: 0.3
    off_target.max_cfd: 0.3
    guides.count: 2
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
