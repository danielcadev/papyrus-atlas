"""Plan HTTP ranges for exact whole XY planes in uncompressed C-order uint8 Zarr chunks."""
import argparse
import json
from itertools import groupby
from pathlib import Path
from urllib.request import Request, urlopen


def plan_ranges(planes, chunk_shape):
    """Coalesce (chunk key, local Z) plane requests into inclusive byte ranges."""
    z_size, height, width = map(int, chunk_shape)
    if min(z_size, height, width) <= 0:
        raise ValueError("Chunk dimensions must be positive.")
    plane_bytes = height * width
    intervals = []
    for key, collection in groupby(sorted(set(planes)), key=lambda request: request[0]):
        if len(key) != 3 or min(key) < 0:
            raise ValueError("Expected a nonnegative Z/Y/X chunk key.")
        previous = start = None
        for _, z in collection:
            if not 0 <= z < z_size:
                raise ValueError("Plane is outside its chunk.")
            if previous is None:
                start = z
            elif z != previous + 1:
                intervals.append((key, start * plane_bytes, z_end(previous, plane_bytes)))
                start = z
            previous = z
        intervals.append((key, start * plane_bytes, z_end(previous, plane_bytes)))
    return intervals


def z_end(z, plane_bytes):
    return (z + 1) * plane_bytes - 1


def read_range(url, start, stop, *, object_bytes, etag, timeout=20):
    """Fetch one verified inclusive range and return only its bytes."""
    if not (0 <= start <= stop < object_bytes):
        raise ValueError("Range is outside the declared object.")
    if not etag.startswith('"') or not etag.endswith('"'):
        raise ValueError("A strong quoted ETag is required.")
    request = Request(url, headers={
        "Range": f"bytes={start}-{stop}",
        "If-Match": etag,
        "Accept-Encoding": "identity",
    })
    size = stop - start + 1
    with urlopen(request, timeout=timeout) as response:
        if response.status != 206 or response.url != url:
            raise ValueError("Expected a direct HTTP 206 response.")
        if response.headers.get("Content-Range") != f"bytes {start}-{stop}/{object_bytes}":
            raise ValueError("Content-Range does not match the requested interval.")
        if response.headers.get("ETag") != etag:
            raise ValueError("The object changed.")
        if response.headers.get("Content-Encoding", "identity").lower() != "identity":
            raise ValueError("A byte-range object needs identity HTTP encoding.")
        result = response.read(size + 1)
    if len(result) != size:
        raise ValueError("Unexpected range body length.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text())
    for case in fixture["cases"]:
        shape = case["chunks"]
        raw = [(tuple(row["key"]), *row["byte_range"]) for row in case["receipts"]]
        plane_bytes = shape[1] * shape[2]
        assert all(start % plane_bytes == (stop + 1) % plane_bytes == 0 for _, start, stop in raw)
        requested = [(key, z) for key, start, stop in raw
                     for z in range(start // plane_bytes, (stop + 1) // plane_bytes)]
        planned = plan_ranges(requested, shape)
        assert sorted(raw) == planned
        body = sum(stop - start + 1 for _, start, stop in planned)
        assert body == case["observed_body_bytes"]
        whole = len({key for key, _, _ in planned}) * shape[0] * plane_bytes
        print(f"{case['name']} {len(planned)} exact ranges, {body:,}/{whole:,} payload bytes")


if __name__ == "__main__":
    main()
