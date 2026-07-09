# CoupledMD — Production Deployment Runbook

Documents the deployment of CoupledMD to its production host, captured so future
sessions can reproduce, troubleshoot, or extend it without re-deriving the steps.

- **Date deployed:** 2026-06-27
- **Host:** `jxhuang@43.111.228.160` (Alibaba Cloud ECS, **US region** — no ICP filing needed)
- **Project path on host:** `/home/jxhuang/gpcr_g_server`
- **Public URL:** `https://www.coupledmd.cn`
- **Domain DNS:** `www.coupledmd.cn` → A record → `43.111.228.160` (managed at Alibaba Cloud / hichina DNS)
- **Stack:** `docker compose` — `api` (FastAPI/uvicorn, built from repo) + `nginx` (nginx:1.27-alpine, TLS + reverse proxy)

---

## 0. What lives where

| Path (host) | Purpose | Comes from |
|-------------|---------|------------|
| `api/` (incl. `rate_limit.py`, `accounts.py`, `citation.py`) | API code — **untracked in git**, must be rsync'd | rsync (a `git clone` misses these) |
| `nginx/nginx.conf` | nginx config (mounted into container) | rsync |
| `CITATION.cff` | read by `api/citation.py` | rsync |
| `db/coupledmd.sqlite` | the database (gitignored) | rsync |
| `data/api/` (~1.6 GB, incl. `pocketgrid.npz` per system) | per-system analysis JSON + consensus + pocketgrids | rsync (run `scripts/p2_serialize.py --copy-grids` first — see §6) |
| `data/chain_roles/` (222 files) | subunit ranges / flareplot coloring | rsync |
| `data/contacts/` (221 parquets) | contact frequencies / 3D coloring | rsync |
| `data/systems_master.csv` | needed to rebuild the DB | rsync |
| `data/viz/{sid}/structure.pdb` (222) | viz topology for NGL | rsync |
| `data/viz/{sid}/traj.xtc` (222) | viz trajectory for NGL (~34 GB total) | rsync (can be deferred — site works without, viewer 404s per missing system) |
| `frontend/dist/` | built SPA (gitignored) | build on dev host with `npm run build`, then rsync |
| `certs/` | self-signed dev certs (fallback only) | rsync (optional) |

**Do NOT transfer:** `.git/`, `frontend/node_modules/`, `__pycache__/`, `*.pyc`,
`manuscript_figures/`, `scripts/audit_output/` (~2.8 GB), `data/viz/*/{1_whole,2_nojump,3_center,traj_fixed}.xtc`,
`data/viz/*/processed.gro`, `data/viz/*/.traj.xtc_offsets.*`, `data/viz/*/*.broken_pbc*` (~7.5 GB of PBC-fix leftovers),
`.env`, `coupledmd.pem` (private key), `data/{keys,accounts,gpcr_g}.db` (local dev state).

---

## 1. Install Docker on the host (was not present)

Ubuntu 26.04, x86_64, clean (no prior docker). Installed via the official convenience script:

```bash
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sudo sh /tmp/get-docker.sh
sudo usermod -aG docker jxhuang   # takes effect on next login; use sudo until then
```

Result: Docker Engine 29.6.1 + Compose v5.2.0.

### ⚠️ Storage driver fix (important)

The convenience script defaulted to the **`overlayfs` snapshotter**
(`io.containerd.snapshotter.v1`), which on this host caused container start to
fail with `mkdirat .../data/state: read-only file system`. Switch to classic
`overlay2`:

```bash
sudo mkdir -p /etc/docker
echo '{ "storage-driver": "overlay2" }' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
docker info | grep "Storage Driver"   # must say overlay2
```

Switching the storage driver wipes existing images — rebuild after this (§3).

---

## 2. The `docker-compose.yml` `/state` fix (committed to repo)

The original compose mounted the writable state volume at `/data/state`, **inside**
the read-only bind mount `${DATA_ROOT}:/data:ro`. Docker cannot create a named-volume
mountpoint inside a read-only bind, so container start fails:
`mkdirat .../data/state: read-only file system`.

Fix: mount the state volume at `/state` (outside `/data:ro`) and point the env
vars there. `api/rate_limit.py` and `api/accounts.py` read `KEYS_DB_PATH` /
`ACCOUNTS_DB_PATH` from env, so no code change is needed.

