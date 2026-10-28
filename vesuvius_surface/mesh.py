"""Small, strict mesh adapter; JSON and triangular Wavefront OBJ are native I/O."""
from dataclasses import dataclass
import json
import math
from pathlib import Path
import struct


@dataclass(frozen=True)
class Mesh:
    vertices: tuple
    faces: tuple

    def __post_init__(self):
        object.__setattr__(self, "vertices", tuple(tuple(p) for p in self.vertices))
        object.__setattr__(self, "faces", tuple(tuple(f) for f in self.faces))
        if not self.vertices or len(self.vertices) > 20000 or len(self.faces) > 20000:
            raise ValueError("Mesh size is outside the bounded research domain")
        for p in self.vertices:
            if len(p) != 3 or any(type(x) not in (int, float) or not math.isfinite(x) for x in p):
                raise ValueError("Vertices must contain three finite numbers")
        for f in self.faces:
            if len(f) != 3 or len(set(f)) != 3 or any(type(x) is not int or not 0 <= x < len(self.vertices) for x in f):
                raise ValueError("Faces must contain three distinct valid indices")

    @classmethod
    def read(cls, filename):
        path = Path(filename)
        if path.stat().st_size > 32 * 1024**2:
            raise ValueError("Mesh input exceeds 32 MiB")
        if path.suffix == ".json":
            data = json.loads(path.read_text())
            return cls(tuple(tuple(v) for v in data["vertices"]), tuple(tuple(f) for f in data["faces"]))
        if path.suffix == ".obj":
            vertices, faces = [], []
            for line in path.read_text().splitlines():
                fields = line.split()
                if not fields or fields[0].startswith("#"):
                    continue
                if fields[0] == "v" and len(fields) == 4:
                    vertices.append(tuple(map(float, fields[1:])))
                elif fields[0] == "f" and len(fields) == 4 and all("/" not in x for x in fields[1:]):
                    faces.append(tuple(int(x) - 1 for x in fields[1:]))
                else:
                    raise ValueError("Only plain triangular OBJ v/f records are supported")
            return cls(tuple(vertices), tuple(faces))
        if path.suffix != ".vmesh":
            raise ValueError("Expected .json, .obj or historical .vmesh")
        # Import-only compatibility with archived ScrollFiesta output. No
        # upstream library is loaded and no upstream build is required.
        payload = path.read_bytes()
        header = struct.Struct("<8sIIIIQQQQQ")
        magic, version, endian, flags, hs, nv, nf, vo, uo, fo = header.unpack_from(payload)
        if (magic, version, endian, hs) != (b"VESMESH1", 1, 0x01020304, 64):
            raise ValueError("Invalid historical mesh header")
        if flags & ~3 or (flags & 2 and not flags & 1) or not 0 < nv <= 20000 or not 0 < nf <= 20000:
            raise ValueError("Invalid historical mesh flags/counts")
        ve = hs + nv * 12
        if vo != hs or uo != (ve if flags & 1 else 0) or fo != ve + (nv * (16 if flags & 2 else 8) if flags & 1 else 0) or len(payload) != fo + nf * 12:
            raise ValueError("Invalid historical mesh layout")
        if flags:
            raise ValueError("UV-bearing meshes require a UV-preserving adapter; refusing to discard UV")
        return cls(tuple(struct.iter_unpack("<fff", payload[vo:ve])), tuple(struct.iter_unpack("<iii", payload[fo:])))

    def write(self, filename):
        path = Path(filename)
        if path.exists():
            raise FileExistsError("Preserve existing output: " + str(path))
        if path.suffix == ".json":
            text = json.dumps({"vertices": self.vertices, "faces": self.faces}, allow_nan=False) + "\n"
        elif path.suffix == ".obj":
            text = "".join("v " + " ".join(repr(x) for x in p) + "\n" for p in self.vertices)
            text += "".join("f " + " ".join(str(x + 1) for x in f) + "\n" for f in self.faces)
        else:
            raise ValueError("Output must be .json or .obj")
        with path.open("x") as stream:
            stream.write(text)
