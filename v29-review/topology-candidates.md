# V29 topology candidate queue (not yet accepted)

Read-only simulation against v28 found 30 non-generic directed links with no duplicate
direction and no deterministic critique delta across the exact 33 or all 222 pending
items. This queue is separate from the proposed 17-node wave.

| Source → target | Relation | Romanian edge label | Strength |
|---|---|---|---:|
| Curcubeu → Ploaie | `formed_after` | apare după ploaie | .98 |
| Curcubeu → Soare | `formed_by` | se formează în lumina soarelui | .99 |
| Vapor → Dunărea | `travels_on` | navighează pe Dunăre | .97 |
| Vapor → Marea Neagră | `travels_on` | navighează pe Marea Neagră | .98 |
| Săptămână → Zi | `has_part_time` | are șapte zile | .99 |
| Lună calendaristică → Săptămână | `has_part_time` | cuprinde aproximativ patru săptămâni | .96 |
| Lună calendaristică → An | `part_of_time` | este una dintre cele douăsprezece luni ale anului | .99 |
| Surpriză → Bucurie | `may_cause` | poate aduce bucurie | .96 |
| Rușine → Tristețe | `may_cause` | poate aduce tristețe | .94 |
| Mândrie → Familie | `felt_for` | poți simți mândrie pentru familie | .92 |
| Speranță → Iubire | `strengthened_by` | poate fi întărită de iubire | .94 |
| Iubire → Familie | `felt_for` | iubire pentru familie | .98 |
| Liniște → A dormi | `enables_action` | ajută la somn | .97 |
| Spanac → Supă | `used_in` | se folosește în supă | .96 |
| Dinte → Gură | `located_in` | se află în gură | .99 |
| Cer → Soare | `seen_in_sky` | soarele se vede pe cer | .99 |
| Cer → Nor | `contains_weather` | norii apar pe cer | .98 |
| Stație → Autobuz | `serves_transport` | autobuzul oprește în stație | .99 |
| Stație → Gară | `same_travel_role` | puncte de plecare și sosire | .94 |
| Restaurant → Mâncare | `serves_food` | servește mâncare | .99 |
| Restaurant → Bucătărie | `has_room` | are bucătărie | .97 |
| A scrie → Caiet | `uses_surface` | se scrie în caiet | .99 |
| A scrie → Creion | `uses_tool` | se poate scrie cu creionul | .98 |
| A închide → Ușă | `acts_on` | se poate închide ușa | .99 |
| A închide → A deschide | `opposite_action` | este opusul lui „a deschide” | .99 |
| Aragaz → A găti | `enables_action` | se folosește la gătit | .99 |
| Grindină → Nor | `formed_in` | se formează în nori | .98 |
| Grindină → Furtună | `occurs_during` | poate cădea în furtună | .96 |
| Tunet → Fulger | `caused_by` | este produs de fulger | .99 |
| Tunet → Furtună | `occurs_during` | se aude în furtună | .98 |

## Alias candidates

- Meserie: `profesie`, `profesia`, `profesii`, `profesiile`
- Serviciu: `slujbă`, `slujbe`, `slujbele`
- Iubire: `dragoste`, `dragostea`, `dragostei`
- Frică: `teamă`, `temeri`, `temerile`
- Furie: `mânie`, `mânia`, `mâniei`
- Inflections: `dinților`, `curcubeelor`, `pietrelor`, `vapoarelor`,
  `săptămânilor`, `lunilor calendaristice`

These are 22 normalized keys; do not duplicate accentless `slujba` or `teama` because
normalization already covers them. Keep `slujbă` explicitly bound to the employment
sense. Continue to block bare Moon/month forms, `navă`, `rocă`, `calm`, `tăcere`,
`vapori`, and `abur`.

## Required follow-up

Reprofile the aggregate directed graph before accepting this queue. In isolation,
`A scrie → Creion` changes 457 old guess-distance cells and improves 275 responsive
guesses for `ct_viata_de_roman_304`; that broad effect is potentially useful but cannot
be accepted from deterministic critique alone.
