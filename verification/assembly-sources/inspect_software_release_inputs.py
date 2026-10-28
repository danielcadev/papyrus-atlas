"""Inventory release inputs without changing source or historical evidence."""
from pathlib import Path
import hashlib,json,tarfile
from ink_guard import require_guard
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent;b=root/'scrollfiesta-comparison'
out=root/'software-release-inputs-v1.json';assert not out.exists()
changed=[];new=[]
with tarfile.open(b/'source.tar.gz','r:gz') as archive:
    prefix=archive.getmembers()[0].name.split('/')[0]+'/'
    originals={m.name[len(prefix):]:m for m in archive.getmembers() if m.isfile()}
    for path in sorted((b/'source/src').rglob('*')):
        if not path.is_file():continue
        relative=str(path.relative_to(b/'source'))
        content=path.read_bytes();before=originals.get(relative)
        if before is None:new.append(dict(path=relative,bytes=len(content)))
        else:
            original=archive.extractfile(before).read()
            if content!=original:changed.append(dict(path=relative,bytes=len(content),
                original_sha256=hashlib.sha256(original).hexdigest(),current_sha256=hashlib.sha256(content).hexdigest()))
    cmake=(b/'source/CMakeLists.txt').read_bytes()
    cmake_changed=cmake!=archive.extractfile(originals['CMakeLists.txt']).read()
result=dict(guard=guard,changed=changed,new=new,cmake_changed=cmake_changed,
    frozen_hole_source=str(b/'hole-recovery-v5/source-v5'))
out.write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
