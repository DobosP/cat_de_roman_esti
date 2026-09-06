# V82 playable-content batch — independent verifier review

Valid until: any bound dossier, rubric, KG, Contexto source, candidate, or runtime-evidence byte changes — then treat as history.

Date: 2026-09-06

Reviewer: `session_refactor`

Role: independent adversarial verifier

## Binding and outcome

- Input IDs: exactly `ct_gastronomie_321` through `ct_gastronomie_328`, in ascending order
- Candidate SHA-256: `c1b2bf353fac92124cf2c3866d8ef352eefa7308cfb254d3b01a28922d0171d0`
- KG SHA-256: `fc3ea5a27e3bcb1da72fb3146316d7709da37012dddc494de0d6d4370862a331`
- Runtime evidence SHA-256: `03082d3acfda05f932afa23f90a0bb070c6caf87ac5a432a8e613d541301d522`
- Runtime correction SHA-256: `3eca288d41c14203186a97ac2c3810a322153ea519b72b626740b191392736bf`
- Independent factual JSON SHA-256: `4069e339f82195fc2fa3bc671e22f30c859f18dcca2a68353d2f13f1a135a018`
- Outcome: 8 `promote`, 0 `keep`, 0 `reject`

| ID | Target | Dossier SHA-256 | Review binding | Verdict |
|---|---|---|---|---|
| `ct_gastronomie_321` | Cozonac | `07dcbf55593c0076038bbd5d089cbdd8dfa08c82512fba72e01fce7a276fb01f` | `22ae35f328b84e2cf75c4e42b18463b06f1906060fe189ca9ea5adf27dcc529b` | promote |
| `ct_gastronomie_322` | Pască | `14e82e3ed5697a3eed1b67c1ae895b80392ec8bee171bdaf761347c7c5846c9b` | `714ca1f1ee77069b005beb94865c6ffe18460de4b16b6444ce050ea58d5f680e` | promote |
| `ct_gastronomie_323` | Muștar | `1be6f7094509b794c122cfd95b0b3d0bb2452f24d1fd51ab55bada99f84cd12c` | `7a8f037be6e0272f4b2598bb3ba67c030db87132ef357695f95eae7ad3044a1e` | promote |
| `ct_gastronomie_324` | Mujdei | `dd9f61dedf8a1ed1fffda55050502d9a005963a1e9f1f9babe2ff841ca077e1b` | `8e50fec08e1c4508b8bb12d711fc1b7f83aa446753124e259aa31e917cb9396f` | promote |
| `ct_gastronomie_325` | Ciorbă de burtă | `f0cc9c83f27e94254c316f2dd1a5384ec6f5a7b621efef8da99be9274c065d35` | `5634aecc3d98fcf274a19d11079fbec43a6a5b8c93da9b9b0ea2c413e83110d8` | promote |
| `ct_gastronomie_326` | Urdă | `0812a320983cda912108e37afdf39fbedc733e25418f8877a57300cccd96e76e` | `cfcc5136078218a76e14cd2ffa8f37cc8bb5341cbf49d21db32e4812339bd26f` | promote |
| `ct_gastronomie_327` | Friptură | `cc90747de1d9c5c6a17dcd2644d45e2c3246906b80149090f6a443bb6626ae41` | `ab6daebd245646bc9873fca5a53e06b898063922926a80090c483d9fec51272d` | promote |
| `ct_gastronomie_328` | Bulz | `c6923bf375fb3907ef8f1ab79b97b592e8aaf44bb56d83c3ccaa8e67686798d6` | `54b3df48d0e8bbad2872b6200974a7bc160774f1d3666c48262af7e672594e69` | promote |

The eight verdicts are independent judgments, not a quota. Each target passes A1–A7 and C1–C6 on the bound graph and public-route evidence. Every dossier is lint-clean. The raw JSON is verifier input under ADR-0104; it is not a hand-authored combined V2 verdict artifact and does not apply promotion.

## Refute-first findings

- **Cozonac:** flour and walnut are both rank 2/Fierbinte, backed by dessert, pastry, cocoa, sugar and egg routes. Butter is cold and several fillings plus the holiday words are unknown. The omissions are visible but no longer erase the defining route.
- **Pască:** cheese, dessert, cozonac, flour, egg and milk form independent warm paths. `Paște`, `păști` and raisins are unknown and optional additions are cold. For `normal`, the cheese-pastry route remains sufficient.
- **Muștar:** mici, sauce, grill and condiment occupy ranks 2–7. Plant/seed polysemy is real, and `semințe` is unknown, but the gastronomy context and feedback strongly select the ordinary condiment sense.
- **Mujdei:** garlic and sauce are ranks 2–3, with grill, soup, mici, tomato, salt and water also warm. Fish is cold and oil/lemon very cold; these serving/variant gaps do not displace garlic as the defining identity.
- **Ciorbă de burtă:** the original central contradiction is repaired narrowly. `ciorbă` and projected `burtă` are rank 2, followed by vinegar 10, garlic 11 and cream 19. The `burtă` result is nonwinning and retains body-domain behavior elsewhere. Mămăligă is misleadingly hot through a weak meal-contrast edge, but it does not swamp five direct defining routes. The result text's party reference is not alcohol-dependent play value and does not trigger A5.
- **Urdă:** cheese 2, milk/pies 4 and familiar dairy/use concepts give a coherent `normal` route. `zer` and `urdei` are unknown and sheep is cold. That production-vocabulary gap is meaningful, but an average player need not know the manufacturing term before trying cheese or milk.
- **Friptură:** grill, meat and salt occupy ranks 2–4, with garlic, bread and vegetables warm. Oven and common meat subtypes are unknown or cold, and pan is cold. The generic dish is still most naturally approached through meat and grilling, both excellent routes.
- **Bulz:** mămăligă, cheese, corn and brânză de burduf occupy ranks 2–6. `mălai`, `bulzuri` and `bulzului` are unknown. The lump/lumber/rock and Bihor-place senses require the `normal` band, but food context and the defining feedback make the culinary sense dominant enough.

## Recognition and source check

Every C2 claim rests on at least two independent signals recorded item by item in `verifier-review.json`: historical/current Romanian dictionary evidence plus national media, public institutions, or current cultural/consumer reporting. Cozonac, Muștar, Mujdei and Friptură clear the stronger `usor` familiarity standard. Pască, Urdă and Bulz are deliberately `normal`; their religious, traditional-dairy, pastoral or homographic qualifications are retained rather than presented as universal recognition. Ciorbă de burtă is widely recognizable but remains `normal`, a conservative band.

The cited evidence also supports predicate honesty: Cozonac and Pască ingredients and holiday use; mustard with mici/grill; mujdei as garlic sauce; cow-stomach soup with garlic, vinegar and cream; urdă as whey cheese; friptură as grilled/pan/oven meat; and bulz as hot mămăligă with sheep cheese or urdă.

## Focused verification and limits

`PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest -q tests/test_v82_burta_feedback.py` passed all 7 tests. It covers the actual route, nonwinning feedback, repeat/resume behavior, suggestion privacy, custom-graph boundaries and the one-target whole-graph inventory. The refreshed comparison observed exactly one change among 764 fixed-session guesses: `burtă` for the soup moved from rank 434/Rece to rank 2/Fierbinte; the other 763 observations were byte-equivalent in the comparison model.

The runtime probe set samples 23 targets and is not exhaustive over every input. This verifier is an independent Codex-agent review, not a Romanian-language SME or human playtest. It does not claim perfect vocabulary coverage or enjoyment; the cold/unknown routes above remain explicit limitations.
