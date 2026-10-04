# Historical saved-prefix corpus

`legacy-saved-prefixes-v92.json` freezes the nine archived mechanics books into the
first productive recipe order used by the independent historical discovery audit.
Each step records its pair, earned result and newly unlocked supplies. Replaying every
prefix yields 1009 distinct saved collections. The trace was frozen from the source
world JSON before calling the Go restore implementation; it is not a native self-oracle.

Source: `cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json` SHA-256
`0b3fea2c30b4c729cbe8398bc467e5a4f7e6a443ff886023a07d9bf0e40e9f44`.
Reference iteration: `scripts/audit_alchimie_discovery_world.py`, historical migration
loop. Corpus SHA-256: `51eadd294f043991fb9a518a0ea62b7bd1249f2f1d3878db91cd0d3253ab1718`.
The native test pins source/corpus/count identities, retains every earned concept and
craft order, and exercises the 1000-entry session bound. Any new world requires fresh
independent compatibility evidence; existing corpus bytes remain historical evidence.
