#!/usr/bin/env python3
"""
Backfill missing receptor_gene values in data/systems_master.csv by querying
the UniProt REST API for each system's receptor_uniprot accession.

Why: 179 of 222 systems have a blank receptor_gene in the source CSV (the
detail page then renders "(null)" and the family/gene search can't find them).
UniProt exposes the official gene symbol at genes[0].geneName.value.

This script updates the CSV (the source of truth for scripts/p1_ingest.py),
so re-running the ingest pipeline preserves the backfill. It does NOT touch
the SQLite DB directly — run `python3 scripts/p1_ingest.py` afterwards to
push the corrected CSV into db/coupledmd.sqlite.

Usage:
    python3 scripts/backfill_receptor_genes.py            # apply
    python3 scripts/backfill_receptor_genes.py --dry-run  # report only

Systems with no receptor_uniprot (Gq_7E9W, Gs_8HTI) cannot be queried and
are left untouched — the UI guards handle them.
"""
import argparse
import csv
import sys
import time
import urllib.request
import urllib.error
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "systems_master.csv"

UNIPROT_BATCH_URL = "https://rest.uniprot.org/uniprotkb/accessions"
USER_AGENT = "CoupledMD-build/1.0 (mailto:jxhuang@sjtu.edu.cn)"
BATCH_SIZE = 25  # keep batches modest to avoid URL-length/throttling issues
MAX_RETRIES = 4


def fetch_genes(accessions: list[str]) -> dict[str, str]:
    """Query UniProt for a batch of accessions; return {accession: gene_symbol}.

    Retries with exponential backoff on connection/SSL errors (UniProt
    intermittently throttles bursty programmatic clients).
    """
    if not accessions:
        return {}
    qs = "&".join(f"accessions={a}" for a in accessions)
    url = f"{UNIPROT_BATCH_URL}?{qs}&size={len(accessions)}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    })

    data = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < MAX_RETRIES - 1:
                wait = 5 * (attempt + 1)
                print(f"  HTTP {e.code} (throttled); retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  HTTPError {e.code} for batch of {len(accessions)}; skipping", file=sys.stderr)
            return {}
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait = 5 * (attempt + 1)
                print(f"  connect error ({e}); retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  giving up on batch of {len(accessions)}: {e}", file=sys.stderr)
            return {}

    out = {}
    for entry in data.get("results", []):
        acc = entry.get("primaryAccession")
        genes = entry.get("genes", [])
        if genes:
            gene = genes[0].get("geneName", {}).get("value")
            if gene:
                out[acc] = gene
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Report what would change; do not write the CSV.")
    args = ap.parse_args()

    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Find rows needing a gene: blank gene but present uniprot.
    needs = [r for r in rows
             if (not r.get("receptor_gene") or r["receptor_gene"].strip() == "")
             and r.get("receptor_uniprot") and r["receptor_uniprot"].strip() != ""]
    accessions = sorted({r["receptor_uniprot"].strip() for r in needs})
    print(f"Systems needing gene backfill: {len(needs)}")
    print(f"Unique UniProt accessions to query: {len(accessions)}")

    # Query in batches.
    acc_to_gene: dict[str, str] = {}
    for i in range(0, len(accessions), BATCH_SIZE):
        batch = accessions[i:i + BATCH_SIZE]
        print(f"  querying UniProt {i+len(batch)}/{len(accessions)} ...", flush=True)
        acc_to_gene.update(fetch_genes(batch))
        time.sleep(2.0)  # be polite to the UniProt API

    print(f"Gene symbols retrieved: {len(acc_to_gene)}")

    # Apply to rows.
    filled = 0
    unfilled_accessions = set()
    for r in needs:
        acc = r["receptor_uniprot"].strip()
        gene = acc_to_gene.get(acc)
        if gene:
            r["receptor_gene"] = gene
            filled += 1
        else:
            unfilled_accessions.add(acc)

    print(f"\nFilled receptor_gene for {filled}/{len(needs)} systems.")
    if unfilled_accessions:
        print(f"Accessions UniProt returned no gene for ({len(unfilled_accessions)}): "
              f"{', '.join(sorted(unfilled_accessions)[:10])}"
              + (" ..." if len(unfilled_accessions) > 10 else ""))

    # Systems with no uniprot at all — cannot backfill.
    no_uniprot = [r["system_id"] for r in rows
                  if (not r.get("receptor_gene") or r["receptor_gene"].strip() == "")
                  and (not r.get("receptor_uniprot") or r["receptor_uniprot"].strip() == "")]
    if no_uniprot:
        print(f"\nSystems with no UniProt accession (cannot backfill, UI guards handle): "
              f"{', '.join(no_uniprot)}")

    if args.dry_run:
        print("\n[DRY RUN] CSV not modified.")
        return

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote updated CSV: {CSV_PATH}")
    print("Next: run `python3 scripts/p1_ingest.py` to push the corrected CSV into the DB.")


if __name__ == "__main__":
    main()
