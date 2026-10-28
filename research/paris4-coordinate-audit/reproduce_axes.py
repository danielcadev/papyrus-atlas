"""Reproduce the Paris4 same-scan axis test using Python's standard library.

Download SHA-pinned public objects, or supply a SHA-to-local-path JSON for an
offline replay. This checks coordinates only; it does not validate ink or text.
"""
import argparse
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from release_guard import require_guard

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def correlation(a,b):
    ma=sum(a)/len(a);mb=sum(b)/len(b)
    aa=[x-ma for x in a];bb=[x-mb for x in b]
    denominator=math.sqrt(sum(x*x for x in aa)*sum(x*x for x in bb))
    return -1. if denominator==0 else sum(x*y for x,y in zip(aa,bb))/denominator

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--offline-objects-json',type=Path)
    args=parser.parse_args();guard=require_guard()
    out=args.output.resolve();out.mkdir(exist_ok=False)
    sources=json.loads(Path(__file__).with_name('SOURCES.json').read_text())
    offline=json.loads(args.offline_objects_json.read_text()) if args.offline_objects_json else None
    receipts=[]
    def acquire(spec):
        if offline is not None:
            path=Path(offline[spec['sha256']]);assert sha(path)==spec['sha256']
        else:
            path=out/(spec['sha256']+'.bin');size=0
            with urllib.request.urlopen(spec['url'],timeout=30) as response,path.open('xb') as stream:
                while block:=response.read(1024**2):
                    size+=len(block);assert size<=spec['maximum_bytes'];stream.write(block)
            assert sha(path)==spec['sha256']
        receipts.append(dict(url=spec['url'],sha256=spec['sha256'],bytes=path.stat().st_size))
        return path
    nrrd=acquire(sources['nrrd'])
    with nrrd.open('rb') as stream:
        lines=[];size=0
        while line:=stream.readline():
            size+=len(line);assert size<65536
            if not line.strip():break
            lines.append(line.decode().rstrip())
        fields=dict(line.split(': ',1) for line in lines if ': ' in line and not line.startswith('#'))
        assert fields['sizes']=='256 256 256' and fields['type'] in ('uint8','unsigned char') and fields['encoding']=='gzip'
        with gzip.GzipFile(fileobj=stream) as compressed:raw=compressed.read(256**3+1)
        assert len(raw)==256**3
    points=list(itertools.product(range(96,160,4),repeat=3))
    values=[raw[i+256*(j+256*k)] for i,j,k in points]
    training=[((p[0]-96)//4)%2==0 for p in points]
    chunks={}
    for spec in sources['old_ct_chunks']:
        payload=acquire(spec).read_bytes();assert len(payload)==128**3
        chunks[tuple(spec['chunk'])]=payload
    origin=(1744,2256,4048);rows=[]
    for permutation in itertools.permutations(range(3)):
        for flips in itertools.product((False,True),repeat=3):
            sample=[]
            for p in points:
                q=[p[i] for i in permutation]
                q=[255-v if flip else v for v,flip in zip(q,flips)]
                q=[v+o for v,o in zip(q,origin)];key=tuple(v//128 for v in q)
                z,y,x=(v%128 for v in q);sample.append(chunks[key][(z*128+y)*128+x])
            fit=correlation([v for v,t in zip(values,training) if t],[v for v,t in zip(sample,training) if t])
            validation=correlation([v for v,t in zip(values,training) if not t],[v for v,t in zip(sample,training) if not t])
            rows.append(dict(permutation=list(permutation),flips=list(flips),training_pearson=fit,validation_pearson=validation))
    rows.sort(key=lambda row:-row['training_pearson']);best=rows[0]
    margin=best['validation_pearson']-max(row['validation_pearson'] for row in rows[1:])
    assert best['permutation']==[0,1,2] and best['flips']==[False]*3
    assert best['validation_pearson']>=.95 and margin>=.1
    result=dict(guard=guard,passed=True,anchor_points=len(points),tested_conventions=len(rows),
        best=best,validation_margin=margin,rows=rows,source_receipts=receipts,
        recovered_ink_or_letters_demonstrated=False,
        interpretation='Native NRRD indices match canonical old CT ZYX; catalogue XYZ input must reverse these native indices.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,best=best,validation_margin=margin)),flush=True)

if __name__=='__main__':main()
