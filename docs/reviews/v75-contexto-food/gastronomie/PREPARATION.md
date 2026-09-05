# V75 Contexto food candidate preparation

Valid until: this frozen V75 candidate batch changes — then treat as history.

This is the pre-import author record. See the wave README and allocation receipt for subsequent staging, review, and promotion.

This directory contains candidate input and read-only KG screening only. It contains no factual or quality verification artifacts, no approval verdicts, and has not been imported.

- Candidate SHA-256: `sha256:baef6c35007d7da7982058f0bbb220b3fbf95f91377247412368f63898e38431`
- KG fixture SHA-256: `sha256:fa9575db4819fa314e43218a0ad953f52c3e6ee2e34cac105dbc88e2d2247106`
- Candidate schema: exactly `nodes`, `edges`, `conexiuni`, `contexto`, `lant`, and `alchimie` arrays; topology arrays are empty.
- Five Contexto candidate rows use existing KG targets and declare `usor`; the importer will independently revalidate runtime floors.
- `kg_screening_dossiers.json` records direct runtime predecessors and reachability only. Recognition, dominant sense, nameability, and intuitive-opener findings remain unassessed for independent reviewers.
