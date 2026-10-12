# Troubleshooting

## Tool not available

`helix_compile` is missing from the tool list: the server is not registered or not
installed. Run `pip install helix-dsl`, add `{ "command": "helix", "args": ["mcp"] }` to
the client's MCP servers, and restart. To confirm outside the client: `helix --version`.

## Errors returned by `helix_compile`

| Message | Cause and fix |
|---|---|
| `Error: expected ':' or '{' after key (line N, col M)` | Syntax error at that line. Keys need `key: value` or `key { ... }`. |
| `Error: strategy.modality: 'x' is not valid - expected ...` | Typo in an enum. Use a value from `modalities.md`. |
| `Error: prime editing requires target.edit (e.g. 'A>G @ 12').` | Add `edit: "REF>ALT @ POS"` inside `target`. |
| `Error: HDR knock-in requires target.edit (...)` / `...requires strategy.donor (ssodn or dsdna).` | Add the missing `edit` (in `target`) or `donor` (in `strategy`). |
| `Error: base editing requires strategy.editor (CBE or ABE).` | Add `editor`. `CGBE` is also accepted although the message omits it. |
| `Error: edit ref 'X' does not match target at position N ('Y')` | The `REF` in `edit` differs from the window. Copy the bases from the sequence. |
| `Internal error: Ensembl request failed: ...` | No network, wrong symbol, or the database is down. Use `sequence_provider: inline` with a user-supplied sequence, or `fallback` to try Ensembl then NCBI. State that the target is user-supplied. |
| `Unknown tool: ...` | Tool name typo. The four tools are `helix_reference`, `helix_compile`, `helix_resolve_gene`, `helix_list_models`. |

## `feasible: false`

Example note: `Requested 40 guides but only 6 satisfy all constraints.` followed by
`Most common blocker: 'off_target_max_cfd' (26 guides). Consider relaxing it.`

1. Read the named blocker. It is the constraint rejecting the most candidates.
2. Relax that one constraint, or reduce `guides.count`, and recompile.
3. If the window is short, ask the user for a longer one; a longer window offers more
   candidate PAM sites.
4. Consider a relaxed-PAM enzyme (`SpG`, `Cas9-NG`, `SpRY`) to widen the search space,
   noting the off-target trade-off.
5. Tell the user every constraint you loosened. Do not loosen silently to reach green.

## No consequence labels

Guides lack `consequence`. Set `target { frame: N }`. Use 0 only if window position 0 is
the first base of a codon on the sense strand; otherwise say consequence is unknown.

## Needs an external model

`cas_offinder_cfd`, `indelphi`, `behive` and `pridict` need their binary or package on the
machine running the server. If the compile reports it is unavailable, fall back to the
`mock_*` / heuristic backend and say so.

## Reproducing a run

The spec plus `provenance` is the reproducible record. Save the exact `.hx` text. To
re-run outside the agent: `helix compile design.hx -o out` writes `out/design.json` and
`out/protocol.md`.
