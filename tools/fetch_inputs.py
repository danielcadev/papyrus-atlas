"""Download the original public CT and annotations with pinned byte checks."""
from pathlib import Path
import argparse,json,urllib.request
from bootstrap import digest
from release_guard import require_guard

def main():
    guard=require_guard();package=Path(__file__).resolve().parent.parent
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    records=[]
    for entry in json.loads((package/'public-data.json').read_text())['files']:
        path=out/entry['file']
        with urllib.request.urlopen(entry['url'],timeout=60) as response,path.open('xb') as stream:
            while block:=response.read(1024*1024):stream.write(block)
        assert path.stat().st_size==entry['bytes'] and digest(path)==entry['sha256']
        records.append(dict(**entry,path=str(path)))
    result=dict(passed=True,guard=guard,files=records,
        scope='Original public data retrieved directly; not redistributed or relicensed by the software release.')
    (out/'input-downloads.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)

if __name__=='__main__':main()
