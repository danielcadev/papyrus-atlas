"""Frozen 45-ray CT/manual-label inventory; never infer pitch or arm a gate.

Run only under run_native_guarded.py in the project's constrained systemd unit.
Positive label runs are observed annotation support, not certified sheet centers.
Zero labels mean unannotated/unknown, never empty space. No mesh is opened.
"""
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'native/paris4-label-radial-inventory-v1'
CAL = ROOT / 'native/paris4-winding-calibration-v1/calibration.json'
AXIS = CAL.parent / 'umbilicus-world-zyx.csv'
CT = ROOT / 'data/01744_02256_04048_volume.nrrd'
MASK = ROOT / 'data/01744_02256_04048_mask.nrrd'
MANIFEST = ROOT / 'data/manifest.json'
CAL_SHA = 'bdf55d44b3e96cfd7db3a1a53e6ec9076e938144082712e651a58893c8ab651f'
AXIS_SHA = '9bd2e8611cd23aad5266fce6653b47a0bd109aad74d897ede29d4a8c9acefb37'
CT_SHA = '3041f5bd3bf5b9d3d68be6a65934c39664d04c2f221ca23561bde0d1376ee110'
MASK_SHA = '5925bff9b6bd5398504bc2aa67621a0632fcadf3d4b2638055e1d4dd7b781e64'
ORIGIN = [1744, 2256, 4048]
Z_PLANES = [144, 152, 160, 168, 176]
TARGET_COORDS = [112, 128, 144]
STEP = .5


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def nrrd(path):
    with path.open('rb') as stream:
        lines = []
        for _ in range(100):
            line = stream.readline(4096)
            require(line, 'Missing NRRD data')
            if not line.strip():
                break
            lines.append(line.decode().strip())
        else:
            raise ValueError('Oversized NRRD header')
        fields = dict(line.split(': ', 1) for line in lines
                      if ': ' in line and not line.startswith('#'))
        require(fields.get('dimension') == '3' and fields.get('sizes') == '256 256 256',
                'Unexpected NRRD shape')
        require('data file' not in fields, 'Detached NRRD unsupported')
        dtype = {'uint8': np.dtype('u1'), 'unsigned char': np.dtype('u1'),
                 'uint16': np.dtype('<u2'), 'unsigned short': np.dtype('<u2')}[fields['type']]
        require(dtype.itemsize == 1 or fields.get('endian') == 'little', 'Unexpected endian')
        nbytes = 256**3 * dtype.itemsize
        if fields['encoding'] == 'gzip':
            with gzip.GzipFile(fileobj=stream) as compressed:
                payload = compressed.read(nbytes + 1)
        else:
            require(fields['encoding'] == 'raw', 'Unsupported NRRD encoding')
            payload = stream.read(nbytes + 1)
        require(len(payload) == nbytes, 'NRRD payload size mismatch')
    return np.frombuffer(payload, dtype=dtype).reshape((256, 256, 256), order='F'), fields


def bilinear(volume, x, y, z):
    ix, iy = np.floor(x).astype(int), np.floor(y).astype(int)
    dx, dy = x-ix, y-iy
    return ((1-dx)*(1-dy)*volume[ix, iy, z] + dx*(1-dy)*volume[ix+1, iy, z]
            + (1-dx)*dy*volume[ix, iy+1, z] + dx*dy*volume[ix+1, iy+1, z])


def ray_geometry(cx, cy, target_x, target_y):
    theta = math.atan2(target_y-cy, target_x-cx)
    direction = [math.cos(theta), math.sin(theta)]
    lo, hi = 0., float('inf')
    for center, component in zip((cx, cy), direction):
        if abs(component) < 1e-14:
            require(2 <= center <= 253, 'Ray misses CT inset')
        else:
            a, b = sorted(((2-center)/component, (253-center)/component))
            lo, hi = max(lo, a), min(hi, b)
    require(math.isfinite(hi) and hi > lo, 'Invalid ray interval')
    radius = np.arange(math.ceil(lo/STEP)*STEP, hi, STEP)
    require(len(radius) >= 8, 'Too few radial samples')
    return theta, radius, cx+radius*direction[0], cy+radius*direction[1]


