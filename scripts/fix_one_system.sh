#!/bin/bash
# Full PBC-pipeline fix for one viz system. Usage: fix_one_system.sh <SYSTEM_ID>
# Runs: build-fake-tpr -> grompp -> make-ndx -> src-to-xtc -> gmx cluster ->
#       assemble-multipass -> fix-structure -> update-db -> audit
# Safeguards: backs up traj.xtc, verifies atom-order match, refuses on mismatch.
set -uo pipefail
SYS="${1:?usage: $0 <SYSTEM_ID>}"
cd /MDdata/data02/jxhuang/gpcr_g/gpcr_g_server
PDB=data/viz/$SYS/structure.pdb
XTC=data/viz/$SYS/traj.xtc
ROLES=scripts/audit_output/chain_roles/${SYS}_chain_roles.json
[ -f "$ROLES" ] && RARG="--roles $ROLES" || RARG=""
export GMXLIB=$(pwd)/scripts/audit_output/gmx_top
TMP=/tmp/${SYS}_fix

# locate source
PDBID=$(python3 -c "import pandas as pd; print(pd.read_csv('data/systems_master.csv').set_index('system_id').loc['$SYS','pdb_id'])")
FAM=$(python3 -c "import pandas as pd; print(pd.read_csv('data/systems_master.csv').set_index('system_id').loc['$SYS','g_protein_family'])")
declare -A FAMMAP=( [G12-13]="a/a_g12 b/b2_g12" [Gi]="a/a_gi b/b1_gi b/b2_gi" [Gq]="a/a_gq b/b1_gq b/b2_gq" [Gs]="a/a_gs b/b1_gs b/b2_gs" )
SRC=""
for sub in ${FAMMAP[$FAM]}; do
  for ext in nc trr xtc; do
    p=/MDdata/data04/gpcr_g_database/$sub/$PDBID/traj1.$ext
    [ -f "$p" ] && SRC="$p" && break
  done
  [ -n "$SRC" ] && break
done
[ -z "$SRC" ] && { echo "$SYS: NO SOURCE FOUND"; exit 1; }
echo "=== $SYS  (pdb=$PDBID fam=$FAM src=$SRC) ==="

# safety: atom-order match between viz pdb and source
python3 -c "
import warnings; warnings.filterwarnings('ignore')
import MDAnalysis as mda
uv=mda.Universe('$PDB'); us=mda.Universe('${SRC%/*}/protein.pdb','$SRC')
if uv.atoms.n_atoms!=us.atoms.n_atoms:
    print('ATOM-COUNT-MISMATCH viz',uv.atoms.n_atoms,'src',us.atoms.n_atoms); raise SystemExit(2)
if not (uv.atoms.names==us.atoms.names).all():
    print('ATOM-ORDER-MISMATCH (names differ)'); raise SystemExit(2)
print('atom-order OK:', uv.atoms.n_atoms, 'atoms')
" || { echo "$SYS: atom-order mismatch — skipping, needs manual handling"; exit 2; }

# backup traj.xtc
[ -f "$XTC.broken_pbc_backup" ] || cp -p "$XTC" "$XTC.broken_pbc_backup"

rm -rf $TMP; mkdir -p $TMP
# A. fake tpr
python3 scripts/fix_viz_pbc_pdb.py build-fake-tpr --pdb $PDB $RARG --outdir $TMP 2>&1 | tail -1
gmx grompp -f $TMP/fake.mdp -c $TMP/fake.gro -p $TMP/fake.top -o $TMP/fake.tpr -maxwarn 5 2>&1 | grep -iE "error|fatal" | head -2
# B. index
python3 scripts/fix_viz_pbc_pdb.py make-ndx --pdb $PDB --out $TMP/sys.ndx 2>&1 | tail -1
# C1. src -> fullres xtc
python3 scripts/fix_viz_pbc_pdb.py src-to-xtc --pdb $PDB --src $SRC --out $TMP/fullres.xtc 2>&1 | tail -1
# C2. cluster
printf '1\n1\n' | gmx trjconv -s $TMP/fake.tpr -f $TMP/fullres.xtc -n $TMP/sys.ndx -o $TMP/cluster.xtc -pbc cluster 2>&1 | grep -aiE "Last frame|fatal|inconsistent" | tail -1
# C3. assemble-multipass
python3 scripts/fix_viz_pbc_pdb.py assemble-multipass --pdb $PDB --cluster $TMP/cluster.xtc $RARG --ndx $TMP/sys.ndx --out $XTC --stride 4 2>&1 | tail -1
# D. fix structure
python3 scripts/fix_viz_pbc_pdb.py fix-structure --pdb $PDB $RARG 2>&1 | tail -1
# E. update db + audit
python3 scripts/fix_viz_pbc_pdb.py update-db --system $SYS 2>&1 | tail -1
python3 scripts/audit_viz_pbc_full.py --system $SYS --frames 10 --out $TMP/audit.csv 2>&1 | grep -E "$SYS "
rm -rf $TMP
echo "--- $SYS done ---"
