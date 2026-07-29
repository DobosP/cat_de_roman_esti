export const meta = {
  name: 'game-audit-recon',
  description: 'Analyst fan-out that builds condensed dossiers for a fun/playability audit: per-game mechanics+UX+friction+sample boards, refinement history, content pipeline, release path, and the cross-game meta-loop.',
  whenToUse: 'Before a fun/quality wave (the V42 ADR-0065 precedent): run first so the orchestrating model judges from condensed evidence instead of reading the whole repo. args {repo?: path (default "."), games?: [{key, hint}]}. ~10 Sonnet analysts; the orchestrator stays the judge.',
  phases: [{ title: 'Gather', detail: 'analyst dossiers over the checkout' }],
}

const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const REPO = A.repo || '.'

const GAME_DOSSIER = {
  type: 'object',
  required: ['game', 'mechanics', 'ux_flow', 'friction', 'sample_boards', 'content_stats', 'anchors'],
  properties: {
    game: { type: 'string' },
    mechanics: { type: 'string', description: 'How the game plays: rules, win/lose, scoring, feedback loop, session flow, difficulty tiers. Concrete, not marketing.' },
    ux_flow: { type: 'string', description: 'Frontend experience: screens, taps, onboarding, in-game feedback, error/recovery, mobile ergonomics.' },
    friction: {
      type: 'array',
      items: {
        type: 'object',
        required: ['issue', 'evidence', 'severity'],
        properties: {
          issue: { type: 'string' },
          evidence: { type: 'string', description: 'file:line anchors' },
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
        },
      },
      description: 'Everything that could make this game hard to play or unfun, judged as a skeptical playtester reading the code.',
    },
    fun_evidence: { type: 'string', description: 'What docs/rankings/pilot notes say about fun; any player evidence; the editorial ranking and its basis.' },
    sample_boards: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'content_json'],
        properties: {
          id: { type: 'string' },
          difficulty: { type: 'string' },
          category: { type: 'string' },
          rank_or_score: { type: 'string' },
          content_json: { type: 'string', description: 'FULL board content verbatim as JSON, including hidden answers, so the orchestrator can judge quality.' },
        },
      },
      description: '6 real boards from the runtime-eligible/preferred set: 2 best-ranked, 2 worst-still-eligible, 2 mid.',
    },
    content_stats: { type: 'string', description: 'Eligible/preferred counts, category spread, thin shelves, pending-vs-approved for this game.' },
    anchors: { type: 'array', items: { type: 'string' } },
  },
}

const DOC_DOSSIER = {
  type: 'object',
  required: ['summary', 'key_facts', 'open_issues', 'anchors'],
  properties: {
    summary: { type: 'string' },
    key_facts: { type: 'array', items: { type: 'string' } },
    open_issues: { type: 'array', items: { type: 'string', description: 'Unresolved problems, deferred decisions, known gaps' } },
    anchors: { type: 'array', items: { type: 'string' } },
  },
}

const COMMON = `You are gathering for the orchestrating model, which will act as game designer and judge. Work in the read-only checkout at ${REPO}. Start from docs/agent-map.md and docs/STATUS.md to locate things fast; do not load build artifacts or node_modules. Coverage note required: state anything you skipped or sampled. Your final output is raw data for a machine, not a human-facing message.`

const DEFAULT_GAMES = [
  { key: 'conexiuni', hint: 'Conexiuni (Connections-style groups); boards in the curated pack, ranking sidecar per docs/PILOT_BOARD_RANKING.md.' },
  { key: 'cald_sau_rece', hint: 'Cald sau Rece (contexto-like semantic guessing over the KG).' },
  { key: 'lant', hint: 'Lanțul Cuvintelor (directed semantic ladder with undo and hop cap).' },
  { key: 'alchimie', hint: 'Alchimie (pair-combination crafting with sparse recipes).' },
  { key: 'intrusul', hint: 'Intrusul (odd-one-out, derived catalog-only game).' },
  { key: 'perechi', hint: 'Perechi (pairs matching, derived catalog-only game).' },
]
const GAMES = A.games || DEFAULT_GAMES

phase('Gather')
const results = await parallel([
  ...GAMES.map(g => () => agent(
    `${COMMON}\n\nBuild a complete dossier on the game "${g.key}". ${g.hint}\n\nCover: (1) exact mechanics from the backend engine code; (2) the frontend UX flow; (3) ALL friction points with file:line evidence; (4) fun evidence from docs; (5) six verbatim sample boards from the runtime-eligible/preferred stock (2 best, 2 worst-still-eligible, 2 mid — full JSON including hidden answers); (6) content stats: eligible counts, category spread, thin shelves.`,
    { agentType: 'analyst', label: `dossier:${g.key}`, phase: 'Gather', schema: GAME_DOSSIER },
  )),
  () => agent(
    `${COMMON}\n\nSynthesize the refinement history: read every V*_ docs file and the relevant ADRs. Extract what fun/playability problems were already identified, fixed, or explicitly deferred, plus any player evidence. List open_issues exhaustively — this is the backlog the orchestrator will triage.`,
    { agentType: 'analyst', label: 'dossier:history', phase: 'Gather', schema: DOC_DOSSIER },
  ),
  () => agent(
    `${COMMON}\n\nBuild a dossier on the CONTENT PIPELINE: how new boards get created, validated, ranked, critiqued (docs/CRITIQUE_RUBRIC.md), approved, and bundled. Include the exact file format + required fields to author a new board for each game, what approved/pending/eligible mean, and how the critique gate is invoked. The orchestrator will author new boards, so precision on formats and gates matters most.`,
    { agentType: 'analyst', label: 'dossier:content-pipeline', phase: 'Gather', schema: DOC_DOSSIER },
  ),
  () => agent(
    `${COMMON}\n\nBuild a dossier on the RELEASE PATH: docs/DEPLOY.md, compose files, Dockerfile, compliance docs, mobile contract, bundle budget. Extract the deploy procedure, what changed vs the currently deployed artifact, what must stay off, risks and rollback, and list open_issues = every blocker between main and a public release.`,
    { agentType: 'analyst', label: 'dossier:release-path', phase: 'Gather', schema: DOC_DOSSIER },
  ),
  () => agent(
    `${COMMON}\n\nBuild a dossier on the CROSS-GAME META-LOOP: lobby, daily circuit, scoring, progression, retention hooks — everything around the games. open_issues = everything that could make a new anonymous player bounce in the first 5 minutes, and every missing repeat-play hook.`,
    { agentType: 'analyst', label: 'dossier:meta-loop', phase: 'Gather', schema: DOC_DOSSIER },
  ),
])

const games = {}
GAMES.forEach((g, i) => { games[g.key] = results[i] })
const n = GAMES.length
return { games, history: results[n], content_pipeline: results[n + 1], release_path: results[n + 2], meta_loop: results[n + 3] }
