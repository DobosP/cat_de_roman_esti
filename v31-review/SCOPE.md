# V31 working scope — hygiene, lower-limb, and cleaning essentials

Status: discovery frozen on landed V30; no product fixture, pack, test, commit, push, or
deployment changed.

## Landed baseline

V31 starts from Cat main `b90c6fd` (`fixture-v30-farm-wardrobe-kitchen`): 2,234
nodes / 8,963 edges / 7,203 aliases / 180 puzzles. The curated pack remains 794
records at SHA-256 `2c7d2eb…023`. Exact critique is 33/33 clean at SHA-256
`5a01894e…349`; the full 222-pending baseline remains SHA-256 `122e35c8…19a`.

## Frozen bounded wave

| Domain | First-class concepts |
|---|---|
| Personal hygiene | Prosop, Săpun, Șampon, Pieptene, Periuță de dinți, Pastă de dinți |
| Lower limb | Genunchi, Coapsă, Gambă, Gleznă, Călcâi |
| Household cleaning | Găleată, Mop, Detergent, Aspirator, Făraș, Burete de vase |

All 17 canonical labels are unresolved. The exact catalog below contains 61
conservative aliases: 78 distinct normalized label/alias surfaces, with zero existing
or intra-wave collision.

```text
Prosop: prosopul, prosoape, prosoapele, prosopului
Săpun: săpunul, săpunuri, săpunurile, săpunului
Șampon: șamponul, șampoane, șampoanele, șamponului
Pieptene: pieptenele, piepteni, pieptenii, pieptenului
Periuță de dinți: periuțe de dinți, periuțele de dinți, periuței de dinți
Pastă de dinți: paste de dinți, pastele de dinți, pastei de dinți

Genunchi: genunchiul, genunchii, genunchiului
Coapsă: coapse, coapsele, coapsei
Gambă: gambe, gambele, gambei
Gleznă: glezne, gleznele, gleznei
Călcâi: călcâiul, călcâie, călcâiele, călcâiului

Găleată: găleți, gălețile, găleții
Mop: mopul, mopuri, mopurile, mopului
Detergent: detergentul, detergenți, detergenții, detergentului
Aspirator: aspiratorul, aspiratoare, aspiratoarele, aspiratorului
Făraș: fărașul, fărașe, fărașele, fărașului
Burete de vase: buretele de vase, bureți de vase, bureții de vase, buretelui de vase
```

Before edges, the expected fixture is 2,251 nodes / 7,264 aliases. The combined
beginner benchmark becomes 288 raw / 286 eligible.

## Sense guardrails

- Keep these outside alias ownership: `ștergar`, `prosop de hârtie`, `gel de duș`,
  `săpunieră`, `balsam`, `perie`, bare `periuță`, `ață dentară`, bare `pastă`, `gel`,
  `rotulă`, `femur`, `pulpă`, `maleolă`, `tendonul lui Ahile`, `lighean`, `căldare`,
  `recipient`, `lavetă`, `înălbitor`, `dezinfectant`, `soluție de curățat`, `aspirație`,
  `aspirator nazal`, bare `burete`, `burete de mare`, `ciupercă`, and `talpă`.
- Continue deferring `Duș`, `Pod`, `Somn`, `Mătură`, `Burete`, `Talpă`, `Cot`, `Umăr`,
  `Braț`, `Spate`, `Burtă`, `Toaletă`, `Perie`, and `Coș` pending explicit sense review.
- `Mătură`, `mătura`, `matură`, and `matura` all normalize to `matura`; do not assign
  that key. Only qualified `Burete de vase` is safe. Bare `Periuță` and `Pastă` remain
  blocked while the dental phrases receive first-class ownership.
- Omit definite forms such as `periuța de dinți`, `pasta de dinți`, `coapsa`, `gamba`,
  `glezna`, and `găleata`: accent folding makes them redundant with their labels.

## Topology and critique contract

- Design three compact local meshes with explicit Romanian predicates, never
  `related_to`. Every new node needs at least four distinct non-distractor neighbors,
  two same-category neighbors, exactly two outgoing choices, and one incoming cue.
- As in V30, point every legacy bridge into V31 and no edge back to the legacy graph.
  Prove each new target clears Contexto reachability 120 and responsive-band 40 while
  the meshes remain one-way sinks that cannot change an old-to-old route.
- Cap each legacy endpoint at three new neighbors. Simulate the exact edge catalog before
  applying; accept zero changed old Contexto score cells, Lanț profiles, or Alchimie
  profiles and no new critique finding.
- Add no curated board and perform no promotion. Preserve both 794-record pack copies
  byte-for-byte, the 7,200-second sliding session TTL, and the 1,000-session cap.
- Only after the graph freezes: add `tests/test_v31_basic_words.py`, run the shared safe
  transaction, regenerate the 33 bound dossiers, update ADR/STATUS, and synchronize the
  public mobile contract in its own worktree.

## Next action

Author and mechanically simulate the exact semantic-edge catalog against this frozen
17-concept/61-alias scope. Do not mutate fixtures until the topology and critique deltas
are accepted.
