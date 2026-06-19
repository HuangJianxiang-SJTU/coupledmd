"""
CoupledMD API — FastAPI application.

All host-specific values (port, DATA_ROOT, DATABASE_URL, API_BASE_URL) come
from environment variables so the same image runs on localhost and the
university host with no code changes.

Endpoints:
    GET /api/v1/systems                  list with filters
    GET /api/v1/systems/{sid}            full metadata record
    GET /api/v1/systems/{sid}/pockets    GPCRdb-mapped pocket data
    GET /api/v1/systems/{sid}/gateways   gateway metrics
    GET /api/v1/families                 family summary with counts
    GET /api/v1/consensus/pockets/druggable
    GET /api/v1/consensus/pockets/orthosteric
    GET /api/v1/consensus/gateways
    GET /api/v1/consensus/nominations
    GET /api/v1/consensus/reorg
    GET /api/v1/health
"""

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import get_connection

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = Path(os.environ.get("DATA_ROOT", _PROJECT_ROOT))
API_V1 = DATA_ROOT / "data" / "api" / "v1"
FRONTEND_DIST = _PROJECT_ROOT / "frontend" / "dist"

app = FastAPI(
    title="CoupledMD",
    description="GPCR-G-protein MD web resource — 222 active-state ternary complex simulations.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened to specific origins in production
    allow_methods=["GET"],
    allow_headers=["*"],
)

# NOTE: frontend static files are mounted AFTER all API routes at the bottom
# of this file. Mounting here (before route definitions) would cause the
# catch-all to intercept all API paths.


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _row_to_dict(row) -> dict:
    return dict(row)


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
    cur.execute("SELECT count(*) FROM systems")
    n = cur.fetchone()[0]
    con.close()
    return {"status": "ok", "n_systems": n, "schema_version": "1.0"}


# --------------------------------------------------------------------------- #
# Families
# --------------------------------------------------------------------------- #

@app.get("/api/v1/families")
def list_families():
    con = get_connection()
    cur = con.cursor()
    cur.execute("""
        SELECT g_protein_family AS family,
               count(*) AS n_systems,
               count(DISTINCT receptor_uniprot) AS n_receptors,
               sum(total_sampling_ns) AS total_sampling_ns
        FROM systems
        GROUP BY g_protein_family
        ORDER BY n_systems DESC
    """)
    rows = [_row_to_dict(r) for r in cur.fetchall()]
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
    trajectory_type: Optional[str] = Query(None, description="membrane_embedded | protein_only"),
    provenance: Optional[str] = Query(None, description="experimental | engineered_uncertain"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    filters, params = [], []
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
               has_bilayer, structural_provenance, traj_size_bytes
        FROM systems {where}
        ORDER BY g_protein_family, system_id
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset],
    )
    rows = [_row_to_dict(r) for r in cur.fetchall()]
    con.close()
    return {"total": total, "limit": limit, "offset": offset, "systems": rows}


# --------------------------------------------------------------------------- #
# Single system
# --------------------------------------------------------------------------- #

@app.get("/api/v1/systems/{system_id}")
def get_system(system_id: str):
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
    filename = "pockets_gpcrdb.json" if gpcrdb else "pockets.json"
    path = _system_json_path(system_id, filename)
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No {'GPCRdb-mapped ' if gpcrdb else ''}pocket data for '{system_id}'",
        )
    return _load_json(path)


@app.get("/api/v1/systems/{system_id}/gateways")
def get_system_gateways(system_id: str):
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
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Frontend not built")
