export const meta = {
  name: 'verify-authored-content',
  description: 'ADR-0011 verification rail for an authored candidates batch: per-category factual web-verification (Opus) + quality pre-screen (analyst) over <dir>/<category>/candidates.json files, before import_candidates.py.',
  whenToUse: 'After authoring a content batch into <dir>/<category>/candidates.json (nodes, edges, game instances) and BEFORE importing it (the V42 ADR-0065 precedent: this caught 21 duplicate nodes, wrong descriptions, duplicate targets, and a false KG edge). args {dir, repo?, categories}. The orchestrator turns the returned issues into corrections (or verify_factual.json blocks) and the instance verdicts into verify_quality.json.',
  phases: [
    { title: 'Factual', detail: 'Opus web-verifies every node/edge/instance claim' },
    { title: 'Quality', detail: 'analyst pre-screens instances keep/fix/drop' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const DIR = A.dir
const REPO = A.repo || '.'
const CATS = A.categories || []
if (!DIR || !CATS.length) throw new Error('args {dir, categories} required')

const FACTUAL_SCHEMA = {
  type: 'object',
  required: ['category', 'reviewed_refs', 'issues', 'coverage_note'],
  properties: {
    category: { type: 'string', minLength: 1 },
    reviewed_refs: {
      type: 'array',
      uniqueItems: true,
      items: {
        type: 'string',
        minLength: 1,
        description: 'raw node id, canonical "edge:<src_id>-><dst_id>", or "<game>[<idx>]"',
      },
      description: 'exactly one entry for every raw node, edge, and game instance',
    },
    issues: {
      type: 'array',
      items: {
        type: 'object',
        required: ['ref', 'severity', 'issue'],
        properties: {
          ref: { type: 'string', minLength: 1, description: 'node id, canonical "edge:<src_id>-><dst_id>", or "<game>[<idx>]" (0-based)' },
          severity: { type: 'string', enum: ['block', 'fix', 'note'] },
          issue: { type: 'string', minLength: 1 },
          correction: { type: 'string' },
        },
      },
    },
    coverage_note: { type: 'string', minLength: 1, description: 'what was checked; nothing may be silently skipped' },
  },
}

const QUALITY_SCHEMA = {
  type: 'object',
  required: ['category', 'instances', 'coverage_note'],
  properties: {
    category: { type: 'string', minLength: 1 },
    instances: {
      type: 'array',
      items: {
        type: 'object',
        required: ['ref', 'verdict', 'note'],
        properties: {
          ref: { type: 'string', minLength: 1, description: '"<game>[<idx>]" e.g. "conexiuni[0]"' },
          scores: { type: 'object', properties: { recognition: { type: 'number' }, fairness: { type: 'number' }, fun: { type: 'number' } } },
          verdict: { type: 'string', enum: ['keep', 'fix', 'drop'] },
          note: { type: 'string', minLength: 1 },
        },
      },
      description: 'exactly one row for every raw game instance and no other rows',
    },
    coverage_note: { type: 'string', minLength: 1 },
  },
}

phase('Factual')
const factual = await parallel(CATS.map(cat => () =>
  agent(`You are the FACTUAL verifier (ADR-0011 rail: unverifiable = block) for a Romanian culture word-game content batch. Read ${DIR}/${cat}/candidates.json.

For EVERY raw new node: FIRST check the bundled KG (${REPO}/cat_de_roman_esti/fixtures/kg_sample.json) for an existing node with the same or equivalent label/alias — an existing equivalent is a "block" with the canonical id in the correction. Then verify the label and description are factually accurate for Romania (web-check anything not common knowledge). For EVERY raw edge: verify the claimed relation is true and distinctive. For EVERY raw game instance: check embedded factual claims (a group label claiming "X are Y" must be true of all four tiles; a contexto target must not duplicate an already-shipped target — check the pack).

Build reviewed_refs from the RAW candidates before aliases or corrections: include every node id, every edge exactly as "edge:<src_id>-><dst_id>", and every 0-based "<game>[<idx>]" exactly once, including clean entries with no issue. Do not add unknown refs. Set category exactly to "${cat}" and write a nonblank coverage_note.

severity=block for wrong/unverifiable/duplicate; severity=fix with a correction for wording problems; severity=note for soft observations. A later importer rejects unresolved fixes, so fixes must be applied and the batch reverified before import. Return ONLY the structured object.`,
    { agentType: 'general-purpose', model: 'opus', effort: 'high', phase: 'Factual', label: `factual:${cat}`, schema: FACTUAL_SCHEMA })
))

phase('Quality')
const quality = await parallel(CATS.map(cat => () =>
  agent(`You are the QUALITY pre-screener for authored Romanian word-game candidates (the full ADR-0023 judge gate runs later — just cull clearly-bad instances). Read ${DIR}/${cat}/candidates.json and ${REPO}/docs/CRITIQUE_RUBRIC.md sections A + B/C/D/E.

For EVERY raw game instance (ref "<game>[<idx>]", 0-based): simulate an average Romanian player. conexiuni: honest single predicates, one defensible partition, one easy anchor, traps within the mistake budget, and CENSUS the served pack for already-used quads (${REPO}/cat_de_roman_esti/fixtures/games_pack.json). contexto: spontaneously nameable famous target. lant/alchimie: legible steps, satisfying discovery. Emit exactly one row per instance, no missing/duplicate/extra refs, with a nonblank note and verdict keep/fix/drop. Set category exactly to "${cat}" and write a nonblank coverage_note. A later importer rejects unresolved fixes, so fixes must be applied and the batch reverified before import. Return ONLY the structured object.`,
    { agentType: 'analyst', effort: 'high', phase: 'Quality', label: `quality:${cat}`, schema: QUALITY_SCHEMA })
))

return { factual, quality }
