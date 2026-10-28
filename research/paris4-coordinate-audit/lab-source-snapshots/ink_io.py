"""Bounded, immutable HTTP object cache for guarded ink experiments."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
CACHE = ROOT/'ink-reading/acquisition-v1'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fetch(url, cap=8*1024**2, expected_sha=None):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()
    target = CACHE/(key+'.bin')
    receipt = CACHE/(key+'.json')
    if target.exists():
        record = json.loads(receipt.read_text())
        assert record['url'] == url and digest(target) == record['sha256']
        assert target.stat().st_size <= cap
    else:
        temporary = CACHE/(key+'.part')
        assert not temporary.exists(), f'Preserve failed download: {temporary}'
        h = hashlib.sha256()
        size = 0
        with urllib.request.urlopen(url, timeout=30) as response, temporary.open('xb') as stream:
            while True:
                block = response.read(1024**2)
                if not block:
                    break
                size += len(block)
                assert size <= cap, f'Object exceeds {cap} bytes'
                h.update(block)
                stream.write(block)
            record = dict(url=url, bytes=size, sha256=h.hexdigest(), status=response.status,
                          etag=response.headers.get('ETag'), link=response.headers.get('Link'),
                          path=str(target))
        if expected_sha:
            assert record['sha256'] == expected_sha, 'Remote object SHA mismatch'
        assert not target.exists() and not receipt.exists()
        temporary.rename(target)
        with receipt.open('x') as stream:
            json.dump(record, stream, indent=2)
    if expected_sha:
        assert record['sha256'] == expected_sha
    return target, record


def json_object(url):
    path, record = fetch(url)
    return json.loads(path.read_text()), record
