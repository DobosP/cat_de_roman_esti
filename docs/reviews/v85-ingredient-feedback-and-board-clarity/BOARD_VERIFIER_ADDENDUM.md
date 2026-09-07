# V85 final runtime binding and focused validation

Valid until: the final bound artifacts, runtime loader, reviewed label policy or test sources change — then treat as history.

**Accept the final trusted-digest update.** The exact proof and validation bindings are in
[board-verifier-addendum.json](board-verifier-addendum.json). This worker implemented the
original label policy; its separate independent code review remains
[board-verifier-review.json](board-verifier-review.json). This addendum independently checks
the root session's subsequent trusted-digest update, rather than claiming another independent
review of this worker's own original implementation.

The final runtime loader SHA-256 is
`7bfd51090554372bf72008f8029580665237d88712085cc8594f0f3e3d24bb34`.
Substituting only its `DEFAULT_DERIVED_CATALOG_SHA256` string with the previous value
reproduces the independently reviewed source SHA-256 exactly:
`9998c1906c457649952b6fdb43a50e36650abe679036228506f8eb2e0e088ac0`.
There is no other byte change. The policy, authoring tool, rollback helper and builder
all retain their independently reviewed hashes.

The trusted value matches the final generated catalog:
`66f4aebe9d64f638cfc8d48d51692b27a0f846d56e072a9a028a33b72d6e1ec7`.
Its package/test mirrors are byte-identical. The normal source bindings and closed
source/member/label checks remain intact.

## Final focused run

`PYTHONPATH=. ~/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v85_ingredient_graph.py tests/test_v85_board_label_corrections.py -q -o addopts=''`

**77 passed in 12.24 seconds**: 57 ingredient/public-journey cases and 20 board cases.
The scratch log and receipt hashes are recorded in the JSON addendum. Every new Contexto
round is selected through the real public endpoint and exercises three guesses, an earned
warmer clue, resume, a hot ingredient form, free repeat and an exact win. The public
Stafide→Brânză round completes both Pască and Poale-n brâu routes with intermediate resume.

Other coverage includes all 25 forms and Unicode variants, exact old input ownership,
all 45 new directed Lanț moves, both unchanged Mucenici↔Moldova directions with the repaired
explanation, source-only reverse rejection, and three actual ingredient-pair Alchimie
projections with earned explanations. These component recipes are not claimed as new
curated Alchimie rounds. Confident target typos retain the existing legitimate-win rule;
weaker advisory typos cannot disclose the answer. Audit metadata does not affect scoring.

Earlier local test assumptions about compact Lanț error responses and confident target
typos were corrected against the established contracts. An interim run passed all 51
then-existing ingredient cases while board reconstruction correctly refused a pack whose
five pending imports were not yet in the delta receipt. The final synchronized artifact
run above passes without weakening those guards. No production fix was needed for either.

All source/test edits in this lane stop at this green result. Full release integration
remains the root session's gate.
