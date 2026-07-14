"""
CoupledMD API — FastAPI application.

All host-specific values (port, DATA_ROOT, DATABASE_URL, API_BASE_URL) come
from environment variables so the same image runs on localhost and the
university host with no code changes.

Open-access rule: No login, registration, account, or email is ever
required to reach any page, dataset, download, CSV, or API endpoint.
The only access-limiting mechanism is per-IP rate limiting.

Endpoints:
    GET /api/v1/systems                  list with filters
    GET /api/v1/systems/{sid}            full metadata record
    GET /api/v1/systems/{sid}/pockets    GPCRdb-mapped pocket data
    GET /api/v1/systems/{sid}/gateways   gateway metrics
    GET /api/v1/families                 family summary with counts
    GET /api/v1/consensus/...            consensus analysis products
    GET /api/v1/citation                 citation and licence info
    POST /api/v1/keys/request            request a Tier-1 API key (optional)
    POST /api/v1/accounts/register       optional account registration
    POST /api/v1/accounts/login          optional account login
    POST /api/v1/accounts/delete         self-service account deletion
    POST /api/v1/accounts/export         data export (GDPR/PIPL)
"""

import json
import os
import re
import csv
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .db import get_connection
from .rate_limit import RateLimitMiddleware, issue_key, delete_key, TIER1_LIMIT
from .accounts import (
    create_account, verify_account, get_account, delete_account,
    export_account_data, init_db as init_accounts_db,
)
from .citation import get_citation_block, CITATION_CFF

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = Path(os.environ.get("DATA_ROOT", _PROJECT_ROOT))
API_V1 = DATA_ROOT / "data" / "api" / "v1"
VIZ_DIR = DATA_ROOT / "data" / "viz"
# Corrected chain roles (subunit resid ranges) and residue-residue contact
# parquets — both ship under data/ so the read-only bind-mount serves them.
CHAIN_ROLES_DIR = DATA_ROOT / "data" / "chain_roles"
CONTACTS_DIR = DATA_ROOT / "data" / "contacts"
FRONTEND_DIST = _PROJECT_ROOT / "frontend" / "dist"
FINAL_RELEASE_COHORT = DATA_ROOT / "data" / "release_cohort_v9_final208.csv"


def _load_final_release_cohort() -> dict[str, dict[str, str]]:
    """Load the final public paper cohort without altering the master inventory."""
    if not FINAL_RELEASE_COHORT.is_file():
        raise RuntimeError(f"Final release cohort file missing: {FINAL_RELEASE_COHORT}")
    with FINAL_RELEASE_COHORT.open(newline="") as handle:
        rows = {row["system_id"]: row for row in csv.DictReader(handle)}
    if len(rows) != 208:
        raise RuntimeError("Final release cohort must contain 208 unique systems")
    return rows


FINAL_RELEASE_COHORT_ROWS = _load_final_release_cohort()
FINAL_RELEASE_IDS = tuple(FINAL_RELEASE_COHORT_ROWS)
FINAL_RELEASE_CLASS = {
    sid: row["gpcr_class"].strip().upper() for sid, row in FINAL_RELEASE_COHORT_ROWS.items()
}
FINAL_RELEASE_SQL = ",".join("?" * len(FINAL_RELEASE_IDS))

