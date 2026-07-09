#!/usr/bin/env python3
"""
Fix blank-element atoms in a viz structure.pdb (the Gi_8YIC root cause).

NGL's colorScheme:'element' throws on ATOM/HETATM lines whose element column
(cols 77-78) is blank, aborting the structure-load callback before the
trajectory loads. This assigns an element to every blank atom:

  - LP/LPH (CHARMM lone-pair, massless) -> 'H'
  - other blanks -> guess from atom name (first non-digit char, uppercased)

Surgical: only the element column is touched; the rest of each line is
byte-identical. Backs up to structure.pdb.pre_elem_fix.

Usage:
    python3 scripts/fix_blank_elements.py <system_id> [<system_id> ...]
    python3 scripts/fix_blank_elements.py --pdb path/to/structure.pdb
"""
import argparse
import shutil
import sys
from pathlib import Path

VIZ = Path(__file__).resolve().parent.parent / "data" / "viz"


def assign_elem(name):
    n = name.strip().lstrip("0123456789")
    if n.startswith("LP"):
        return "H"
    if not n:
        return "C"
    return n[0].upper()


def fix_pdb(pdb_path, dry=False):
    pdb_path = Path(pdb_path)
    with open(pdb_path) as f:
        lines = f.readlines()
    fixed = 0
    out = []
    for line in lines:
        if line.startswith(("ATOM", "HETATM")) and len(line) >= 78 and line[76:78].strip() == "":
            name = line[12:16]
            elem = assign_elem(name)
            l = line.rstrip("\n")
            if len(l) < 78:
                l = l.ljust(78)
            # cols 77-78 (0-indexed 76:78): right-justified 2-char element
            l = l[:76] + f"{elem:>2s}" + l[78:]
            out.append(l + "\n")
            fixed += 1
        else:
            out.append(line)
    if fixed == 0:
        print(f"  {pdb_path}: no blank elements (nothing to do)")
        return 0
    if not dry:
        shutil.copy2(pdb_path, str(pdb_path) + ".pre_elem_fix")
        with open(pdb_path, "w") as f:
            f.writelines(out)
    print(f"  {pdb_path}: fixed {fixed} blank elements")
    return fixed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("systems", nargs="*", help="system_id(s) under data/viz/")
    ap.add_argument("--pdb", help="explicit PDB path instead of system_id")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    targets = []
    if args.pdb:
        targets.append(args.pdb)
    else:
        if not args.systems:
            ap.error("give one or more system_ids, or --pdb")
        for s in args.systems:
            targets.append(VIZ / s / "structure.pdb")

    for t in targets:
        if not Path(t).exists():
            print(f"  MISSING: {t}", file=sys.stderr)
            continue
        fix_pdb(t, dry=args.dry)


if __name__ == "__main__":
    main()
