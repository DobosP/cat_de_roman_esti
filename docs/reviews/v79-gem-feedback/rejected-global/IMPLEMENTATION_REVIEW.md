# V79 `gem` mapping — independent implementation and privacy review

Valid until: source `a93dc84a6443abd19e34b9fa75df8df04f344cb50ef80e305c2063c6ed06f423`, tests `804f8910ef4c8d09e0eb1e7f6609d3d37a87c6e2c32f5925029250a828ee2141`, or impact comparison `48a28d21516c75c4c9da4bb8d4382a11cc091461115e7816fb1a7b577d1b936e` changes — then treat as history.

Date: 2026-09-06

Verdict: **defer; do not land the candidate mapping**.

## Technical and privacy result

The code change itself is narrow and correctly implements the proposed table edit. It moves only the existing `gem` projection from the Miere override to a new one-surface Dulceață override. The surface/key, `ingrediente` domain, explicit mapping kind, rank penalty 1 and public synthetic ID remain exact. A canonical digest pins all other 472 projection rows.

The six focused route tests are meaningful and passed independently. They show:

- `Gem` becomes rank 8/Fierbinte for the fixed Clătite target.
- The response exposes only `ctxp_fab0f46e7bcd5932442e` and label `Gem`; it does not serialize `anchor_id`, the private Dulceață ID or label, or the hidden Clătite answer.
- When Dulceață is hidden, projected `gem` remains a nonwin at rank 2 or worse and below closeness 100; direct `dulceață` still wins at rank 1.
- A real `gemm` typo suggests Gem for a nonsecret target but suppresses both Gem and Dulceață when that projection anchor is the secret.
- Whitespace/case repeat handling remains free and survives resume.
- Miere and Unt remain KG words, Lanț rejects `gem` without mutation, and KG/pack/ranking/derived/mobile artifact bytes remain pinned.

Independent focused checks: 6 tests passed; scoped Ruff and `git diff --check` passed. No full suite was run.

## Blocking semantic impact

The factual review found Dulceață to be a closer lexical and culinary approximation than Miere. That local fact is insufficient for a shared Contexto feedback anchor because the anchor contributes its whole graph position for every target.

The bound all-approved-target sweep covers 207 approved targets, including all 203 eligible targets, and keeps all answers hidden. It confirms exactly one mapping change among 473 projection terms and exact KG/pack/ranking/derived hashes. Clătite improves from rank 1699/Înghețat to rank 8/Fierbinte.

It also finds 13 newly warm eligible gastronomy targets. Several results are plainly misleading:

- `Gem` becomes Cald for Grătarul de 1 Mai and Murături.
- `Gem` becomes Călduț for Ciorbă rădăuțeană, Fasole cu ciolan, Must și pastramă, Șaorma cu de toate, Mămăligă and Salată de boeuf.

Other newly warm cases include broad or weakly adjacent festival/preserve/dessert routes. The existence of a few reasonable changes, such as Papanași, does not rescue the savory false warmth.

This is a gameplay-semantics blocker rather than a privacy or mutation bug. The shared Dulceață anchor is technically correct but too broad in the current graph. The V78 Clătite defer should remain. A target-conditioned projection or graph redesign would expand the approved scope and needs a separate proposal and impact review.

## Bindings

- baseline: `010cfd176dcaa78aac660aea71e154691bd010f3`
- proposal: `sha256:58629365916673283e56c77edcd88afa7b75e63615e78863a909705865ef7fbd`
- candidate projection source: `sha256:a93dc84a6443abd19e34b9fa75df8df04f344cb50ef80e305c2063c6ed06f423`
- unchanged Contexto route source: `sha256:e248eed373c3a732f4316b52b2c9114942f3db29cf3594fcc8ec8ce99eed676d`
- V79 tests: `sha256:804f8910ef4c8d09e0eb1e7f6609d3d37a87c6e2c32f5925029250a828ee2141`
- KG: `sha256:c158262f7216c3b7ec2381f9fbe5ffc5d2ac987ad6a1d56de61e58ec276eb370`
- factual review: `sha256:b1ae2bc95892b296dff46a8a43367fbeafd2e1bb686a2633b14ec1d5119c79fd`
- impact baseline/candidate/comparison: `sha256:79ca578f1380264d8d6b82dad07c06bf24fdccbbbd5af6fb00354d3654150c0f`, `sha256:a312c8afeb8182d0f8cbdf8f7690d32bd804d41d480bfb4dfa42fb9d6e13fe3c`, `sha256:48a28d21516c75c4c9da4bb8d4382a11cc091461115e7816fb1a7b577d1b936e`

This is an independent Codex-agent review, not a human Romanian playtest. I made no repository edits.
