#!/usr/bin/env python3
"""Final PBC verifier using the TRUE criterion (raw all-atom span is too strict —
it flags genuinely elongated-but-correctly-assembled complexes that NGL renders
fine). A viz system is correctly assembled iff, densely across the trajectory:

  * reassembly-Δ ≈ 0  — greedy proximity reassembly of the chain-role segments
    does NOT reduce the span (i.e. no chain sits in a wrong periodic image), AND
  * 0 min-image-collapsing CA breaks — no consecutive CA pair within a chain is
    >8 Å apart in a way that collapses under the minimum-image convention (a real
    PBC split, as opposed to a genuine structural gap).

Also reports frame0 RMSD to structure.pdb and blank-element count (NGL blockers).

Usage: python3 scripts/verify_pbc_final.py SYS [SYS ...]   (default: all 23)
"""
import sys, json, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np
import MDAnalysis as mda

ROOT = Path(__file__).resolve().parents[1]
VIZ = ROOT / "data" / "viz"
ROLES = ROOT / "scripts" / "audit_output" / "chain_roles"
STEP = 25   # frame stride for dense sampling


def roles_of(sid):
    r = json.load(open(ROLES / f"{sid}_chain_roles.json"))["roles"]
    return {k: [int(x) for x in v["resid_range"].split("-")] for k, v in r.items()}


def reassemble_span(segpos, box):
    order = sorted(segpos, key=lambda p: -len(p))
    cens = [order[0].mean(0)]; allp = [order[0]]
    for p in order[1:]:
        c = p.mean(0); best = np.zeros(3); bd = np.inf
        for pc in cens:
            sh = box * np.round((pc - c) / box); d = np.linalg.norm(c + sh - pc)
            if d < bd: bd, best = d, sh
        q = p + best; allp.append(q); cens.append(q.mean(0))
    return np.vstack(allp).ptp(0) / box


def verify(sid):
    u = mda.Universe(str(VIZ / sid / "structure.pdb"), str(VIZ / sid / "traj.xtc"))
    ref = mda.Universe(str(VIZ / sid / "structure.pdb"))
    roles = roles_of(sid)
    seg_ca = {lbl: u.select_atoms(f"name CA and resid {a}:{b}") for lbl, (a, b) in roles.items()}
    nfr = len(u.trajectory)
    u.trajectory[0]
    r0 = np.sqrt(((u.atoms.positions - ref.atoms.positions) ** 2).sum(1).mean())
    blank = int((ref.atoms.elements == "").sum()) if hasattr(ref.atoms, "elements") else -1
    max_d = 0.0; max_after = np.zeros(3); break_frames = 0
    for fi in range(0, nfr, STEP):
        u.trajectory[fi]; box = u.dimensions[:3]
        seg = [u.select_atoms(f"resid {a}:{b}").positions for a, b in roles.values()]
        seg = [p for p in seg if len(p)]
        before = np.vstack(seg).ptp(0) / box
        after = reassemble_span(seg, box)
        max_d = max(max_d, float((before - after).max()))
        max_after = np.maximum(max_after, after)
        # min-image-collapsing CA break within any chain
        bad = False
        for ca in seg_ca.values():
            if ca.n_atoms < 2: continue
            dv = np.diff(ca.positions, axis=0); d = np.linalg.norm(dv, axis=1)
            for k in np.where(d > 8.0)[0]:
                if np.linalg.norm(dv[k] - box * np.round(dv[k] / box)) <= 8.0:
                    bad = True; break
            if bad: break
        if bad: break_frames += 1
    n = len(range(0, nfr, STEP))
    # PASS criteria reflect what NGL actually renders: a chain in the wrong image
    # (reasmΔ>0.1) or a broken bond within a chain (min-image-collapsing CA break)
    # is a visible defect; a large span_after with reasmΔ=0 is just a genuinely
    # elongated-but-whole complex and renders fine. frame0 RMSD >10 A means the
    # trajectory was fit to a wrong/broken structure.pdb reference.
    ok = (max_d <= 0.10) and (break_frames == 0) and blank == 0 and (r0 <= 10.0)
    print(f"{'PASS' if ok else 'FAIL'}  {sid:11s} reasmΔ={max_d:.2f} span_after={max_after.round(2)} "
          f"pbc_break_frames={break_frames}/{n} frame0_RMSD={r0:.2f} blank={blank}")
    return ok


ALL23 = ["Gs_7F4H","Gq_7S8L","Gq_7XJL","Gi_8J22","Gs_6UVA","Gi_8YIC","Gq_8DPF","Gi_7V68",
         "Gi_7YK6","Gi_7YON","Gq_8DWC","Gq_7DWC","Gi_6LFO","Gq_7W55","Gi_6WWZ","Gi_6OSA",
         "Gq_7F8W","Gi_7XK8","Gi_7XA3","G12_8H8J","Gs_8GY7","Gs_8XVI","Gi_8K6O"]

if __name__ == "__main__":
    sids = sys.argv[1:] or ALL23
    n_pass = sum(verify(s) for s in sids)
    print(f"\n{n_pass}/{len(sids)} PASS")
