export const meta = {
  name: 'critique-games',
  description: 'Hard-critique curated pack items against docs/CRITIQUE_RUBRIC.md: Sonnet analysts critique per-item dossiers, Opus verifiers adversarially re-judge with live Romanian-relevance web checks (ADR-0023).',
  whenToUse: 'Before promoting pack items to approved (gate mode), or to sweep existing approved stock (sweep mode). Run `python scripts/critique_pack.py --dossier <dir> [--ids ...]` FIRST, then invoke with args {dossierDir, ids, mode}.',
  phases: [
    { title: 'Critique', detail: 'analyst per item: rubric walk + simulated play' },
    { title: 'Verify', detail: 'Opus adversarial re-judge with web checks' },
  ],
}

// args: { dossierDir: string, ids: string[], mode: 'gate'|'sweep', repo?: string }
// gate  -> verdicts for PENDING items in apply_rereview.py vocabulary (promote|keep|reject)
// sweep -> PROPOSALS for approved items (keep|demote|revise); the owner decides (ADR-0019 precedent).
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const REPO = A.repo || '.'
const RUBRIC = `${REPO}/docs/CRITIQUE_RUBRIC.md`
const MODE = A.mode || 'gate'
const IDS = A.ids || []
const DOSSIERS = A.dossierDir
if (!['gate', 'sweep'].includes(MODE)) throw new Error('mode must be gate or sweep')
if (!Array.isArray(IDS) || IDS.some(id => typeof id !== 'string' || !id.length)) {
  throw new Error('ids must be a non-empty string array')
}
if (new Set(IDS).size !== IDS.length) throw new Error('ids must be unique')
if (!DOSSIERS || !IDS.length) throw new Error('args {dossierDir, ids} required — run scripts/critique_pack.py --dossier first')

const GAME_BY_PREFIX = { cx: 'conexiuni', ct: 'contexto', lt: 'lant', al: 'alchimie' }
const gameOf = id => GAME_BY_PREFIX[id.slice(0, 2)] || 'unknown'
const SECTION_BY_GAME = { conexiuni: 'B', contexto: 'C', lant: 'D', alchimie: 'E' }
const sectionOf = id => SECTION_BY_GAME[gameOf(id)]
if (IDS.some(id => gameOf(id) === 'unknown')) throw new Error('every id must have a known game prefix')
const VOCAB = MODE === 'gate' ? ['promote', 'keep', 'reject'] : ['keep', 'demote', 'revise']

const CRITIQUE_SCHEMA = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    review_binding: { type: 'string', description: 'copy the dossier review_binding exactly' },
    proposed: { type: 'string', enum: VOCAB },
    failure_modes: { type: 'array', items: { type: 'string' }, description: 'named rubric failure modes that apply (empty if clean)' },
    reasoning: { type: 'string', description: 'rubric walk + simulated player experience, <=250 words' },
    web_claims: { type: 'array', items: { type: 'string' }, description: 'recognition/relevance claims the verifier must check on the web' },
  },
  required: ['id', 'review_binding', 'proposed', 'failure_modes', 'reasoning', 'web_claims'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    review_binding: { type: 'string', description: 'copy the dossier review_binding exactly' },
    final: { type: 'string', enum: VOCAB },
    overturned: { type: 'boolean', description: 'true if the critique verdict was overturned' },
    web_checks: { type: 'array', items: { type: 'string' }, description: 'each rubric-D signal checked, with outcome' },
    evidence: { type: 'string', description: 'decisive evidence for the final verdict, <=150 words' },
  },
  required: ['id', 'review_binding', 'final', 'overturned', 'web_checks', 'evidence'],
}

