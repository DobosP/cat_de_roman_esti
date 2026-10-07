# Core requests — S1

Record actual core friction and source evidence here; parent owns core patches.

REQ-1 | blocking no | none | core-v1.1 plain gen cannot nest canonical setup (locate-kit.mjs/frozenBootstrapConfig parents omit gen); the original repo:gen runs genuine npm-ci/build/binary prerequisites itself and retains named actions. Consider allowing setup under gen without changing current-invocation binding.
REQ-2 | blocking no | none | successful original gen sync-back emits hundreds of rsync "cannot delete non-empty directory" warnings for excluded source directories; actual .gate/gen/result.json passed and source porcelain stayed confined to authored hooks/tests. Preserve exclusions while making generating sync-back output concise.
REQ-3 | blocking yes | none | core-v1.1 consumer gen --resolve-versions cannot use shipped resolve-versions.sh: it launches literal web-kit/scripts/resolve-versions.mjs; the resolver processes only core-scope entries and edits root package.json plus web-kit/package.json. Cat has neither core layout. Provide configured consumer resolution and real app manifest mapping; no alias/fork or lock hand-edit. Original qualification/auxiliary locked baseline work can continue first.
REQ-4 | blocking no | none | current v11 AST rules ban native style attributes but do not enforce explicit length units in useCspSafeStyle CSSOM bags; require the supported stricter app/kit numeric-unit check route while retaining existing style bans. Source audit204 sites is lexical only, not native AST qualification.