def peak_inventory(raw, radius):
    grid = np.arange(-6, 7, dtype=float)
    kernel = np.exp(-.5*(grid/1.5)**2)
    kernel /= kernel.sum()
    smooth = np.convolve(np.pad(raw, 6, mode='reflect'), kernel, mode='valid')
    differences = np.diff(raw)
    noise = float(1.4826*np.median(np.abs(differences-np.median(differences)))/math.sqrt(2))
    threshold = max(1.5*noise, .05*float(np.std(smooth)))
    peaks = []
    for i in np.where((smooth[1:-1] > smooth[:-2]) & (smooth[1:-1] >= smooth[2:]))[0]+1:
        if i < 3 or i+3 >= len(smooth):
            continue
        prominence = float(smooth[i] - max(smooth[i-3:i].min(), smooth[i+1:i+4].min()))
        peaks.append(dict(sample=int(i), radius_voxels=float(radius[i]),
                          intensity=float(smooth[i]), local_prominence=prominence,
                          above_diagnostic_threshold=bool(prominence >= threshold)))
    return smooth, peaks, dict(noise_mad=noise, prominence_threshold=threshold,
                              sigma_voxels=.75, prominence_half_window_voxels=1.5,
                              purpose='CT extrema diagnostic; neither sheets nor adjacency certified')


def annotation_runs(labels, radius):
    starts = [0] + (np.where(labels[1:] != labels[:-1])[0]+1).tolist()
    ends = starts[1:] + [len(labels)]
    records = []
    for index, (start, end) in enumerate(zip(starts, ends)):
        lab = int(labels[start])
        records.append(dict(run=index, label=lab, annotation_status='positive' if lab else 'unknown_zero',
                            first_sample=start, end_sample_exclusive=end,
                            radius_first=float(radius[start]), radius_last=float(radius[end-1]),
                            center_of_observed_support=float((radius[start]+radius[end-1])/2),
                            support_width_voxels=float((end-start)*STEP),
                            touches_sample_boundary=start == 0 or end == len(labels),
                            center_is_certified_sheet_center=False))
    return records


def candidate_pairs(runs, peaks, roi):
    positive = [r for r in runs if r['label'] > 0]
    pairs = []
    for a, b in zip(positive, positive[1:]):
        intervening = runs[a['run']+1:b['run']]
        interior = [p for p in peaks if a['radius_last'] < p['radius_voxels'] < b['radius_first']]
        reasons = ['annotation_adjacency_not_established_by_inventory']
        if a['label'] == b['label']:
            reasons.append('same_label_reentry_or_fragmentation')
        if intervening:
            reasons.append('zero_labels_between_runs_are_unknown_not_empty')
        if any(p['above_diagnostic_threshold'] for p in interior):
            reasons.append('intermediate_CT_extrema_require_sheet_review')
        if a['touches_sample_boundary'] or b['touches_sample_boundary']:
            reasons.append('annotation_support_truncated_at_ray_boundary')
        pairs.append(dict(left_run=a['run'], right_run=b['run'], labels=[a['label'], b['label']],
                          support_center_separation_voxels=b['center_of_observed_support']-a['center_of_observed_support'],
                          separation_is_pitch=False, zero_run_indices=[r['run'] for r in intervening],
                          intervening_CT_peak_samples=[p['sample'] for p in interior],
                          significant_intervening_CT_peaks=sum(p['above_diagnostic_threshold'] for p in interior),
                          intersects_target_radius_interval=bool(b['radius_first'] >= roi[0] and a['radius_last'] <= roi[1]),
                          adjacency_accepted=False, rejection_or_review_reasons=reasons))
    return pairs


def label_color(label):
    return (55, 55, 55) if label == 0 else (60+(label*67)%196, 60+(label*113)%196, 60+(label*37)%196)


def render_strip(path, strip, labels, radius, raw, smooth, peaks, record, Image, ImageDraw):
    width, left, top = len(radius), 65, 45
    # Fixed full dtype range: no per-strip normalization that exaggerates noise.
    gray = np.clip(strip / (257 if record['ct_dtype_bytes'] == 2 else 1), 0, 255).astype('uint8')
    pixels = np.repeat(gray[:, :, None], 3, axis=2)
    base = Image.fromarray(pixels).resize((width, 72), Image.Resampling.NEAREST)
    canvas = Image.new('RGB', (left+width+20, 300), '#161616')
    canvas.paste(base, (left, top))
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 5), record['ray_id'] + '  CT z-4..z+4; label at central z', fill='white')
    draw.text((8, 22), 'ASSISTED inventory. Gray label = unknown. No pitch/adjacency accepted.', fill='white')
    for i, label in enumerate(labels):
        draw.line((left+i, 126, left+i, 142), fill=label_color(int(label)))
    draw.text((5, 126), 'labels', fill='white')
    for run in record['runs']:
        if run['label']:
            middle = (run['first_sample']+run['end_sample_exclusive'])//2
            draw.text((left+middle, 146+(run['run']%2)*12), str(run['label']), fill=label_color(run['label']))
    scale = 257 if record['ct_dtype_bytes'] == 2 else 1
    for values, color in ((raw, '#aaaaaa'), (smooth, '#ffa850')):
        points = [(left+i, 268-min(255, max(0, float(value)/scale))*90/255) for i, value in enumerate(values)]
        draw.line(points, fill=color, width=1)
    for peak in peaks:
        if peak['above_diagnostic_threshold']:
            x = left+peak['sample']
            draw.line((x, 171, x, 175), fill='#ff7777')
    for value in range(int(math.ceil(radius[0]/25)*25), int(radius[-1])+1, 25):
        x = left+int(round((value-radius[0])/STEP))
        draw.line((x, 270, x, 274), fill='white')
        draw.text((x-9, 277), str(value), fill='white')
    draw.text((4, 277), 'r vox', fill='white')
    canvas.save(path)


