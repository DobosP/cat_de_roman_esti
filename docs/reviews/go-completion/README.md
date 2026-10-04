# Complete Go serving rollout proof

Valid until: deployed code/image/profile changes — then requalify.

Cât de român ești? codeabe933779f04c46a32ff0194b5111e68086ba93f landed and shipped
2026-10-04 after exact-head [CI37208742166](https://github.com/DobosP/cat_de_roman_esti/actions/runs/37208742166)
passed Go/nativeaccounts, Python3.12/3.14, frontend and selectedGo browser. Local622/622
browser cases passed, zero skips/retries/flaky; native/PostgreSQL combined lifecycle,
ownership/erasure races and1,207 independent anonymous HTTP parity responses pass.

The [candidate](candidate-smoke.json) and [public](public-smoke.json) each pass151 bounded
requests: all six games completed, exploration restore,28 assets/cache/HEAD, legal metadata,
current content identity and disabled accounts. These clients use offline Python content
answers; the server executes no Python/proxy/worker. Public URL:
https://cat-de-roman-esti.dobolabs.ro . Production account and proposal activation stay off.

Exact local scanned image73be231008d3067610f9e1cfe8fc24180845bfaae846b3903bc4d7c31ccac170
imports on the older VPS Docker engine as70361cff03367cd71ea2754c63fa080e70bcbc8a069d189c2946a03e48eff418.
All seven rootfs diffIDs and compiled ELF99cc4e9a57577d6aac70959055ff74df41367f721b5904eaf5a42064dc98d9c1
match; image metadata is normalized during import. Archive SHA82f512d2b28401739fb4ac8003f046c6191a6af493da87f0423dd2d5c5a68907
was verified before import. UID10001/read-only, healthy/zero restarts, no Python/pip;
PCRE2 is fixed10.42-1+deb12u2. [Image gate](image-security.json): fresh Trivy0.75,
zero fixable HIGH/CRITICAL findings. Source/package and symbol-retained audits also pass;
unimported module-level openpgp advisory remains disclosed in WORKLOG.

Only app was recreated; Caddy, certificates, DNS and volumes were preserved. Previous
Go image7663bff4c2e6 remains rollback-ca61b5d34236; the earlier Python rollback and its
matching Compose remain intact. Current previous Compose is preserved at
/root/_temp/cat-go-complete-abe9337/previous-compose.yml; rollback must use matchingimage/profile.
