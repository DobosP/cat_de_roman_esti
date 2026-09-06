# V80 Clătite fixed-target runtime probes

This is probe evidence only. It contains no factual/quality verdict and does not stage or promote the candidate.

## Binding and method

- Candidate: `import/gastronomie/candidates.json`, SHA-256 `87e8b3b4133a82c83542070f6f3228d7482b8e775d66fed660574148220e67dd`.
- Result capture: `runtime-openers.json`, SHA-256 `251be6d78f287b878fdd1b7a1734773cad670f58683efae8110026cb99859ca3`. The earlier outgoing-only capture remains as `runtime-openers.pre-incoming.json`, SHA-256 `3ff9fc7297af54bf475875c4b5c8e98d5e0d4324db9e23d2d838c37d35bfc2f0`.
- Runner: `runtime_probes.py`, SHA-256 `b00a63c0621fe8850421efa3010b6d587206dff101ccf15cb43004388fe54786`.
- Fixed target is `n_v3gas_clatite` / **Clătite**, created with the real in-process Django Contexto API route at `usor`; every one-word probe uses a fresh temporary session, which the runner deletes. A Papanași (`n_gas_papanasi`) fixed-target control uses the same API path.
- Captured bindings: KG `sha256:c158262f7216c3b7ec2381f9fbe5ffc5d2ac987ad6a1d56de61e58ec276eb370`; V79 projection `sha256:d6b80f7cb7abcce77c64d04d94ff2cf7e178ffd6bb1d48cbd7b4a9e441fd9cb1`; Contexto route `sha256:bdef59b96dd7f3b06321b20463987e7d4140625e60b07bc043383cd3caf3282f`.

Run from this worktree:

```bash
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python \
  /home/dobo/work/_temp/v80-clatite-target/runtime_probes.py \
  > /home/dobo/work/_temp/v80-clatite-target/runtime-openers.json
```

## Clătite results

| Submitted input | Resolution / result |
|---|---|
| Făină / `faina` | one hop, rank 2, Fierbinte |
| Zahăr | two hops, rank 11, Fierbinte |
| Ou / `ouă` | one hop, rank 5, Fierbinte |
| Desert | one hop, rank 3, Fierbinte |
| Gem | one hop, rank 8, Fierbinte; synthetic public projection ID |
| Dulceață | one hop, rank 7, Fierbinte |
| Lapte | two hops, rank 40, Cald |
| Brânză | two hops, rank 30, Cald |
| Smântână | two hops, rank 22, Cald |
| Tigaie | four hops, rank 185, Călduț |
| Apă | three hops, rank 181, Călduț |
| Unt / Miere | six hops, rank 1698, Înghețat |
| Nucă | six hops, rank 1699, Înghețat |
| Ulei | six hops, rank 1698, Înghețat |
| `ciocolată` | unresolved, no attempt; suggestion `Ciocolata ROM` |
| `aluat` | unresolved, no attempt; suggestions `Alună`, `Palat` |
| `chocolate` / `dough` | unresolved, no attempt; no suggestions |
| Clătite / `clatite` / Clătită / `clatita` / Clătitele / Clătitei / Clătitelor | exact rank 1 win |

The **incoming** directed non-distractor neighborhood used by Contexto guesses has nine recorded neighbors: Făină (0.97), Desert (0.82), Papanași (0.78), Ou (0.76), Înghețată (0.72), Dulceață (0.70), Plăcinte (0.66), Gogoși (0.65), and Brânză cu smântână (0.45). The separate **outgoing** set has eight and omits Făină because the V77 ingredient edge is directed Făină→Clătite. Full IDs, edges, relations and responses are in the JSON capture.

## Controls and session behavior

For the Papanași fixed-target control, Gem and Dulceață are each one hop/Fierbinte (ranks 13 and 12); Făină is two hops/Cald (rank 24); Stilou is four hops/Rece (rank 458); `chocolate` is unresolved without an attempt. These distinguish the target-specific ranks from generic acceptance.

A Clătite Gem attempt remains nonwinning and takes one attempt; a subsequent GET returns the same one guess/attempt, and normalized ` GEM ` returns `repeat` without increasing the count. The capture contains only public API responses; it has no target ID/label fields in the normal game-response envelopes.
