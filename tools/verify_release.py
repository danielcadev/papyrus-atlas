"""Verify the sealed release inventory without executing archived evidence."""
from pathlib import Path
import json
from bootstrap import digest
from release_guard import require_guard

def main():
    guard=require_guard();package=Path(__file__).resolve().parent.parent
    manifest=json.loads((package/'MANIFEST.json').read_text())
    for relative,record in manifest['files'].items():
        path=package/relative
        assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
        assert path.is_file() and path.stat().st_size==record['bytes'] and digest(path)==record['sha256'],relative
    print(json.dumps(dict(passed=True,files_verified=len(manifest['files']),
        manifest_sha256=digest(package/'MANIFEST.json'),guard=guard,
        scope='Release file integrity only; experimental verification is recorded separately.')),flush=True)

if __name__=='__main__':main()
