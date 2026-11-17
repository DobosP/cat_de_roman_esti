# Deploying cât-de-român-ești

Two shippable shapes:

| Mode | Flag | What it is | Compliance |
| --- | --- | --- | --- |
| **Anonymous arcade** | `CAT_ACCOUNTS_ENABLED=0` (default) | No DB, progress in the browser, optional board counts | Accounts off |
| **Optional native accounts** | `CAT_ACCOUNTS_ENABLED=1` | PostgreSQL + password/Google/Facebook sessions + consent/private score copy | Full child-data stack (below) |

The selected production backend is Go ([ADR-0162](adr/0162-select-go-production-backend.md)).
The root Dockerfile and anonymous Compose profile serve all gameplay and site routes
without Python or a Rust process. Content authoring/validation and the Python reference
remain outside the runtime image. Native accounts/OAuth use the same Go image through
`docker-compose.prod.yml` or the optional `docker-compose.accounts.yml` override
([ADR-0163](adr/0163-complete-native-go-accounts.md)); those profiles are not activated publicly.
`Dockerfile.python-reference`, `docker-compose.python-reference.yml` and the Python
entrypoint are reference/rollback artifacts only.

**Product model.** The game is **always free to play without an account.** With current
consent, signing in can do two private things; Google name/email are never published. The
history boundary is recorded in
[ADR-0061](adr/0061-device-local-progress-and-upload-only-private-backup.md):

1. **Back up completed scores** — the frontend uploads retained finished-score rows to a
   private account copy. The browser remains the source of truth: there is no automatic
   download, restore, or merge, so this is not cross-device progress continuity.
2. **Don't get the same game again** — once you *finish* a curated puzzle (win or give up), the
   server stores its game key, opaque curated pack ID, and completion timestamp, then avoids
   offering it again (`PlayedPuzzle`; daily challenges are exempt). Mined/random boards and
   solutions are never persisted.

An account can also **appear on the public ranking** (`/clasament`) with a chosen nickname
(never Google name/email) and one selected game's server-verified record. Browser/imported
history never feeds public standings. Visibility requires current consent plus an explicit
`show_on_ranking` opt-in, which defaults to private. Money comes from **donations**: set
`CAT_DONATE_URL` and a "Donează" button shows in both modes (real provider/ONG page is an
owner task). An under-16 provider-linked native user/profile can exist, but a sticky parental hold
blocks score-copy, repeat, and verified-record writes plus ranking visibility. Letting minors
rank (pseudonymously, with verifiable parental consent) is a **new DPIA** — see
`docs/compliance/`.

