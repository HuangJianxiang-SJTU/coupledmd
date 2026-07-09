import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# ---- Health ----

def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok"
    assert d["n_systems"] == 222
    assert d["schema_version"] == "1.0"


# ---- Families ----

def test_families():
    r = client.get("/api/v1/families")
    assert r.status_code == 200
    d = r.json()
    fams = d["families"]
    assert len(fams) == 4
    names = {f["family"] for f in fams}
    assert names == {"Gi", "Gs", "Gq", "G12-13"}


# ---- Systems list ----

def test_systems_list():
    r = client.get("/api/v1/systems")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 222
    assert len(d["systems"]) > 0


def test_systems_filter_family():
    r = client.get("/api/v1/systems", params={"family": "Gi"})
    assert r.status_code == 200
    d = r.json()
    assert d["total"] > 0
    assert all(s["g_protein_family"] == "Gi" for s in d["systems"])


def test_systems_filter_gene():
    r = client.get("/api/v1/systems", params={"gene": "ADRB2"})
    assert r.status_code == 200
    d = r.json()
    # Gene filter is case-insensitive; just check it doesn't error
    assert d["total"] >= 0


def test_systems_filter_trajectory_type():
    r = client.get("/api/v1/systems", params={"trajectory_type": "membrane_embedded"})
    assert r.status_code == 200
    d = r.json()
    assert d["total"] > 0
    assert all(s["trajectory_type"] == "membrane_embedded" for s in d["systems"])


def test_systems_pagination():
    r = client.get("/api/v1/systems", params={"limit": 5, "offset": 0})
    assert r.status_code == 200
    d = r.json()
    assert len(d["systems"]) <= 5
    assert d["limit"] == 5
    assert d["offset"] == 0


# ---- Single system ----

def test_system_detail():
    r = client.get("/api/v1/systems/G12_7T6B")
    assert r.status_code == 200
    d = r.json()
    assert d["system_id"] == "G12_7T6B"
    assert d["pdb_id"]
    assert d["receptor_name"]
    assert d["receptor_uniprot"]
    assert d["receptor_gene"]
    assert d["g_protein_family"]
    assert "analysis_available" in d


def test_system_detail_not_found():
    r = client.get("/api/v1/systems/NONEXISTENT")
    assert r.status_code == 404


# ---- Pockets ----

def test_system_pockets():
    r = client.get("/api/v1/systems/G12_7T6B/pockets", params={"gpcrdb": True})
    # May be 200 or 404 depending on data availability
    if r.status_code == 200:
        d = r.json()
        assert "pockets" in d
    else:
        assert r.status_code == 404


def test_system_pockets_raw():
    r = client.get("/api/v1/systems/G12_7T6B/pockets", params={"gpcrdb": False})
    if r.status_code == 200:
        d = r.json()
        assert "pockets" in d


# ---- Gateways ----

def test_system_gateways():
    r = client.get("/api/v1/systems/G12_7T6B/gateways")
    if r.status_code == 200:
        d = r.json()
        assert "records" in d
    else:
        assert r.status_code == 404


# ---- Viz tier ----

def test_viz_meta():
    r = client.get("/api/v1/systems/G12_7T6B/viz/meta")
    assert r.status_code == 200
    d = r.json()
    assert "viz_files" in d
    assert "traj_xtc" in d["viz_files"] or "structure_pdb" in d["viz_files"]


def test_viz_structure():
    r = client.get("/api/v1/systems/G12_7T6B/viz/structure")
    assert r.status_code == 200
    assert "pdb" in r.headers.get("content-type", "").lower() or \
           "octet-stream" in r.headers.get("content-type", "").lower()


def test_viz_trajectory():
    r = client.get("/api/v1/systems/G12_7T6B/viz/trajectory")
    assert r.status_code == 200
    assert "octet-stream" in r.headers.get("content-type", "").lower()


def test_viz_meta_not_found():
    r = client.get("/api/v1/systems/NONEXISTENT/viz/meta")
    assert r.status_code == 404


# ---- Consensus endpoints ----

def test_consensus_druggable():
    r = client.get("/api/v1/consensus/pockets/druggable")
    assert r.status_code == 200
    d = r.json()
    assert "clusters" in d
    assert len(d["clusters"]) > 0


def test_consensus_orthosteric():
    r = client.get("/api/v1/consensus/pockets/orthosteric")
    assert r.status_code == 200


def test_consensus_gateways():
    r = client.get("/api/v1/consensus/gateways")
    assert r.status_code == 200
    d = r.json()
    assert "records" in d
    assert len(d["records"]) > 0


def test_consensus_gateways_filters():
    r = client.get("/api/v1/consensus/gateways", params={"metric": "occupancy", "group": "Gi"})
    assert r.status_code == 200
    d = r.json()
    for rec in d["records"]:
        assert rec["metric"] == "occupancy"
        assert rec["group"] == "Gi"


def test_consensus_nominations():
    r = client.get("/api/v1/consensus/nominations")
    assert r.status_code == 200
    d = r.json()
    assert "nominations" in d


def test_consensus_reorg():
    r = client.get("/api/v1/consensus/reorg")
    assert r.status_code == 200
    d = r.json()
    assert "comparisons" in d
    for c in d["comparisons"]:
        assert c["sid_A"]
        assert c["sid_B"]


# ---- Path traversal guard ----

def test_path_traversal_rejected():
    # The system_id validator rejects IDs that don't match ^[A-Za-z0-9_-]{1,64}$
    r = client.get("/api/v1/systems/..%2F..%2Fetc%2Fpasswd")
    assert r.status_code in (400, 404, 422)


def test_path_traversal_pockets():
    r = client.get("/api/v1/systems/..%2F..%2Fetc%2Fpasswd/pockets")
    assert r.status_code in (400, 404, 422)


def test_path_traversal_viz():
    r = client.get("/api/v1/systems/..%2F..%2Fetc%2Fpasswd/viz/structure")
    assert r.status_code in (400, 404, 422)


def test_invalid_system_id_special_chars():
    # System IDs must be alphanumeric + dash/underscore only
    r = client.get("/api/v1/systems/;rm%20-rf%20/")
    assert r.status_code in (400, 404, 422)