const critiquePrompt = id => `You are a HARSH game-content critic for a Romanian word-game arcade. Judge pack item ${id} (game: ${gameOf(id)}).

Read, in this order:
1. ${RUBRIC} — the rubric. Sections A + ${sectionOf(id)} bind you.
2. ${DOSSIERS}/${id}.json — the item dossier: members with node types/salience/descriptions, lint findings, cross-group strong edges.

Then:
- Simulate an average Romanian player (not a specialist). For conexiuni: labels are HIDDEN during play — can the player partition the 16 tiles from the tiles alone, and does each solved group feel earned and consistent? For contexto: would the player ever converge on this target by free association, and does getting warmer feel legible?
- For lant, inspect every labeled representative path and judge whether each step is a nameable association. For alchimie, inspect productive_openings and minimum_action_recipe; structural craftability alone is not quality.
- Walk every rubric criterion; name each violated failure mode exactly (e.g. "B1 Predicate Inconsistency", "C1 Nameable-thing", "B5 mirrored groups", "A7 non-distinctive association" — check the dossier's nondistinctive_region_links block).
- Be hard: "technically valid but no Romanian would enjoy it" is a failing item. The bar is a prime-time-audience puzzle, not a graph exercise.
- ADR-0019 triggers (adult/profanity/alcohol/insensitive-humor/near-duplicate): ${MODE === 'gate' ? 'propose "keep" and say so — that boundary is the owner\'s.' : 'flag them in your reasoning but still return your honest QUALITY verdict — in sweep mode every verdict is already only an owner proposal; never soften to "keep" out of deference.'}
- Mode=${MODE}: propose one of ${JSON.stringify(VOCAB)}. ${MODE === 'gate' ? '"promote" only when the item is genuinely good; when in doubt, "keep" (stays pending).' : '"demote" = should leave the served pool; "revise" = good bones, one group/target swap fixes it; "keep" = genuinely fine.'}
- List every recognition/relevance claim you could not settle from the dossier alone as web_claims (e.g. "Bonțida is nationally known beyond Electric Castle context").
- Copy the dossier's review_binding field exactly into review_binding. It binds this judgment to the reviewed content and rubric.

Return ONLY the structured object.`

const verifyPrompt = (c, sampled) => `You are an adversarial Opus verifier with web access for Romanian game content. ${sampled ? 'This item was judged CLEAN — your job is to find what the critic missed.' : 'Your job is to OVERTURN this critique if it is wrong in either direction.'}

Item ${c.id} (game: ${gameOf(c.id)}), mode=${MODE}. Review binding: ${c.review_binding}. Critic proposed: ${c.proposed}. Failure modes: ${JSON.stringify(c.failure_modes)}. Reasoning: ${c.reasoning}

1. Read ${RUBRIC} (sections A, F, and ${sectionOf(c.id)}) and ${DOSSIERS}/${c.id}.json yourself — do not trust the critic's summary.
   For lant/alchimie, independently inspect the labeled representative paths or productive openings/minimum recipe; do not accept aggregate branch/closure counts as semantic evidence.
2. Refute-first: argue the OPPOSITE of the critic's verdict; keep whichever position survives the evidence.
3. Run rubric section F web checks (WebSearch/WebFetch) on every claim in ${JSON.stringify(c.web_claims)} and on any A1/A2/C2 doubt you have: ro.wikipedia presence, school-canon, national media (digi24/HotNews/ProTV/Libertatea/GSP), charts, sustained-vs-spike interest, cross-generational legibility. Record each check + outcome in web_checks.
4. Salience numbers under-rate some famous nodes — fame is settled by the web checks, never by salience alone.
5. ADR-0019 boundary: ${MODE === 'gate' ? 'a trigger forces final "keep" (stays pending), noted in evidence.' : 'note any trigger in evidence but return your honest QUALITY verdict — sweep verdicts are only owner proposals; deferring to "keep" hides the signal the owner needs.'}
6. Copy the dossier's review_binding exactly into review_binding; it must equal the value above.

Return ONLY the structured object with your FINAL verdict (${JSON.stringify(VOCAB)}).`

log(`critique-games: ${IDS.length} item(s), mode=${MODE}`)

