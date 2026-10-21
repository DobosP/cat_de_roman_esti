# KIT_BUMP core-v1.13 — qualification record

Valid until: the next KIT_BUMP; then treat as history.

Decision: [ADR-0209](../../adr/0209-kit-bump-core-v1-13.md). Branch `fix/kit-bump-core-v112` on `main` 8a5e6f28;
operator agent:claude-code (PROGRAM E8). Status: qualification in progress; no gate result is claimed here yet.

| Step | Command | Result |
|---|---|---|
| core-v1.12 sync (refused) | `GATE_OPERATOR=agent:claude-code bash scripts/gate.sh kit:sync --sha 3423601c22a6b89168a45895b23591d52c7f9d16` | fail `consumer-config` "Higher core toolchain version refused" (`62913516…`), tree unchanged |
| Stage + runner + probe | a6975640, 1d82f362, 8fced572 | trust pin `80e5a3a2…` |
| kit:sync | `GATE_OPERATOR=agent:claude-code bash scripts/gate.sh kit:sync --sha 8fced572308520c94e6f7ee8ddec322c1ad0b5f0` | pass 9/9 `4ea0807f…` |
| deps | `GATE_OPERATOR=agent:claude-code bash scripts/gate.sh deps --sha 8fced572308520c94e6f7ee8ddec322c1ad0b5f0 --dirty` | pass 4/4 `9a81bbc9…`, no further change |
