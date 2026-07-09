# CoupledMD — Deployment Checklist

Production target: `docker compose` (the committed `docker-compose.yml`).

> The dev host does **not** have Docker installed, so the fixes for B1–B3 were
> verified via `uvicorn` + the FastAPI test client, not inside a container.
> The in-container smoke tests below **must** be run on the deploy host before
> going live — they are the only way to confirm the B1/B2/B3 fixes hold in the
> actual image (paths resolve via env, state DBs are writable, tables exist).

---

## 0. Pre-deploy (on the dev/build host)

- [ ] All source changes committed.
- [ ] `data/systems_master.csv` has receptor genes backfilled (177 systems filled
      from UniProt). Confirm: only 2 systems lack a gene (Gq_7E9W, Gs_8HTI).
- [ ] `db/coupledmd.sqlite` regenerated from the corrected CSV via
      `python3 scripts/p1_ingest.py` (gene-null count = 2).

### Data payload — must be on the deploy host (NOT in a `git clone`)

The bind-mount (`${DATA_ROOT}:/data:ro`) serves files from the host filesystem,
so these must be copied/rsync'd to the cloud host separately — a fresh
`git clone` will **not** include them (they are gitignored or untracked):

| Path | Approx. size | In git? |
|------|------|---------|
| `db/coupledmd.sqlite` | small | gitignored |
| `data/api/` | small | gitignored |
| `data/viz/` | ~39 GB | untracked |
| `data/chain_roles/` (222 files) | ~1 MB | untracked |
| `data/contacts/` (221 parquet) | ~11 MB | untracked |

- [ ] All five present on the host. Confirm: `ls data/chain_roles | wc -l` → 222
      and `ls data/contacts | wc -l` → 221. Missing `chain_roles`/`contacts`
      silently breaks the Flareplot + 3D subunit coloring; a missing `viz/`
      breaks the trajectory viewer.

## 1. Build the frontend (on the deploy host, after the last source change)

`dist/` is gitignored and not baked into any image; nginx serves `./frontend/dist`.

```bash
cd frontend
npm ci
npm run build     # produces frontend/dist/
```

- [ ] `frontend/dist/index.html` and `frontend/dist/assets/*` exist.
- [ ] (Optional) `npm test` passes.

## 1b. TLS certificates (nginx serves `:443`)

nginx's `:443` server block hard-requires `fullchain.pem` + `privkey.pem` under
the mounted cert dir (`${SSL_CERT_DIR:-./certs}` → `/etc/nginx/ssl`). **nginx
will not start if they are missing.**

- For a quick test, the repo's `./certs/` already holds self-signed certs —
  `curl -k` (insecure) accepts them.
- For production on a real domain, replace them with Let's Encrypt
  `fullchain.pem` + `privkey.pem`, or point `SSL_CERT_DIR` at
  `/etc/letsencrypt/live/<domain>`.
- [ ] `ls certs/` shows `fullchain.pem` and `privkey.pem`.
- **Never commit `privkey.pem`** — keep `certs/` untracked/gitignored.

## 2. Start the stack

```bash
docker compose config >/dev/null && echo "compose OK"   # validate YAML + volume refs first
docker compose build
docker compose up -d
docker compose ps      # api healthy, nginx up
```

- [ ] `curl -k https://localhost/api/v1/health` → `{"status":"ok","n_systems":222,...}`

## 3. In-container smoke tests (the B1/B2/B3 verification)

These are the tests that pass on the dev host via `uvicorn` but can only be
trusted once they pass **inside the container**.

### B1 — Flareplot + 3D coloring data is reachable
- [ ] `curl -k "https://localhost/api/v1/systems/Gi_6CMO/subunit-ranges" | head -c 200`
      → JSON with `subunit_ranges` containing G_alpha/Receptor/G_beta/G_gamma
      (NOT a 404 / "No contact data").
- [ ] `curl -k "https://localhost/api/v1/systems/Gi_6CMO/contacts?min_freq=0.4" | head -c 200`
      → JSON with `n_contacts` > 0.
- [ ] Open a system detail page in the browser → the Flareplot ("Interaction
      Network") renders contacts, and the 3D viewer shows per-subunit coloring.

### B2 — API keys + accounts are writable
- [ ] `curl -k -X POST https://localhost/api/v1/keys/request -H 'Content-Type: application/json' -d '{}'`
      → 200 with an `api_key` (proves the writable `api-state` volume works).
- [ ] Register + login round-trip via the UI (or `curl -X POST .../accounts/register`).
- [ ] `docker compose exec api ls -la /data/state/` → `keys.db` and
      `accounts.db` exist and are writable.

### B3 — Fresh-deploy rate-limit middleware does not 500
- [ ] `curl -k "https://localhost/api/v1/health?api_key=cmd_notreal"` → 200
      (NOT 500). On a fresh deploy with no keys, the `api_keys` table is
      created eagerly at import time, so a bogus key is looked up without error.

## 4. Post-deploy sanity

- [ ] Systems list shows all 222 (not 200). Browse to `/systems`, the "All" pill
      count is 222 and the last page of systems is reachable.
- [ ] A system whose gene was backfilled (e.g. Gi_6G79) shows "HTR1B" in its
      detail header; Gq_7E9W shows no "(null)" and no broken UniProt link.
- [ ] `/api/docs` loads; the citation string says "DOI pending (pre-publication)".
- [ ] HTTPS redirect works; HSTS + security headers present
      (`curl -k -I https://localhost/ | grep -i strict`).

## 5. Rollback

- **CSV** (`data/systems_master.csv`) is git-tracked, so the pre-backfill version
  is recoverable: `git checkout HEAD -- data/systems_master.csv`.
- **DB** (`db/coupledmd.sqlite`) is gitignored (no snapshot); rebuild it from the
  restored CSV with `python3 scripts/p1_ingest.py`.
- To roll back a deploy: `docker compose down` and re-run the previous image.