```yaml
api:
  environment:
    - KEYS_DB_PATH=/state/keys.db          # was /data/state/keys.db
    - ACCOUNTS_DB_PATH=/state/accounts.db  # was /data/state/accounts.db
  volumes:
    - ${DATA_ROOT:-.}:/data:ro
    - api-state:/state                     # was /data/state
```

**This fix is committed** (commit `2cd6ada` on `overnight/manuscript-20260619`,
"Fix deploy: mount api-state volume at /state, not /data/state"). A fresh
`git clone` of the repo includes it. The remote `docker-compose.yml` matches.

---

## 3. Runtime `.env` on the host

`/home/jxhuang/gpcr_g_server/.env` (created on host — do NOT copy the dev `.env`,
which has the dev `DATA_ROOT` path):

```env
# DATA_ROOT intentionally unset → docker-compose.yml defaults it to "." (project dir)
HTTP_PORT=80
HTTPS_PORT=443
SSL_CERT_DIR=/etc/letsencrypt/live/www.coupledmd.cn
CORS_ORIGINS=
```

`DATA_ROOT` unset → compose bind-mounts `./` → `/data:ro`, which is correct.
`DATABASE_URL` is hardcoded in compose to `sqlite:////data/db/coupledmd.sqlite`.

---

## 4. TLS: Let's Encrypt cert for www.coupledmd.cn

### Prerequisites (all required before issuing)
1. **Domain DNS resolving** to the host IP (verified via `getent hosts www.coupledmd.cn`).
2. **Security group open** for inbound TCP 80 **and** 443, source `0.0.0.0/0`
   (Alibaba Cloud console → ECS instance → Security Groups → Inbound rules).
   Without 80, the HTTP-01 challenge fails; without 443, the site is unreachable.
3. **No ICP filing needed** — host is in a US region. (A mainland-China region
   would require ICP 备案 and would block 80/443 until granted.)

