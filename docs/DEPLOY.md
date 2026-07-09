# Deploying cât-de-român-ești

Two shippable shapes:

| Mode | Flag | What it is | Compliance |
| --- | --- | --- | --- |
| **Anonymous arcade** | `CAT_ACCOUNTS_ENABLED=0` (default) | Stateless, no DB, progress in the browser | Minimal — no accounts/PII |
| **Accounts + Google login** | `CAT_ACCOUNTS_ENABLED=1` | Postgres + sessions + Sign-in-with-Google + saved progress | Full child-data stack (below) |

This document covers publishing the **accounts** stack on a single EU VPS (Hetzner), fronted
by Cloudflare, with TLS via Caddy. The anonymous arcade is a subset (skip Postgres/OAuth).

> **Go-live gate.** The accounts stack collects personal data from possibly-minor users. Do
> **not** point real users at it until the [Go-live compliance checklist](#go-live-compliance-checklist)
> is satisfied and the `docs/compliance/` drafts have been completed + lawyer-reviewed. Until
> then, run it on a staging host, or deploy the anonymous arcade first and flip the flag later.

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
2. Caddy will obtain a Let's Encrypt certificate automatically on first boot (uses `TLS_EMAIL`).

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
# Fill in: CAT_DOMAIN, TLS_EMAIL, CAT_SECRET_KEY (python -c "import secrets;print(secrets.token_urlsafe(64))"),
#          POSTGRES_PASSWORD, GOOGLE_OAUTH_CLIENT_ID/SECRET.
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml logs -f app   # watch migrations + boot
```

The `app` entrypoint runs `migrate` automatically. Verify:

```bash
curl -fsS https://<CAT_DOMAIN>/api/health        # {"ok": true, ...}
curl -fsS https://<CAT_DOMAIN>/api/me            # {"accounts_enabled": true, "authenticated": false, ...}
# open https://<CAT_DOMAIN> and click "Intră cu Google"
```

### Single-process constraint

Game sessions live in memory (`SessionStore`), so the app **must stay one process** (the
image runs a single uvicorn worker — keep it that way). If real load arrives, move session
state to Redis before scaling out.

## 5. Backups

- Postgres: `docker compose -f docker-compose.prod.yml exec db pg_dump -U cat cat > backup.sql`
  on a daily cron; ship the dump to an **EU** private, versioned bucket (separate creds).
- **Prove a restore** into a throwaway DB before you rely on it (fleet runbook requirement).
- `pgdata` + `submissions` are named volumes — include them in host-level backups too.

## 6. Updates

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Migrations run on boot. Roll back by checking out the previous tag and rebuilding.

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
- [ ] `manage.py check --deploy` clean; secure cookies, CSRF, rate-limit on `/accounts/*` and
      `/api/me/*` confirmed; no OAuth tokens logged.
- [ ] Backup taken **and a restore drill proven**.

Only after all boxes: set the `joc` DNS live, publish the Google OAuth consent screen, and
announce.
