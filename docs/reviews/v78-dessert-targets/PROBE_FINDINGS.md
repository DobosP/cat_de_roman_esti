# V78 fixed-target Contexto probe findings

Candidate batch: `import/gastronomie/candidates.json`, SHA-256
`7a7c22fba430bbd23d84dd33d78979ba6b28670338151daeacf7999dce621b38`.

`runtime_openers.py` exercised 68 one-guess fixed-target sessions through the real
`/api/wordgames/contexto/games/<id>/guess` route on `fixture-v77-flour-associations`.
Each temporary session was deleted after its response. `runtime-openers.json` records
all public responses, resolved IDs, public suggestions, and directed incoming/outgoing
neighborhoods.

| Target | Strong ordinary probes | Missing or weak feedback observed |
|---|---|---|
| Cozonac | Făină: 1 hop/rank 2/Fierbinte; Desert: 1/4/Fierbinte; Fruct: 1/17/Fierbinte; Zahăr: 2/25/Cald; Ou: 2/37/Cald; Dulceață: 2/80/Călduț; Tigaie: 2/47/Cald | Unt and miere are 4 hops/Rece. `gem` and `nucă` are accepted via Contexto projection rather than exact KG resolution and are 4 hops/Rece. `cacao` is likewise projected but 1/15/Fierbinte; English `cocoa`, `rahat`, `stafide`, `aluat`, `sărbătoare`, `Crăciun`, `Paște`, and `cuptor` are unknown. `ciocolată` suggests only `Ciocolata ROM`; `cuptor` suggests `Sculptor`; `rahat` suggests `iRaphahell`; `aluat` suggests `Alună`/`Palat`. |
| Clătite | Făină: 1/2/Fierbinte; Desert: 1/3/Fierbinte; Ou/ouă: 1/5/Fierbinte; Dulceață: 1/7/Fierbinte; Zahăr: 2/11/Fierbinte; Fruct: 2/31/Cald; Cacao: 2/42/Cald | Lapte is 2/40/Cald. Unt, miere, `gem`, and `nucă` are 6 hops/Înghețat; `gem`/`nucă` use Contexto projection. Cacao is a projection, while `cocoa`, `rahat`, `stafide`, `aluat`, holiday terms, oven, and chocolate are unknown with the same misleading suggestions. Tigaie is 4/185/Călduț. |

All tested target spelling/inflection cases won as the intended node: Cozonac
(`cozonac`, upper case, `cozonacul`, `cozonacului`) and Clătite (`clătite`,
accentless/upper case, `clătitele`, singular `clătită`). The unrelated controls
`stilou`, `fotbal`, and `curcubeu` did not win; their per-target feedback remains in
`runtime-openers.json`.

These are local graph/API observations only. They are not factual or quality verdicts,
do not stage the candidates, and do not establish player fairness.
