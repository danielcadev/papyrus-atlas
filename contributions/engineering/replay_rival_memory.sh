set -euo pipefail
p=$1
py=$2
out=$3
mkdir "$out"
for combo in x:old x:packed y:packed y:old; do
 IFS=: read -r axis method <<<"$combo"
 if [[ "$axis" == x ]]; then
   blocks=task258-pherc0191-m7; target=task263-pherc0191-western-target; old=task263-pherc0191-western-scene
 else
   blocks=task277-pherc0191-tail-m7; target=task281-pherc0191-lower-target; old=task281-pherc0191-lower-scene
 fi
 src="$p/$old/evaluate.py"
 if [[ "$method" == packed ]]; then src="$p/task661-rival-control-$axis/evaluate.py"; fi
 /usr/bin/time -f '{"wall_s":%e,"peak_rss_kib":%M}' -o "$out/$axis-$method.time.json" \
  "$py" "$src" --catalog "$p/task254-pherc0191-catalog" --block-case "$p/$blocks" \
  --rival-inventory-mesh "$p/$target" --inventory-axis "$axis" --output "$out/$axis-$method"
done
"$py" - "$out" <<'PY'
from pathlib import Path
import sys
from pherc0813_auto_reader import Seals, digest, load, save

out=Path(sys.argv[1])
rows=[]
for axis in ('x','y'):
    old,packed=(out/f'{axis}-{mode}' for mode in ('old','packed'))
    for case in (old,packed):
        Seals().verify(case)
    same=[name for name in ('EXACT-TARGET.npz','rivals-f64.bin') if digest(old/name)==digest(packed/name)]
    assert len(same)==2
    left,right=(load(p/'RESULT.json') for p in (old,packed))
    counters=['candidate_closed_cells','exact_duplicate_cells','conservatively_relevant_rival_triangles']
    assert all(left[key]==right[key] for key in counters)
    rows.append(dict(axis=axis,baseline=load(out/f'{axis}-old.time.json'),
                     packed=load(out/f'{axis}-packed.time.json'),
                     exact_hashes={name:digest(old/name) for name in same},
                     counts={key:left[key] for key in counters}))
save(out/'comparison.json',dict(rows=rows,scope='Matched PHerc0191 native block and exact target files; one replay each; GNU time peak RSS per command.'))
print(rows,flush=True)
PY