> **Go-live gate.** The accounts stack collects personal data from possibly-minor users. Do
> **not** point real users at it until the [Go-live compliance checklist](#go-live-compliance-checklist)
> is satisfied and the `docs/compliance/` drafts have been completed + lawyer-reviewed. Until
> then, run it on a staging host, or deploy the
> [anonymous arcade (v1) launch](#anonymous-arcade-v1-launch) first and flip the flag later.

---

## Anonymous arcade (v1) launch

The v1 public launch ships **accounts OFF** (`CAT_ACCOUNTS_ENABLED=0`, the default): a
Go app container + Caddy TLS, without Postgres or Google OAuth. Player progress is stored
in the browser. Switch to the accounts stack only once its go-live checklist is done.

This "v1" names the first anonymous public launch; it is not the V1 (1.0.x) testing
release. For a same-Wi-Fi phone playtest served from the organizer's own computer (no
hosted server), see [TESTARE_V1](TESTARE_V1.md).

**1. Provision the server** — same as [section 1](#1-provision-the-server-hetzner) below
(Hetzner CX22, EU location, Docker + Compose plugin, clone the repo).

**2. DNS + TLS (Cloudflare)** — same quick start as [section 2](#2-dns--tls-cloudflare)
below: add an **A record** for your chosen host (e.g. `joc.<yourdomain>.ro`) pointed at the
server, **Proxy status: DNS only (grey cloud)**; Caddy 2.11 obtains its own Let's Encrypt
certificate automatically on first boot (uses `TLS_EMAIL`). Skip Google OAuth (section 3)
and Postgres entirely — this mode needs neither.

**3. Configure + launch:**

```bash
cd ~/cat_de_roman_esti
cp .env.anon.example .env.anon
# Fill in: CAT_DOMAIN, TLS_EMAIL and the public legal fields. Existing secret files stay private.
# Go does not require CAT_SECRET_KEY, a database or live fixture overrides.
docker compose -f docker-compose.anon.yml --env-file .env.anon up -d --build
docker compose -f docker-compose.anon.yml logs -f app   # watch boot (no migrations to run)
```

**4. Smoke test:**

```bash
curl -fsS https://<CAT_DOMAIN>/api/health        # concepts must equal /api/manifest counts.nodes
curl -fsS https://<CAT_DOMAIN>/healthz           # container-internal healthcheck endpoint
curl -fsS https://<CAT_DOMAIN>/api/me            # {"accounts_enabled": false, ...}
curl -fsS https://<CAT_DOMAIN>/api/categories    # 14 rows; curated + available + difficulty matrix
curl -fsS -X POST "https://<CAT_DOMAIN>/api/wordgames/intrusul/games?seed=38"
curl -fsS -X POST "https://<CAT_DOMAIN>/api/wordgames/perechi/games?seed=38"
```

`curated` is raw approved inventory, not a runtime-playability promise. Four easy Conexiuni
themes are intentionally false in `available_by_difficulty`; the picker hides them. If every
category shows `node_count: 0`, or every nested availability flag is false, the app loaded
a mismatched release. Go embeds the reviewed fixture/export; rebuild after approved
content changes. The anonymous Go profile does not forward `CAT_KG_FIXTURE` or live
RO-EDU variables, so a stale host variable cannot silently replace the graph.

`/api/health` does not instantiate the derived catalog. The two POST probes are mandatory:
both must return 200 after every deploy, or Intrusul/Perechi may be unavailable despite a
healthy container.

**Single-process constraint** still applies: game sessions live in memory
(`SessionStore`), so the app remains one Go process (see the
[note below](#single-process-constraint)). Multiple replicas require session affinity
or shared atomic session storage.

**The default anonymous app persists no player data on the server.** It has no `db`
service or submissions mount. `POST /api/submissions` returns 503, player progress stays
in the browser, and the board comparison is off. Caddy keeps its TLS and configuration
volumes.

**Anonymous go-live requirements** come from the [checklist below](#go-live-compliance-checklist).
Set `CAT_LEGAL_OPERATOR` and `CAT_LEGAL_CONTACT_EMAIL` in `.env.anon` to publish the
operator identity and contact on `/legal/privacy` and `/legal/terms`. The pages show draft
placeholders while either is empty. If you set `CAT_DONATE_URL`, point it at the real
donation provider with the receiving entity and tax treatment confirmed.

### Optional anonymous daily board comparison

Paul owns activation, deployment, and final privacy wording. See the wording draft in
[ADR-0234](adr/0234-anonymous-daily-board-place.md).

The `docker-compose.board-stats.yml` override sets `CAT_BOARD_STATS_DIR=/data/board-stats`
and mounts the named `board_stats` volume. The image prepares the mount point for UID
10001. The app root stays read-only and a directory lock permits one writer.

The app stores board keys, win-step histograms, and aggregate win, loss, and give-up counts.
Only reviewed daily boards for today or yesterday in Europe/Bucharest are eligible. A
finished daily win includes `place` once its board has at least 100 counted rounds. The
store batches atomic snapshots about every 30 seconds and flushes during graceful shutdown.
Shutdown reserves seven seconds for HTTP draining, then gives the final snapshot close
its own three-second budget, including when a request ignored cancellation. The stats
Compose override provides a 20-second stop grace. Flush errors and timeouts are logged;
a volume that cannot finish within the flush budget can lose its unflushed tail.
At startup it loads retained snapshots and reports corrupt files it skips. Retention covers
the newest recorded Bucharest date and its previous 13 calendar days. Clock reads alone
never expire recorded data, so an idle store can keep snapshots longer than 14 wall-clock
days. A reading over two days ahead of the last trusted clock reading withholds sampling
and placement and logs the anomaly once. Correcting the clock resumes sampling. A restart
with a verified current clock also permits sampling after a long shutdown. Snapshots
contain no guesses, IP addresses, session or browser identifiers, or account IDs. Include any backup of these
snapshots in the same retention window.

**Client address.** The app is reachable from Caddy on the Compose network and has no
published port. Caddy overwrites `X-Cat-Client-IP` with the address it resolves. The app
uses it only in memory to admit up to 20 finished rounds in ten minutes per IPv4 address
or IPv6 /64 prefix. IPv4-mapped IPv6 shares the IPv4 budget. An IPv6 /48 can hold at most
64 active buckets. At the 4,096-entry global bound, a new bucket replaces the least
recently active one. The limiter removes expired keys even while traffic is idle. With
DNS-only ingress, Caddy uses the address of the connected client.

Before counting is enabled, verify the Docker host's IPv6 ingress with an isolated echo
upstream behind the same Caddy and port-publishing configuration. Make requests from two
external IPv6 networks and compare the upstream `X-Cat-Client-IP` values with the clients'
public IPv6 addresses. Docker's userland proxy can collapse IPv6 connections to a gateway
address. If both clients arrive as that gateway, keep counting off, correct the Docker
IPv6 forwarding configuration, and repeat the check until each client address survives.

For Cloudflare-proxied ingress, configure Caddy’s global `servers` options before enabling
comparison. Set `trusted_proxies static` to Cloudflare’s current published IPv4 and IPv6
ranges, and set `client_ip_headers CF-Connecting-IP`. Keep those ranges current. Verify
with a test upstream that an actual proxied request carries the client address. Check
that direct requests with forged `CF-Connecting-IP` and `X-Cat-Client-IP` headers still
carry the socket address to the upstream. [Caddy server options](https://caddyserver.com/docs/caddyfile/options#trusted-proxies),
[Cloudflare IP ranges](https://www.cloudflare.com/ips/)

**Activation.** With the qualified app image already present and Caddy running the
reviewed ingress configuration, use the normal `GATE_SHA` and `GATE_TREE_SHA256` values for
that release. Include the override after the anonymous Compose file.

```bash
docker compose --env-file .env.anon -f docker-compose.anon.yml \
  -f docker-compose.board-stats.yml config --quiet
docker compose --env-file .env.anon -f docker-compose.anon.yml \
  -f docker-compose.board-stats.yml up -d --no-deps --no-build --pull never app
```

**Manual verification.** Use a separate test volume. With comparison off, finish a curated
daily board and check that the response omits `place`. For the enabled check, seed 100
fixture rounds for the exact release and today's curated board before starting the app.
Win that daily board. Verify `place.rounds` is 101 and the result displays the four tiers
and Romanian round-count wording. Reload the same session to confirm the count stays at
101. Check that wins on free boards omit `place`. Restart the app after a flush on the
same Bucharest date, start a new session for the same board, and confirm a win shows 102.
Check app logs for startup or snapshot errors with the override enabled.

**Deactivation.** Recreate `app` with the base profile and verify that a new daily win
omits `place`.

```bash
docker compose --env-file .env.anon -f docker-compose.anon.yml \
  up -d --no-deps --no-build --pull never app
```

The detached `board_stats` volume still contains its snapshots. Automatic pruning runs
when the store is open. For retirement, have Paul confirm the project's `board_stats`
volume and remove that volume separately from the app recreation.

---

## 0. Prerequisites (accounts you create)

- **Hetzner Cloud** account (recommended: **CX22**, 2 vCPU / 4 GB / 40 GB NVMe, location
  **Nuremberg/Falkenstein DE** or **Helsinki FI** — EU/EEA, GDPR DPA). ~€4–5/mo.
- **Cloudflare** account (you have this) with your Romanian domain's nameservers delegated
  to Cloudflare.
- **Google Cloud** account for the OAuth client (below).
- A server user with Docker + the Docker Compose plugin installed.

> Provider note: Hetzner is the price/performance/compliance sweet spot for a first small app.
> Contabo is marginally cheaper (more RAM/€) but weaker I/O and oversubscribed — not worth it
> for a latency-sensitive game. Stay on Hetzner.

---

## 1. Provision the server (Hetzner)

1. Create a CX22 in an EU location; add your SSH key; enable backups.
2. Harden: non-root sudo user, `ufw` allow 22/80/443 only, `fail2ban`, unattended-upgrades.
3. Install Docker Engine + Compose plugin.
4. Clone this repo (or copy an artifact) to `~/cat_de_roman_esti`.

## 2. DNS + TLS (Cloudflare)

Pick your host, e.g. `joc.<yourdomain>.ro`, and set it as `CAT_DOMAIN`.

**Quick start (works out of the box):**
1. Cloudflare → DNS → add an **A record** `joc` → your server's IPv4, **Proxy status: DNS only
   (grey cloud)**.
2. Caddy 2.11 will obtain a Let's Encrypt certificate automatically on first boot (uses
   `TLS_EMAIL`) and applies `CAT_MAX_REQUEST_BYTES` before proxying a body to the Go application.

**Production (recommended — keeps Cloudflare WAF/DDoS in front):**
1. Set the `joc` record to **Proxied (orange cloud)**; SSL/TLS mode **Full (strict)**.
2. Cloudflare → SSL/TLS → Origin Server → **Create Certificate** (Origin CA). Save the cert +
   key onto the server, mount them into the Caddy container, and switch the Caddyfile site to
   `tls /etc/caddy/origin.pem /etc/caddy/origin-key.pem` (see the note in `deploy/Caddyfile`).
3. Enable a WAF rate-limit rule for `/accounts/*` and `/api/me/*`.

## 3. Google OAuth client

1. Google Cloud Console → create/select a project (under the publishing identity).
2. **APIs & Services → OAuth consent screen**: External; app name, support email, logo;
   scopes `openid`, `email`, `profile` only; add your privacy-policy + ToS URLs
   (`https://<CAT_DOMAIN>/legal/privacy`, `/legal/terms`); publish (or keep in testing with
   test users while staging).
3. **Credentials → Create OAuth client ID → Web application**:
   - Authorized JavaScript origins: `https://<CAT_DOMAIN>`
   - Authorized redirect URIs: `https://<CAT_DOMAIN>/accounts/google/login/callback/`
4. Copy the **Client ID** + **Client secret** into `.env.prod`.

## 4. Configure + launch

```bash
cd ~/cat_de_roman_esti
cp .env.prod.example .env.prod
# Supply registered names via the fleet secret delivery path: CAT_DOMAIN, TLS_EMAIL,
# POSTGRES_PASSWORD and optional GOOGLE_OAUTH_CLIENT_ID/SECRET or FACEBOOK_OAUTH_CLIENT_ID/SECRET.
# Native opaque sessions do not require the legacy CAT_SECRET_KEY; never print secret values.
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml logs -f app   # watch migrations + boot
```

The optional native account `app` command runs `cat-server -migrate` before serving. Verify:

```bash
curl -fsS https://<CAT_DOMAIN>/api/health        # {"ok": true, ...}
curl -fsS https://<CAT_DOMAIN>/api/me            # {"accounts_enabled": true, "authenticated": false, ...}
# open https://<CAT_DOMAIN> and click "Intră cu Google"
```

### Single-process constraint

Game sessions live in memory (`SessionStore`), so the app **must stay one process** (the
Go image runs one server process). Add replicas only after session affinity or shared
transactional state is designed and verified.

## 5. Backups

- Postgres: `docker compose -f docker-compose.prod.yml exec db pg_dump -U cat cat > backup.sql`
  on a daily cron; ship the dump to an **EU** private, versioned bucket (separate creds).
- **Prove a restore** into a throwaway DB before you rely on it (fleet runbook requirement).
- `pgdata` + `submissions` are named volumes — include them in host-level backups too.

## 6. Updates

For the selected anonymous Go deployment, preserve the running image and Caddy volumes,
then build a named candidate while the old app serves. Verify the candidate through
its own temporary loopback port: HTML MIME/cache, manifest/categories, anonymous mode,
legal notices, all six create/resume/action paths and exploration restore. Inspect its
process and absence of Python executables/modules; `X-Cat-Runtime: go` is the public
operational identity. Recreate only `app` with `--no-deps`, then repeat public probes.
Keep the previous Compose file with its previous image tag for rollback; a Python
rollback image must not be launched with the new Go environment/command. Do not change
Caddy, its certificates, DNS, account flags or volumes during this app replacement.


Before either stack rebuilds `latest`, preserve the running app image under the recorded
known-good release. Docker may discard the prior untagged image after replacement:

```bash
cat_previous_good="SHORT_SHA_RECORDED_IN_STATUS"
cat_compose_file="docker-compose.prod.yml"  # use docker-compose.anon.yml for anonymous
cat_env_file=".env.prod"                    # use .env.anon for anonymous
cat_app_container="$(docker compose -f "$cat_compose_file" --env-file "$cat_env_file" ps -q app)"
cat_running_image="$(docker inspect --format '{{.Image}}' "$cat_app_container")"
docker image tag "$cat_running_image" "cat-de-roman-esti:rollback-$cat_previous_good"
```

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

The Go anonymous image runs no migrations. The optional native account profile applies explicit
Go migrations against PostgreSQL; activation still requires the go-live checklist.
Legacy Python staging is isolated in `docker-compose.python-reference.yml` for offline reference/rollback.
Roll back by checking out the recorded commit and either restoring
the preserved image tag or rebuilding that commit. Never use `down -v` or a Docker prune:
the Caddy TLS volumes and other apps on the shared host are outside this rollout's scope.

---

## Go-live compliance checklist

The accounts stack must not serve real users until these are done (see `docs/compliance/`):

- [ ] **Controller entity** decided (ONG/asociație or interim personal identity) and named in
      the privacy notice + ToS (`[[PLACEHOLDER]]` fields filled).
- [ ] **Privacy notice, ToS, cookie notice** completed, lawyer-reviewed, published at
      `/legal/privacy` + `/legal/terms` (replace the condensed built-in pages with the final
      text, or point them at the reviewed documents).
- [ ] **DPIA** (`docs/compliance/dpia-lite.md`) completed; decide if Art. 36 ANSPDCP prior
      consultation is needed.
- [ ] **ROPA** (Art. 30 record) completed.
- [ ] **Under-16 handling** confirmed: this build **blocks** under-16 self-service accounts
      (the RO age-16 rule). If you instead want a verifiable parental-consent flow, implement
      it per `docs/compliance/consent-and-age-gate-spec.md` before enabling child accounts.
- [ ] **DPAs (Art. 28)** signed/verified with Google, Hetzner, Cloudflare; account/progress
      data confirmed to stay in **EU/EEA**.
- [ ] **DSAR + deletion** verified on a demo account (the app exposes account deletion; also
      document the export/erasure request path + SLA).
- [ ] **72h breach** runbook + incident + DSAR registers in place; contact email published.
- [ ] **Public ranking and score copy** reviewed: only terminal server scores and chosen
      nicknames appear; the account copy is private, upload-only, and never restores
      local progress or feeds standings. Visibility defaults off and requires current
      consent; if under-16 players should rank, complete a new DPIA + parental-consent flow.
- [ ] **Donations**: `CAT_DONATE_URL` points at the real donation page (Stripe link /
      redirecționează.ro / ONG page); the receiving entity + tax treatment confirmed.
- [ ] Native account/combined HTTP PostgreSQL race gates and shared-auth race/vet pass
      with explicit disposable fixtures; configured HTTPS origin/callbacks, secure cookies,
      same-origin CSRF and database-backed auth attempt limits are verified. No OAuth tokens logged.
- [ ] Backup taken **and a restore drill proven**.

Only after all boxes: set the `joc` DNS live, publish the Google OAuth consent screen, and
announce.
