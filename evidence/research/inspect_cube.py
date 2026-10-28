import gzip
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from guard import start_guard


def read_nrrd(path):
    with open(path, 'rb') as stream:
        header = []
        while True:
            line = stream.readline()
            if not line:
                raise ValueError('Missing NRRD data')
            if not line.strip():
                break
            header.append(line.decode().rstrip())
        fields = dict(line.split(': ', 1) for line in header if ': ' in line and not line.startswith('#'))
        assert fields['dimension'] == '3'
        shape = tuple(map(int, fields['sizes'].split()))
        dtype = {'uint8': np.dtype('u1'), 'unsigned char': np.dtype('u1'),
                 'uint16': np.dtype('<u2'), 'unsigned short': np.dtype('<u2')}[fields['type']]
        assert np.prod(shape) <= 256**3
        if dtype.itemsize > 1:
            assert fields.get('endian') == 'little'
        if fields['encoding'] == 'gzip':
            with gzip.GzipFile(fileobj=stream) as compressed:
                raw = compressed.read(int(np.prod(shape)) * dtype.itemsize + 1)
        elif fields['encoding'] == 'raw':
            raw = stream.read()
        else:
            raise ValueError(fields['encoding'])
        assert len(raw) == int(np.prod(shape)) * dtype.itemsize
        return np.frombuffer(raw, dtype=dtype).reshape(shape, order='F'), fields


if __name__ == '__main__':
    start_guard()
    root = Path(__file__).resolve().parent
    volume, header = read_nrrd(root / 'data/01744_02256_04048_volume.nrrd')
    labels, _ = read_nrrd(root / 'data/01744_02256_04048_mask.nrrd')
    print(json.dumps(dict(shape=volume.shape, dtype=str(volume.dtype),
                         range=[int(volume.min()), int(volume.max())],
                         instance_ids=np.unique(labels).tolist(),
                         label_fraction=float(np.count_nonzero(labels) / labels.size))), flush=True)
    canvas = Image.new('RGB', (3 * 256, 280), '#161616')
    draw = ImageDraw.Draw(canvas)
    rng = np.random.default_rng(0)
    colors = rng.integers(40, 255, (int(labels.max()) + 1, 3), dtype=np.uint8)
    for axis in range(3):
        gray = np.take(volume, 128, axis=axis).astype(np.float32)
        low, high = np.percentile(gray, [2, 98])
        gray = np.clip((gray - low) / max(high - low, 1) * 255, 0, 255).astype(np.uint8)
        rgb = np.repeat(gray[:, :, None], 3, axis=2)
        lab = np.take(labels, 128, axis=axis)
        sel = lab > 0
        rgb[sel] = (rgb[sel].astype(np.uint16) + colors[lab[sel]].astype(np.uint16)) // 2
        canvas.paste(Image.fromarray(rgb), (256 * axis, 24))
        draw.text((256 * axis + 8, 6), f'Native axis {axis}, index 128', fill='white')
    canvas.save(root / 'cube-inspection.png')
