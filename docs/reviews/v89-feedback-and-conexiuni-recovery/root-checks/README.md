# V89 root development checks

Valid until: V89 is superseded — then treat as history.

[Original logs](logs.json) preserve the serial supported import, three dossiers, portable
artifact, two rejections/one promotion, rankings/derived regeneration and seeded-start
regeneration. Every transaction completed with exit0 before the next mutation began.
The served KG and mobile fixture were not regenerated. Seeded starts remain byte-identical.

The first focused feedback run passed11 tests; the following Ruff check found one overlong
decorator. The final15-case test run adds exact serialized private-answer checks and four
projected-typo privacy controls. All15 and Ruff pass. These are focused checks, not the full
integration matrix. Fresh constrained Python3.14 installation output is also preserved.