const sampleBucket = id => [...id].reduce(
  (acc, ch) => ((acc * 31) + ch.charCodeAt(0)) >>> 0,
  0,
) % 4

const results = await pipeline(
  IDS,
  id => agent(critiquePrompt(id), {
    agentType: 'analyst', effort: 'high',
    phase: 'Critique', label: `critique:${id}`, schema: CRITIQUE_SCHEMA,
  }),
  (critique, id) => {
    if (!critique || critique.id !== id || !critique.review_binding) return null
    const clean = critique.proposed === (MODE === 'gate' ? 'promote' : 'keep') && critique.failure_modes.length === 0
    const sampledOut = MODE === 'sweep' && clean && sampleBucket(id) !== 0
    if (sampledOut) return { critique, verdict: null, verified: false, verifierLost: false, sampledOut: true }
    return agent(verifyPrompt(critique, clean), {
      agentType: 'general-purpose', model: 'opus', effort: 'high',
      phase: 'Verify', label: `verify:${critique.id}`, schema: VERDICT_SCHEMA,
    }).then(verdict => {
      const valid = !!verdict && verdict.id === id && verdict.review_binding === critique.review_binding
      return { critique, verdict: valid ? verdict : null, verified: valid, verifierLost: !valid, sampledOut: false }
    })
  },
)

const perItem = []
const verdicts = {}
let verified = 0, unverifiedClean = 0, lost = 0, verifiersLost = 0
for (let i = 0; i < IDS.length; i++) {
  const inputId = IDS[i]
  const r = results[i]
  if (!r || !r.critique) { lost++; continue }
  let final = r.verdict ? r.verdict.final : r.critique.proposed
  let evidence = r.verdict ? r.verdict.evidence : 'clean sweep critique, stable sample skipped'
  if (r.verifierLost) {
    verifiersLost++
    evidence = 'VERIFIER LOST — analyst-only judgment, do not trust as verified'
    // Gate integrity: promotion requires a live adversarial verifier.
    if (MODE === 'gate' && final === 'promote') final = 'keep'
  }
  verified += r.verified ? 1 : 0
  unverifiedClean += r.sampledOut ? 1 : 0
  const game = gameOf(inputId)
  ;(verdicts[game] = verdicts[game] || {})[inputId] = final
  perItem.push({
    id: inputId, game, proposed: r.critique.proposed, final,
    review_binding: r.critique.review_binding,
    verified: !!r.verified, verifier_lost: !!r.verifierLost,
    sampled_out: !!r.sampledOut,
    overturned: r.verdict ? r.verdict.overturned : false,
    failure_modes: r.critique.failure_modes,
    reasoning: r.critique.reasoning,
    web_checks: r.verdict ? r.verdict.web_checks : [],
    evidence,
  })
}
log(`coverage: ${verified} verified, ${unverifiedClean} clean sweep items sampled out, ${verifiersLost} verifier(s) lost, ${lost} lost critique agents`)
const coverage = { total: IDS.length, verified, unverifiedClean, verifiersLost, lost }
const batch = { version: 2, mode: MODE, input_ids: [...IDS].sort() }
const artifacts = {}
for (const game of new Set(IDS.map(gameOf))) {
  const requested = IDS.filter(id => gameOf(id) === game).length
  const items = perItem.filter(item => item.game === game)
  const gameVerdicts = verdicts[game] || {}
  const gameVerified = items.filter(item => item.verified).length
  const gameVerifierLost = items.filter(item => item.verifier_lost).length
  const gameSampledOut = items.filter(item => item.sampled_out).length
  artifacts[game] = {
    game, mode: MODE, batch, verdicts: gameVerdicts, perItem: items,
    coverage: {
      total: requested,
      verified: gameVerified,
      unverifiedClean: gameSampledOut,
      verifiersLost: gameVerifierLost,
      lost: requested - items.length,
    },
  }
}
return { mode: MODE, batch, verdicts, perItem, coverage, artifacts }
