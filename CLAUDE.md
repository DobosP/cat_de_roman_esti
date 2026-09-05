# Claude Code — cat_de_roman_esti
@AGENTS.md
Read and follow `AGENTS.md` (imported above). Current truth: `docs/STATUS.md`; fleet view: vault `NOW.md`.
- Workflow tool scripts in `.claude/workflows/`: `critique-games` (rubric critique + adversarial re-judge; run
  `scripts/critique_pack.py --dossier <dir>` first), `game-audit-recon` (analyst dossiers before a fun/quality
  wave), `verify-authored-content` (factual + quality pre-screen before `scripts/import_candidates.py`).
- Roles and rungs for those workflows come from the `agent-routing` skill (the ladder in `fleet-tiers.sh`);
  never hard-code model ids here.