def main():
    from prepare_next_validation import require_guard
    guarded = require_guard()
    require(not OUT.exists(), 'Preserve existing inventory outputs')
    OUT.mkdir()
    global np
    import numpy as np
    result = dict(schema='paris4-label-radial-inventory-v1', state='started',
                  method='manual-label-assisted CT inventory, same development cube; not blind',
                  calibration_valid=False, winding_gate_ready=False, pitch_voxels=None,
                  manual_labels_opened=False, result_meshes_opened=False,
                  zero_label_meaning='unknown or unannotated; never evidence of empty space',
                  source_origin_world_zyx=ORIGIN, source_volume_id='20230205180739',
                  guard=guarded, rays=[], inputs={},
                  sampling=dict(z_local=Z_PLANES, target_xy_cartesian=TARGET_COORDS,
                                radial_step_voxels=STEP, inset_xy=[2, 253],
                                CT_profile='bilinear XY, arithmetic mean of z-1,z,z+1',
                                mask_profile='nearest XY at central z, floor(coord+0.5)',
                                strip_z_offsets=list(range(-4, 5))))
    try:
        for key, path, expected in [('calibration_v1', CAL, CAL_SHA), ('axis_csv', AXIS, AXIS_SHA),
                                    ('CT', CT, CT_SHA), ('mask', MASK, MASK_SHA),
                                    ('manifest', MANIFEST, None), ('script', Path(__file__), None)]:
            digest = sha256(path)
            result['inputs'][key] = dict(path=str(path), sha256=digest)
            require(expected is None or digest == expected, key+' hash mismatch')
        cal = json.loads(CAL.read_text())
        manifest = json.loads(MANIFEST.read_text())
        require(cal.get('axis_valid') is True and cal['source_sha256'] == CT_SHA
                and cal['coordinates'] == 'worldZYX', 'v1 axis/source contract mismatch')
        require(cal['artifacts'][AXIS.name] == AXIS_SHA, 'v1 axis artifact mismatch')
        require(manifest['cube_zyx_origin'] == ORIGIN, 'Manifest origin mismatch')
        for path, expected in ((CT, CT_SHA), (MASK, MASK_SHA)):
            entries = [r for r in manifest['files'] if r['file'] == path.name]
            require(len(entries) == 1 and entries[0]['sha256'] == expected, 'Manifest file mismatch')
        axis = np.loadtxt(AXIS, delimiter=',', skiprows=1)
        require(axis.shape == (146, 3) and np.isfinite(axis).all()
                and np.all(np.diff(axis[:, 0]) > 0), 'Invalid axis CSV')
        require(np.array_equal(axis, np.asarray(cal['axis_zyx'])), 'CSV/JSON axis differs')
        require(axis[0, 0] <= ORIGIN[0]+144 and axis[-1, 0] >= ORIGIN[0]+176, 'Axis does not cover target Z')
        volume, ct_header = nrrd(CT)
        mask, mask_header = nrrd(MASK)
        result['manual_labels_opened'] = True
        result['headers'] = dict(CT=ct_header, mask=mask_header)
        require(ct_header.get('space directions') == mask_header.get('space directions')
                and ct_header.get('space origin') == mask_header.get('space origin'), 'CT/mask coordinate mismatch')
        try:
            from PIL import Image, ImageDraw
            result['png_available'] = True
        except ImportError:
            Image = ImageDraw = None
            result['png_available'] = False
        pair_csv = OUT / 'candidate-pairs.csv'
        with pair_csv.open('x', newline='') as pair_stream:
            pairs_writer = csv.writer(pair_stream)
            pairs_writer.writerow(['ray', 'left_label', 'right_label', 'left_run', 'right_run',
                                   'support_center_separation_not_pitch', 'roi_intersection', 'review_reasons'])
            for z_local in Z_PLANES:
                z = ORIGIN[0]+z_local
                cy = float(np.interp(z, axis[:, 0], axis[:, 1]))-ORIGIN[1]
                cx = float(np.interp(z, axis[:, 0], axis[:, 2]))-ORIGIN[2]
                near_x, near_y = min(144., max(112., cx)), min(144., max(112., cy))
                roi = [math.hypot(near_x-cx, near_y-cy),
                       max(math.hypot(x-cx, y-cy) for x in (112, 144) for y in (112, 144))]
                for target_y in TARGET_COORDS:
                    for target_x in TARGET_COORDS:
                        ray_id = f'z{z_local:03d}-x{target_x:03d}-y{target_y:03d}'
                        theta, radius, x, y = ray_geometry(cx, cy, target_x, target_y)
                        strip = np.asarray([bilinear(volume, x, y, z_local+dz) for dz in range(-4, 5)])
                        raw = strip[3:6].mean(axis=0)
                        labels = mask[np.floor(x+.5).astype(int), np.floor(y+.5).astype(int), z_local]
                        smooth, peaks, peak_method = peak_inventory(raw, radius)
                        runs = annotation_runs(labels, radius)
                        pairs = candidate_pairs(runs, peaks, roi)
                        record = dict(ray_id=ray_id, z_local=z_local, z_world=z,
                                      target_local_xy=[target_x, target_y], axis_local_yx=[cy, cx],
                                      theta_radians=theta, radial_interval_voxels=[float(radius[0]), float(radius[-1])],
                                      target_radius_interval_voxels=roi,
                                      covers_target_radius_interval=bool(radius[0] <= roi[0] and radius[-1] >= roi[1]),
                                      samples=len(radius), ct_dtype_bytes=volume.dtype.itemsize,
                                      positive_label_samples=int(np.count_nonzero(labels)),
                                      unknown_zero_samples=int(np.count_nonzero(labels == 0)),
                                      positive_ids=sorted(set(int(v) for v in labels if v)),
                                      runs=runs, CT_peaks=peaks, peak_method=peak_method,
                                      candidate_pairs=pairs, profile=ray_id+'.csv',
                                      adjacent_pairs_certified=0)
                        with (OUT / record['profile']).open('x', newline='') as stream:
                            writer = csv.writer(stream)
                            writer.writerow(['radius_voxels', 'x_local', 'y_local', 'CT_mean3z',
                                             'CT_central_z', 'CT_smoothed', 'label_nearest_central_z'])
                            writer.writerows(zip(radius, x, y, raw, strip[4], smooth, map(int, labels)))
                        for pair in pairs:
                            pairs_writer.writerow([ray_id, *pair['labels'], pair['left_run'], pair['right_run'],
                                                   pair['support_center_separation_voxels'],
                                                   pair['intersects_target_radius_interval'],
                                                   '|'.join(pair['rejection_or_review_reasons'])])
                        if Image is not None:
                            record['strip_png'] = ray_id+'.png'
                            render_strip(OUT / record['strip_png'], strip, labels, radius, raw, smooth,
                                         peaks, record, Image, ImageDraw)
                        result['rays'].append(record)
                        print(json.dumps(dict(ray=ray_id, positive_runs=sum(r['label'] > 0 for r in runs),
                                              candidate_pairs=len(pairs), certified_pairs=0)), flush=True)
        require(len(result['rays']) == 45, 'Frozen ray count mismatch')
        result['summary'] = dict(rays=45, rays_with_positive_labels=sum(bool(r['positive_ids']) for r in result['rays']),
                                 candidate_pairs=sum(len(r['candidate_pairs']) for r in result['rays']),
                                 certified_adjacent_pairs=0, pitch_emitted=False)
        result['state'] = 'inventory-complete-adjacency-review-required'
    except Exception as error:
        result['state'] = 'failed-closed'
        result['error'] = type(error).__name__+': '+str(error)
    result['artifacts'] = {p.name: sha256(p) for p in sorted(OUT.iterdir()) if p.is_file()}
    write_json(OUT / 'inventory.json', result)
    print(json.dumps(dict(output=str(OUT), state=result['state'], summary=result.get('summary'),
                          calibration_valid=False, winding_gate_ready=False)), flush=True)
    return 2 if result['state'] == 'failed-closed' else 0


if __name__ == '__main__':
    raise SystemExit(main())