# System IDs follow the pattern "Gx_PDBID" (e.g. Gi_6CMO, G12_7T6B).
# Enforce this format to prevent path-traversal attacks in file-serving endpoints.
_SYSTEM_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _validate_system_id(sid: str) -> str:
    if not _SYSTEM_ID_RE.match(sid):
        raise HTTPException(status_code=400, detail=f"Invalid system_id: '{sid}'")
    if sid not in FINAL_RELEASE_IDS:
        raise HTTPException(status_code=404, detail=f"System not in the final public release: '{sid}'")
    return sid


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Ensure the accounts table exists at startup (keys table is created at
    # import time in rate_limit.py so the middleware can't hit a missing table).
    init_accounts_db()
    yield


app = FastAPI(
    title="CoupledMD",
    description=(
        "GPCR-G-protein MD web resource — 208 validated active-state ternary complex simulations.\n\n"
        "**Open access**: No login required. All data, downloads, and API endpoints are "
        "freely accessible. Optional API keys provide higher rate limits only.\n\n"
        "**Citation**: Huang J et al., CoupledMD: a web resource for GPCR–G-protein molecular dynamics. Citation details to be confirmed (pre-publication).\n\n"
        "**Licence**: Data CC-BY-4.0, Code MIT."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=_lifespan,
)

# Rate limiting middleware (applied to /api/ routes only)
app.add_middleware(RateLimitMiddleware)

# CORS: open for GET/POST so others can build on the API
_cors_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

# NOTE: frontend static files are mounted AFTER all API routes at the bottom
# of this file. Mounting here (before route definitions) would cause the
# catch-all to intercept all API paths.


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _row_to_dict(row) -> dict:
    data = dict(row)
    # The frozen final-release cohort defines sampling uniformly.  The master
    # table retains historical pre-repair values for a few systems.
    if "system_id" in data and data["system_id"] in FINAL_RELEASE_IDS:
        data["gpcr_class"] = FINAL_RELEASE_CLASS[data["system_id"]]
        if "n_replicas" in data:
            data["n_replicas"] = 3
        if "length_per_replica_ns" in data:
            data["length_per_replica_ns"] = 500
        if "total_sampling_ns" in data:
            data["total_sampling_ns"] = 1500.0
    return data


def _load_json(path: Path) -> dict | list:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Analysis file not found: {path.name}")
    with open(path) as f:
        return json.load(f)


def _system_json_path(sid: str, filename: str) -> Path:
    return API_V1 / "systems" / sid / filename


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #

@app.get("/api/v1/health")
def health():
    con = get_connection()
    cur = con.cursor()
    cur.execute(f"SELECT count(*) FROM systems WHERE system_id IN ({FINAL_RELEASE_SQL})", FINAL_RELEASE_IDS)
    n = cur.fetchone()[0]
    con.close()
    return {"status": "ok", "n_systems": n, "schema_version": "1.0"}


# --------------------------------------------------------------------------- #
# Citation & licence
# --------------------------------------------------------------------------- #

@app.get("/api/v1/citation")
def citation_info():
    """Citation, licence, and DOI information."""
    return get_citation_block()


@app.get("/api/v1/citation.cff", response_class=PlainTextResponse)
def citation_cff():
    """CITATION.cff file for software citation."""
    return CITATION_CFF


# --------------------------------------------------------------------------- #
# API key request (Tier-1 — optional, instant, no email required)
# --------------------------------------------------------------------------- #

class KeyRequestBody(BaseModel):
    email: str = ""
    institution: str = ""
    name: str = ""


@app.post("/api/v1/keys/request")
def request_api_key(body: KeyRequestBody):
    """
    Request a free Tier-1 API key for higher rate limits (600 req/min vs 60).

    Email, institution, and name are ALL optional. A working key is issued
    even if all fields are left blank. The key only raises the rate limit;
    it unlocks no data that anonymous users cannot already get.

    Sent as a POST body (not query params) so nothing is logged in URLs.
    """
    key = issue_key(email=body.email or "", institution=body.institution or "", name=body.name or "")
    return {
        "api_key": key,
        "tier": 1,
        "rate_limit": TIER1_LIMIT,
        "usage": "Pass as ?api_key=... query parameter or X-API-Key header.",
        "notice": "This key only raises your rate limit. All data is accessible without it.",
    }


# --------------------------------------------------------------------------- #
# Optional accounts (convenience only)
# --------------------------------------------------------------------------- #

class RegisterBody(BaseModel):
    email: str
    password: str
    name: str = ""
    institution: str = ""
    research_area: str = ""
    notify_updates: bool = False


class CredentialsBody(BaseModel):
    email: str
    password: str


@app.post("/api/v1/accounts/register")
def register_account(body: RegisterBody):
    """
    Register an optional account. Benefits: saved sessions, Tier-1 API key,
    update notifications. No data or download is ever account-gated.

    Credentials are sent in the POST body, never the URL.
    """
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    try:
        account = create_account(
            email=body.email, password=body.password, name=body.name or "",
            institution=body.institution or "", research_area=body.research_area or "",
            notify_updates=body.notify_updates,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"account": account, "notice": "Account is optional. All data remains accessible without login."}


@app.post("/api/v1/accounts/login")
def login_account(body: CredentialsBody):
    """Log in to an optional account. Returns account info and API key."""
    account = verify_account(body.email, body.password)
    if account is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"account": account}


@app.post("/api/v1/accounts/export")
def export_account(body: CredentialsBody):
    """Export all stored data for your account (GDPR/PIPL data portability)."""
    account = verify_account(body.email, body.password)
    if account is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    data = export_account_data(body.email)
    return data


@app.post("/api/v1/accounts/delete")
def delete_account_endpoint(body: CredentialsBody):
    """Self-service account deletion. Removes all stored data and API key."""
    account = verify_account(body.email, body.password)
    if account is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    delete_account(body.email)
    return {"deleted": True, "notice": "Account and all associated data have been removed."}


# --------------------------------------------------------------------------- #
# Families
# --------------------------------------------------------------------------- #

@app.get("/api/v1/families")
def list_families():
    con = get_connection()
    cur = con.cursor()
    rows = [_row_to_dict(r) for r in cur.execute("""
        SELECT g_protein_family AS family,
               count(*) AS n_systems,
               count(DISTINCT receptor_uniprot) AS n_receptors,
               count(*) * 1500.0 AS total_sampling_ns
        FROM systems
        WHERE system_id IN (""" + FINAL_RELEASE_SQL + ") GROUP BY g_protein_family ORDER BY n_systems DESC", FINAL_RELEASE_IDS).fetchall()]
    con.close()
    return {"families": rows}


# --------------------------------------------------------------------------- #
# Systems list
# --------------------------------------------------------------------------- #

@app.get("/api/v1/systems")
def list_systems(
    family: Optional[str] = Query(None, description="G-protein family (Gi, Gs, Gq, G12-13)"),
    uniprot: Optional[str] = Query(None, description="Receptor UniProt accession"),
    gene: Optional[str] = Query(None, description="Receptor gene name (case-insensitive)"),
    trajectory_type: Optional[str] = Query(None, description="membrane_embedded"),
    provenance: Optional[str] = Query(None, description="experimental | engineered_uncertain"),
    gpcr_class: Optional[str] = Query(None, description="GPCR class (A, B)"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    filters, params = [f"system_id IN ({FINAL_RELEASE_SQL})"], list(FINAL_RELEASE_IDS)
    if family:
        filters.append("g_protein_family = ?")
        params.append(family)
    if uniprot:
        filters.append("receptor_uniprot = ?")
        params.append(uniprot)
    if gene:
        filters.append("lower(receptor_gene) = lower(?)")
        params.append(gene)
    if trajectory_type:
        filters.append("trajectory_type = ?")
        params.append(trajectory_type)
    if provenance:
        filters.append("structural_provenance = ?")
        params.append(provenance)
    if gpcr_class:
        requested_class = gpcr_class.strip().upper()
        if requested_class not in {"A", "B"}:
            raise HTTPException(status_code=422, detail="gpcr_class must be A or B")
        class_ids = [sid for sid in FINAL_RELEASE_IDS if FINAL_RELEASE_CLASS[sid] == requested_class]
        filters.append("system_id IN (" + ",".join("?" * len(class_ids)) + ")")
        params.extend(class_ids)

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    con = get_connection()
    cur = con.cursor()
    cur.execute(f"SELECT count(*) FROM systems {where}", params)
    total = cur.fetchone()[0]

    cur.execute(
        f"""
        SELECT system_id, pdb_id, receptor_name, receptor_uniprot, receptor_gene,
               g_protein_family, g_alpha_subtype, ligand_name, ligand_chem_id,
               n_replicas, total_sampling_ns, force_field, trajectory_type,
               has_bilayer, structural_provenance, traj_size_bytes, gpcr_class
        FROM systems {where}
        ORDER BY g_protein_family, system_id
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset],
    )
    rows = [_row_to_dict(r) for r in cur.fetchall()]

    # Attach analysis availability for each system
    if rows:
        sids = [r["system_id"] for r in rows]
        placeholders = ",".join("?" * len(sids))
        cur.execute(
            f"SELECT system_id, file_type FROM system_pocket_files WHERE system_id IN ({placeholders})",
            sids,
        )
        pocket_types = {}
        for pr in cur.fetchall():
            pocket_types.setdefault(pr["system_id"], set()).add(pr["file_type"])

        cur.execute(
            f"SELECT system_id, file_type FROM system_gateway_files WHERE system_id IN ({placeholders})",
            sids,
        )
        gateway_types = {}
        for gr in cur.fetchall():
            gateway_types.setdefault(gr["system_id"], set()).add(gr["file_type"])

        for r in rows:
            sid = r["system_id"]
            pt = pocket_types.get(sid, set())
            gt = gateway_types.get(sid, set())
            r["analysis_available"] = {
                "pockets": "pockets_json" in pt,
                "pockets_gpcrdb": "pockets_gpcrdb_json" in pt,
                "pocketgrid": "pocketgrid_npz" in pt,
                "gateways": "gateways_json" in gt,
            }

    con.close()
    return {"total": total, "limit": limit, "offset": offset, "systems": rows}


# --------------------------------------------------------------------------- #
# Single system
# --------------------------------------------------------------------------- #

@app.get("/api/v1/systems/{system_id}")
def get_system(system_id: str):
    _validate_system_id(system_id)
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT * FROM systems WHERE system_id = ?", (system_id,))
    row = cur.fetchone()
    con.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"System '{system_id}' not found")

    meta = _row_to_dict(row)

    # Attach analysis file availability from the DB.
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT file_type, file_path, file_size_bytes FROM system_pocket_files WHERE system_id = ?",
        (system_id,),
    )
    pocket_files = {r["file_type"]: {"path": r["file_path"], "size_bytes": r["file_size_bytes"]}
                    for r in cur.fetchall()}
    cur.execute(
        "SELECT file_type, file_path, file_size_bytes FROM system_gateway_files WHERE system_id = ?",
        (system_id,),
    )
    gateway_files = {r["file_type"]: {"path": r["file_path"], "size_bytes": r["file_size_bytes"]}
                     for r in cur.fetchall()}
    con.close()

    return {
        **meta,
        "analysis_available": {
            "pockets": "pockets_json" in pocket_files,
            "pockets_gpcrdb": "pockets_gpcrdb_json" in pocket_files,
            "pocketgrid": "pocketgrid_npz" in pocket_files,
            "gateways": "gateways_json" in gateway_files,
        },
    }


@app.get("/api/v1/systems/{system_id}/pockets")
def get_system_pockets(system_id: str, gpcrdb: bool = Query(True, description="Return GPCRdb-mapped version")):
    _validate_system_id(system_id)
    filename = "pockets_gpcrdb.json" if gpcrdb else "pockets.json"
    path = _system_json_path(system_id, filename)
    # Fall back to raw pockets.json if GPCRdb version is missing
    if not path.exists() and gpcrdb:
        fallback = _system_json_path(system_id, "pockets.json")
        if fallback.exists():
            path = fallback
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No pocket data for '{system_id}'",
        )
    return _load_json(path)


@app.get("/api/v1/systems/{system_id}/gateways")
def get_system_gateways(system_id: str):
    _validate_system_id(system_id)
    path = _system_json_path(system_id, "gateways.json")
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No gateway data for '{system_id}' (protein-only systems have no bilayer gateways)",
        )
    return _load_json(path)


@app.get("/api/v1/systems/{system_id}/pocketgrid")
def get_system_pocketgrid(system_id: str):
    """Return the pocketgrid.npz occupancy frequency grid as a binary download."""
    _validate_system_id(system_id)
    # Prefer the copied file; fall back to ANALYSIS_SRC path registered in DB.
    local_path = _system_json_path(system_id, "pocketgrid.npz")
    if local_path.exists():
        return FileResponse(local_path, media_type="application/octet-stream",
                            filename=f"{system_id}_pocketgrid.npz")

    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT file_path FROM system_pocket_files WHERE system_id=? AND file_type='pocketgrid_npz'",
        (system_id,),
    )
    row = cur.fetchone()
    con.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"No pocketgrid for '{system_id}'")
    src = Path(row["file_path"])
    if not src.exists():
        raise HTTPException(status_code=503,
                            detail=f"Pocketgrid file registered but not accessible: {src}")
    return FileResponse(src, media_type="application/octet-stream",
                        filename=f"{system_id}_pocketgrid.npz")


# --------------------------------------------------------------------------- #
# Consensus endpoints
# --------------------------------------------------------------------------- #

@app.get("/api/v1/consensus/pockets/druggable")
def consensus_pockets_druggable():
    return _load_json(API_V1 / "consensus" / "pockets_druggable.json")


@app.get("/api/v1/consensus/pockets/orthosteric")
def consensus_pockets_orthosteric():
    return _load_json(API_V1 / "consensus" / "pockets_orthosteric.json")


@app.get("/api/v1/consensus/gateways")
def consensus_gateways(
    pair: Optional[str] = Query(None, description='e.g. "TM1-TM2"'),
    metric: Optional[str] = Query(None, description="occupancy | penetration | open_fraction"),
    group: Optional[str] = Query(None, description="G-protein family or 'all'"),
):
    data = _load_json(API_V1 / "consensus" / "gateways.json")
    records = data.get("records", [])
    if pair:
        records = [r for r in records if r.get("pair") == pair]
    if metric:
        records = [r for r in records if r.get("metric") == metric]
    if group:
        records = [r for r in records if r.get("group") == group]
    return {**data, "records": records, "n_records": len(records)}


@app.get("/api/v1/consensus/nominations")
def consensus_nominations():
    return _load_json(API_V1 / "consensus" / "druggable_nominations.json")


@app.get("/api/v1/consensus/reorg")
def consensus_reorg():
    return _load_json(API_V1 / "consensus" / "reorg_atlas.json")


@app.get("/api/v1/systems/{system_id}/gprotein")
def get_system_gprotein(system_id: str):
    _validate_system_id(system_id)
    path = _system_json_path(system_id, "gprotein_metrics.json")
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No G-protein metrics for '{system_id}'",
        )
    return _load_json(path)


@app.get("/api/v1/consensus/coupling")
def consensus_coupling():
    return _load_json(API_V1 / "consensus" / "coupling_geometry.json")


@app.get("/api/v1/consensus/gprotein/barcode")
def consensus_gprotein_barcode():
    return _load_json(API_V1 / "consensus" / "gprotein_barcode_reference.json")


# --------------------------------------------------------------------------- #
# Viz tier — structure PDB and decimated XTC per system
# --------------------------------------------------------------------------- #

@app.get("/api/v1/systems/{system_id}/viz/structure")
def get_viz_structure(system_id: str):
    """Reference PDB for NGL topology loading."""
    _validate_system_id(system_id)
    _no_cache = {"Cache-Control": "no-cache"}
    path = VIZ_DIR / system_id / "structure.pdb"
    if path.exists():
        return FileResponse(path, media_type="chemical/x-pdb",
                            filename=f"{system_id}_structure.pdb",
                            headers=_no_cache)
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT file_path FROM system_viz_files WHERE system_id=? AND file_type='structure_pdb'",
        (system_id,),
    )
    row = cur.fetchone()
    con.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"No viz structure for '{system_id}'")
    src = Path(row["file_path"])
    if not src.exists():
        raise HTTPException(status_code=503, detail=f"Viz structure registered but missing: {src}")
    return FileResponse(src, media_type="chemical/x-pdb",
                        filename=f"{system_id}_structure.pdb",
                        headers=_no_cache)


@app.get("/api/v1/systems/{system_id}/viz/trajectory")
def get_viz_trajectory(system_id: str):
    """Decimated XTC trajectory for NGL streaming."""
    _validate_system_id(system_id)
    _no_cache = {"Cache-Control": "no-cache"}
    path = VIZ_DIR / system_id / "traj.xtc"
    if path.exists():
        return FileResponse(path, media_type="application/octet-stream",
                            filename=f"{system_id}_traj.xtc", headers=_no_cache)
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT file_path FROM system_viz_files WHERE system_id=? AND file_type='traj_xtc'",
        (system_id,),
    )
    row = cur.fetchone()
    con.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"No viz trajectory for '{system_id}'")
    src = Path(row["file_path"])
    if not src.exists():
        raise HTTPException(status_code=503, detail=f"Viz trajectory registered but missing: {src}")
    return FileResponse(src, media_type="application/octet-stream",
                        filename=f"{system_id}_traj.xtc", headers=_no_cache)


@app.get("/api/v1/systems/{system_id}/viz/meta")
def get_viz_meta(system_id: str):
    """Return metadata about the viz files (n_frames, n_atoms, file sizes)."""
    _validate_system_id(system_id)
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT file_type, file_size_bytes, n_frames, n_atoms FROM system_viz_files WHERE system_id=?",
        (system_id,),
    )
    rows = cur.fetchall()
    con.close()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No viz files for '{system_id}'")
    meta = {r["file_type"]: {"size_bytes": r["file_size_bytes"],
                              "n_frames": r["n_frames"],
                              "n_atoms": r["n_atoms"]} for r in rows}
    return {"system_id": system_id, "viz_files": meta}


@app.get("/api/v1/systems/{system_id}/subunit-ranges")
def get_subunit_ranges(system_id: str):
    """Return residue ranges for each protein subunit (lightweight, for NGL coloring).
    Uses corrected chain_roles.json when available, falls back to contacts parquet.
    
    Returns each subunit as an array of {min, max} ranges to preserve
    fragment boundaries (e.g., Receptor + Receptor_frag0 as separate ranges
    so NGL renders each fragment as an independent cartoon segment).
    """
    _validate_system_id(system_id)
    
    # Try corrected chain_roles.json first
    chain_roles_path = CHAIN_ROLES_DIR / f"{system_id}_chain_roles.json"
    if chain_roles_path.exists():
        with open(chain_roles_path) as f:
            data = json.load(f)
        roles = data.get("roles", {})
        # Collect ranges per canonical subunit as a list (preserving fragments)
        subunit_range_lists = {}
        for role, info in roles.items():
            # Map Receptor_frag* → Receptor for coloring, but keep as separate range
            canonical = "Receptor" if role.startswith("Receptor") else role
            if canonical not in ("G_alpha", "Receptor", "G_beta", "G_gamma"):
                continue
            rng = info.get("ngl_range", "") or info.get("resid_range", "")
            if "-" in rng:
                parts = rng.split("-")
                rmin, rmax = int(parts[0]), int(parts[1])
                subunit_range_lists.setdefault(canonical, []).append({"min": rmin, "max": rmax})
        # Sort ranges within each subunit by min residue
        subunit_ranges = {}
        for canonical, ranges in subunit_range_lists.items():
            ranges.sort(key=lambda r: r["min"])
            subunit_ranges[canonical] = ranges
        if subunit_ranges:
            return {"system_id": system_id, "subunit_ranges": subunit_ranges}
    
    # Fallback: derive from contacts parquet
    parquet_path = CONTACTS_DIR / f"{system_id}_contacts.parquet"
    if not parquet_path.exists():
        raise HTTPException(status_code=404, detail=f"No contact data for '{system_id}'")
    import pandas as pd
    df = pd.read_parquet(parquet_path, columns=["subunit1", "subunit2", "res1", "res2"])
    subunit_ranges = {}
    for sub in ["G_alpha", "Receptor", "G_beta", "G_gamma"]:
        r1 = df.loc[df["subunit1"] == sub, "res1"]
        r2 = df.loc[df["subunit2"] == sub, "res2"]
        all_resids = pd.concat([r1, r2])
        if len(all_resids) > 0:
            subunit_ranges[sub] = {"min": int(all_resids.min()), "max": int(all_resids.max())}
    return {"system_id": system_id, "subunit_ranges": subunit_ranges}


@app.get("/api/v1/systems/{system_id}/contacts")
def get_system_contacts(system_id: str,
                        min_freq: float = Query(0.4, description="Minimum contact frequency"),
                        scope: str = Query("receptor_galpha", description="Scope: receptor_galpha, receptor_only, or all")):
    """Return residue-residue contact frequencies for a system."""
    _validate_system_id(system_id)
    parquet_path = CONTACTS_DIR / f"{system_id}_contacts.parquet"
    if not parquet_path.exists():
        raise HTTPException(status_code=404, detail=f"No contact data for '{system_id}'")

    import pandas as pd
    df = pd.read_parquet(parquet_path)

    # Extract subunit residue ranges (before filtering) for NGL coloring.
    # Receptor_frag* labels are collapsed into Receptor.
    subunit_ranges = {}
    for col in ["subunit1", "subunit2"]:
        res_col = "res1" if col == "subunit1" else "res2"
        for label in df[col].unique():
            canonical = "Receptor" if str(label).startswith("Receptor") else label
            if canonical not in ("G_alpha", "Receptor", "G_beta", "G_gamma"):
                continue
            resids = df.loc[df[col] == label, res_col]
            if len(resids) == 0:
                continue
            if canonical not in subunit_ranges:
                subunit_ranges[canonical] = {"min": int(resids.min()), "max": int(resids.max())}
            else:
                subunit_ranges[canonical]["min"] = min(subunit_ranges[canonical]["min"], int(resids.min()))
                subunit_ranges[canonical]["max"] = max(subunit_ranges[canonical]["max"], int(resids.max()))

    # Filter by minimum frequency
    df = df[df["frequency"] >= min_freq]

    # Filter by scope
    if scope == "receptor_only":
        df = df[(df["subunit1"] == "Receptor") & (df["subunit2"] == "Receptor")]
    elif scope == "receptor_galpha":
        df = df[
            ((df["subunit1"] == "Receptor") & (df["subunit2"] == "Receptor")) |
            ((df["subunit1"] == "Receptor") & (df["subunit2"] == "G_alpha")) |
            ((df["subunit1"] == "G_alpha") & (df["subunit2"] == "Receptor")) |
            ((df["subunit1"] == "G_alpha") & (df["subunit2"] == "G_alpha"))
        ]

    # Convert to list of dicts for JSON
    # Only return columns needed by the frontend
    df = df[["res1", "res2", "subunit1", "subunit2", "itype", "frequency"]]
    contacts = df.to_dict(orient="records")
    return {
        "system_id": system_id,
        "n_contacts": len(contacts),
        "scope": scope,
        "min_freq": min_freq,
        "subunit_ranges": subunit_ranges,
        "contacts": contacts,
    }


# --------------------------------------------------------------------------- #
# robots.txt
# --------------------------------------------------------------------------- #

@app.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
def robots_txt():
    return """User-agent: *
Allow: /
Disallow: /api/v1/systems/*/viz/trajectory
Disallow: /api/v1/systems/*/pocketgrid
"""


# --------------------------------------------------------------------------- #
# Frontend static files — MUST be last so API routes take priority
# --------------------------------------------------------------------------- #

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail="Not found")
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            # no-cache so the browser always revalidates index.html and picks up
            # new hashed bundle filenames after a deploy (assets are hashed → cacheable).
            return FileResponse(index, headers={"Cache-Control": "no-cache"})
        raise HTTPException(status_code=404, detail="Frontend not built")
