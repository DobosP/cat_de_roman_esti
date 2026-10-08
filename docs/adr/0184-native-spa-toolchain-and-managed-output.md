# ADR-0184: Native SPA tooling and managed-output prerequisites

Date: 2026-10-08
Status: accepted; actual normalized validation pending
Supersedes: ADR-0020 tooling/lint and generated-output clauses; bounded session/input and120KiB acceptance remain.

## Context

The owner's real core-v1.2 firstSYNC/trust at5baf581ce753c5f009ff19604e830fa2926492a8 reached npm-ci andfailed ERESOLVE: typescript-eslint8.63.0 requires TypeScript<6.1, but the actualselectedcompiler is7.0.2. Result6b70c7637038754074da145a4915e54457ba0290700201d20cc4d4873e31a0fa ispreserved; noGREENunit orformalKIT_BUMP wasissued. Original45ed900/900, Node2 and16/78 proof plusoriginal30freeze742bb111 arealready real andpreserved.

## Decision

Use selectedNode26.10.0/npm12.2.0/TypeScript7.0.2/Vite8.3.3 andGo1.27.1. Remove the incompatibleESLint/typescript-eslint/plugin stack. ActualOxlint1.87.0/oxlint-tsgolint7.0.2003 andast-grep0.45.3 replace it with explicitengine-supported equivalents for priorhooks/compiler/refresh rules; installedengine probing precedesclaims. Both native andimmutable SDK AST checks aremandatory; no broadsource/CSP/SafeURL/nativeJSX/import exemption isadded.

Motion14 isdirect; Framer14 isonlytransitive. React19 andexactoldUI0.3 remainruntime throughM1 under staged-reactuntilS1-M2. PendingUI1.0.2 isnotactive. Originalpackage/lock/SDK/runtime snapshots andallsealedassertions remainunchanged; normalizedreplay hasgenuinecurrentversion/source admission andseparateoutputs.

Probe actualinstalledTS7 CLI/package/JSAPI first. The corelock alreadyallows optional@typescript/typescript6 exactly6.0.2 forrequiredAST/transpilation, with explicitseparatebindings. NativeTypeScript7 remainsauthoritative forconsumer/noEmit/declaration diagnostics. No corecompiler downgrade, force/legacy-peer install ornewexception isintroduced.

Under PROGRAM E1, futurebuilds usefrontend/dist andmanagedGoembedfs. The existingtrackedweb/static30 remainsfrozen at originalGitbytes untilreviewedsource retirement; preserveoriginalcopies/legacyarchive. ManagedoutDir/source retirement isseparate fromthe presentdependencyrepair. PROGRAM E3 retainsreal40960/30720 observations andformalM0/M1 qualification limits; device/M2 activation isnotinferred.

## Validation and consequences

Onlytrusteddeps/genresolve writeslocks. The nextrealdeps generatesfrontendlock, performsactualnpm-ci andprobes compiler/linter/rules/config/WKinstallation. Currentlint/class/replay source isunexecuted. Exactstyles/conditionalarms/animations/focus andall900identities musthold; authcore andnative1207 privacybodyparity stayindependent. Parent owns finalprotectedsourceconfig/stage/sync/trust andactualsamefinalSYNC GREENunit beforeformalKIT_BUMP. Worker commits locallyonly; canonicalunit/full/image/device/activeUI acceptance remainsunearned.