### nginx ACME challenge patch (`nginx/nginx.conf`)
The default port-80 block redirects **everything** to HTTPS, which breaks the
HTTP-01 challenge (Let's Encrypt does not follow redirects to HTTPS). Patch the
port-80 server to serve `.well-known/acme-challenge/` over plain HTTP:

```nginx
server {
    listen 80;
    server_name _;

    location ^~ /.well-known/acme-challenge/ {
        root /usr/share/nginx/html;          # = ./frontend/dist on host
        default_type "text/plain";
    }
    location / {
        return 301 https://$host$request_uri;
    }
}
```

The webroot for certbot is `/home/jxhuang/gpcr_g_server/frontend/dist` (mapped to
`/usr/share/nginx/html` in the container).

### Issue the cert
```bash
sudo apt-get install -y certbot
sudo certbot certonly --webroot \
  -w /home/jxhuang/gpcr_g_server/frontend/dist \
  -d www.coupledmd.cn \
  --non-interactive --agree-tos --email jxhuang@sjtu.edu.cn
# → /etc/letsencrypt/live/www.coupledmd.cn/{fullchain,privkey}.pem
```

### Make nginx use the cert
The Let's Encrypt `live/*/fullchain.pem` files are **symlinks** to
`../../archive/...`. Mounting only the `live/` dir breaks them inside the
container (broken symlinks → `cannot load certificate`). Mount the **whole**
`/etc/letsencrypt` tree so symlinks resolve:

```yaml
nginx:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./frontend/dist:/usr/share/nginx/html:ro
    - ${SSL_CERT_DIR:-./certs}:/etc/nginx/ssl:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro          # added for LE symlinks
```

And in `nginx.conf` point directly at the LE paths:
```nginx
ssl_certificate     /etc/letsencrypt/live/www.coupledmd.cn/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/www.coupledmd.cn/privkey.pem;
```

Make the letsencrypt dirs readable by the container bind:
```bash
sudo chmod -R a+rX /etc/letsencrypt/live /etc/letsencrypt/archive
```

### Auto-renewal (already set up)
- `certbot.timer` is enabled + active (runs renewal checks periodically).
- Deploy hook at `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh` reloads
  nginx in the container after a successful renewal:
  ```sh
  #!/bin/sh
  cd /home/jxhuang/gpcr_g_server || exit 0
  /usr/bin/docker compose exec -T nginx nginx -s reload 2>/dev/null || \
  /usr/bin/docker exec gpcr_g_server-nginx-1 nginx -s reload 2>/dev/null || true
  ```
- Cert valid Jun 27 → Sep 25 2026; certbot renews automatically at ~60 days.
- **Note:** `certbot renew --dry-run` was flaky during setup (stale lock kept
  regenerating, possibly the systemd timer firing mid-test). The real renewal
  uses the same HTTP-01 path that succeeded at issuance, so it should work.
  To check later: `sudo certbot certificates`.

---

## 5. Build & start the stack

From the dev host, build the frontend and rsync `dist/`:
```bash
cd frontend && npm ci && npm run build      # produces frontend/dist/
rsync -av --delete frontend/dist/ jxhuang@43.111.228.160:/home/jxhuang/gpcr_g_server/frontend/dist/
```

On the host:
```bash
cd /home/jxhuang/gpcr_g_server
docker compose config >/dev/null && echo "compose OK"
docker compose up -d --build
docker compose ps      # api: healthy, nginx: up
```

### ⚠️ nginx.conf edits require container recreate, not just reload
`nginx/nginx.conf` is bind-mounted as a **single file**. Editing it on the host
(e.g. via rsync) creates a **new inode**; the container keeps the old inode and
`nginx -s reload` reloads the stale config. After any nginx.conf change:
```bash
docker compose up -d --force-recreate nginx
```
This is the inode-stale-bind-mount gotcha — it bit us during cert setup (new
ACME location wasn't visible until force-recreate).

---

## 6. Data prep on the dev host before transfer (the pocketgrid fix)

The `pocketgrid_npz` rows in the DB originally pointed **outside the repo**
(`/MDdata/.../a/paper1_pockets/atlas/{sid}_pocketgrid.npz`), which would 503 on
the deploy host. Fix: copy grids locally so the API's local-first resolution
serves them, and the DB rows point into the repo:

```bash
# on dev host, before rsync:
python3 scripts/p2_serialize.py --copy-grids
# → copies 219 npz into data/api/v1/systems/{sid}/pocketgrid.npz (~1.6 GB)
# → re-registers the DB rows to the local repo paths
# → also re-serializes all consensus + per-system JSON (safe; does NOT touch the
#   `systems` table, so gene backfills are preserved)
```

Verify after: `python3 -c "import sqlite3;c=sqlite3.connect('db/coupledmd.sqlite');print([r[0] for r in c.execute('SELECT DISTINCT file_path FROM system_pocket_files WHERE file_type=\"pocketgrid_npz\"')][:1])"`
— paths should be `.../gpcr_g_server/data/api/v1/systems/...`, not `.../a/paper1_pockets/...`.

3 systems (`Gq_7RAN`, `Gq_7RYC`, `Gq_8J9N`) have no pocketgrid in source — they
correctly 404; that's expected, not a bug.

---

## 7. Transfer (one rsync from project root, defer trajs)

Everything needed (untracked code, data, db, dist, certs) lives under the repo
tree, so one tree-wide rsync grabs it all — just exclude the heavy/irrelevant:

```bash
SRC=/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server
DST=jxhuang@43.111.228.160:/home/jxhuang/gpcr_g_server

# Bundle 1 — everything except trajs (≈7 GB, ~3300 files):
rsync -av --info=progress2 \
  --exclude='.git/' --exclude='frontend/node_modules/' \
  --exclude='__pycache__/' --exclude='*.pyc' --exclude='*.pyo' \
  --exclude='.claude/' --exclude='.pytest_cache/' --exclude='.vscode/' --exclude='.codeartsdoer/' \
  --exclude='.env' --exclude='coupledmd.pem' \
  --exclude='manuscript_figures/' --exclude='scripts/audit_output/' \
  --exclude='data/viz/*/1_whole.xtc' --exclude='data/viz/*/2_nojump.xtc' \
  --exclude='data/viz/*/3_center.xtc' --exclude='data/viz/*/traj_fixed.xtc' \
  --exclude='data/viz/*/processed.gro' --exclude='data/viz/*/.traj.xtc_offsets.*' \
  --exclude='data/viz/*/*.broken_pbc*' \
  --exclude='data/viz/*/traj.xtc' \
  --exclude='data/keys.db' --exclude='data/accounts.db' --exclude='data/gpcr_g.db' \
  $SRC/ $DST/

# Bundle 2 — trajectories (later; XTCs are already compressed, so plain tar is fine):
rsync -av --info=progress2 --include='*/' --include='traj.xtc' --exclude='*' \
  $SRC/data/viz/ $DST/data/viz/
```

Notes:
- `.env` is excluded on purpose — the dev `.env` has the dev `DATA_ROOT`; ship
  the minimal one in §3 instead.
- Trajs are deferred because they're ~34 GB; the site works without them (the
  viewer returns 503 per missing system until that system's `traj.xtc` lands).

---

## 8. Post-deploy smoke tests (all should pass)

```bash
# from any external machine (NOT the dev host if it has a local proxy on :7890)
curl -s https://www.coupledmd.cn/api/v1/health          # {"status":"ok","n_systems":222,...}
curl -s "https://www.coupledmd.cn/api/v1/systems?limit=1" | python3 -c "import sys,json;print(json.load(sys.stdin)['total'])"  # 222
curl -s -o /dev/null -w "%{http_code}\n" https://www.coupledmd.cn/api/v1/systems/Gi_6CMO/contacts?min_freq=0.4   # 200
curl -s -o /dev/null -w "%{http_code}\n" "https://www.coupledmd.cn/api/v1/systems/Gi_6CMO/pocketgrid"            # 200, 6.16 MB
curl -s -o /dev/null -w "%{http_code}\n" https://www.coupledmd.cn/api/v1/systems/Gi_6CMO/viz/structure           # 200
curl -s -X POST https://www.coupledmd.cn/api/v1/keys/request -H 'Content-Type: application/json' -d '{}'         # 200 + api_key
# cert is real (no -k needed):
curl -s https://www.coupledmd.cn/api/v1/health   # should NOT throw cert error
```

External reachability gotcha: the dev host routes through a local proxy on
`127.0.0.1:7890`, so curl from there returns misleading 502/000. Test with
`curl --noproxy '*'` or from the server itself / a clean vantage.

---

## 9. Operations cheat sheet (on the host)

```bash
cd /home/jxhuang/gpcr_g_server

docker compose ps                          # status
docker compose logs --tail=50 api          # API logs
docker logs --tail=50 gpcr_g_server-nginx-1  # nginx access/error logs
docker compose restart api                 # restart API only
docker compose up -d --force-recreate nginx  # after nginx.conf change (inode gotcha)
docker compose down                        # stop stack
docker compose up -d --build               # rebuild + start (after api/ code change)

sudo certbot certificates                  # check cert expiry / renewal status
sudo certbot renew --dry-run               # test renewal (see caveat in §4)
```

State DBs (API keys + optional accounts) live in the `api-state` named volume
(`/state/keys.db`, `/state/accounts.db`) — they persist across container
recreations but are per-host, not in git.

---

## 10. Known follow-ups / debt

- **Repo divergence (IMPORTANT):** the remote `nginx/nginx.conf` and
  `docker-compose.yml` have production-only changes (ACME challenge location,
  `/etc/letsencrypt` mount, LE cert paths, OCSP) that are **not** in the git
  repo. A fresh `git clone` deploy would NOT reproduce the cert setup. To make
  the repo deployable as-is, these should be parameterized (e.g. cert paths via
  env so it works with both self-signed dev certs and LE prod) and committed.
- **Trajectory transfer:** 221 of 222 `traj.xtc` still to transfer (Bundle 2 in §7).
  The viewer 503s per missing system until landed; no restart needed (API reads from disk).
- **OCSP stapling:** `ssl_stapling on;` is set but nginx warns "no OCSP responder
  URL in the certificate" — harmless, but could be disabled to keep logs clean.
- **`certbot renew --dry-run`** never completed cleanly during setup (stale lock).
  Real renewal should work, but verify with `sudo certbot certificates` closer to
  the 60-day mark.
- **5-year URL maintenance + DOI deposition** are commitments made in the NAR
  pre-submission inquiry. The 4.7 TB Zenodo trajectory deposition is a hard
  requirement by the NAR full-submission deadline (Aug 15), not just at acceptance.
