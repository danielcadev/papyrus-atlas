"""Fetch a pinned upstream archive and apply the release's checked patch series."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tarfile,urllib.request
from release_guard import require_guard

def digest(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):result.update(block)
    return result.hexdigest()

def main():
    guard=require_guard();package=Path(__file__).resolve().parent.parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination',type=Path,required=True)
    p.add_argument('--archive',type=Path,help='Optional already downloaded, byte-verified original archive.')
    args=p.parse_args();dest=args.destination.resolve();dest.mkdir(parents=True,exist_ok=False)
    spec=json.loads((package/'patches/series.json').read_text());archive=args.archive
    if archive is None:
        archive=dest/'upstream.tar.gz'
        with urllib.request.urlopen(spec['upstream']['url'],timeout=60) as response,archive.open('xb') as output:
            while block:=response.read(1024*1024):output.write(block)
    assert digest(archive)==spec['upstream']['sha256'],'Upstream archive digest mismatch'
    source=dest/'source';source.mkdir()
    with tarfile.open(archive,'r:gz') as stream:
        for member in stream:
            parts=Path(member.name).parts[1:]
            if not parts:continue
            assert '..' not in parts and not Path(*parts).is_absolute()
            target=source.joinpath(*parts)
            if member.isdir():target.mkdir(parents=True,exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True,exist_ok=True)
                with stream.extractfile(member) as inp,target.open('xb') as out:
                    while block:=inp.read(1024*1024):out.write(block)
                target.chmod(member.mode & 0o777)
            else:raise ValueError(f'Unexpected archive member type: {member.name}')
    for stage in spec['patches']:
        patch=package/'patches'/stage['file'];assert digest(patch)==stage['sha256']
        for relative,expected in stage['before'].items():
            path=source/relative
            assert (digest(path) if path.exists() else None)==expected,(stage['file'],relative,'before')
        subprocess.run(['patch','--batch','--forward','--fuzz=0','-p1','-i',str(patch)],cwd=source,check=True)
        for relative,expected in stage['after'].items():assert digest(source/relative)==expected
    result=dict(passed=True,guard=guard,source=str(source),upstream=spec['upstream'],
        patches=[entry['file'] for entry in spec['patches']],third_party_source_retrieved_directly_not_redistributed=True)
    (dest/'bootstrap-result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
