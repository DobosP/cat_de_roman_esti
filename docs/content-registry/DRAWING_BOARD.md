# V4 drawing board

Use the candidate ID, recorded reason, evidence reference and retry predicate to
revisit an item. Resolve the recorded prerequisite before rescreening it.

~~~sh
python3 -I scripts/content_registry.py view docs/content-registry/registry.jsonl --state held_recorded
~~~

| Imported scope | Disposition |
| --- | --- |
| V3 N3 concepts | Named holds retained. The V3 seed preserves counts and archived evidence references for the other outcomes. |
| V3 N5 bulk and selected work | Exact intake status retained. The 499 selections are bound to bulk rows and wait for screening, source proof or resolution of their recorded holds. |
| V3 N6–N8 | Named Cratiță and seven N8 family holds retained. The 12 held and three unresolved N7 board prospects remain separate. |
| V2 and V3 handoffs | Source-scoped records retain decisions, file references and the original payload references. |

The retired V3 drawing board records the group-level rejected and tooling-blocked V2
waves. Unavailable archived packets are referenced by the seed and [ADR-0225](../adr/0225-retire-v3-content-loop-artefacts.md).
For live work, add the failed stage and specific retry evidence to the registry when the
underlying proof, source, validator or prerequisite changes.
