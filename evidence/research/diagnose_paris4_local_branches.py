"""Frozen local CT branch diagnosis. No tracker, mesher, pitch, or leaf inference.

Box source XYZ [112,176) x [112,160) x [144,192), half-open slices.
Seed windows at z160 on the ray toward XY128,128: r277..288 and r294..312.
Ambiguous initial crests/orientation/interfaces stop the corresponding branch.
Run once, serially, through run_native_guarded.py and project systemd limits.
"""
import csv
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'native/paris4-local-branches-v1'
LOW = [112, 112, 144]
HIGH = [175, 159, 191]
WINDOWS = [('B1', 277., 288.), ('B2', 294., 312.)]
RULES = dict(seed_z=160, target_xy=[128, 128], seed_radial_step=.25,
             seed_profile_range=[269., 320.], seed_windows=WINDOWS,
             smoothing_sigma_voxels=.75, local_prominence_halfwidth_voxels=1.5,
             prominence_noise_factor=2., prominence_range_fraction=.1,
             seed_boundary_margin_voxels=1.,
             tensor_halfwidths_voxels=[2, 4], tensor_gaussian_sigmas=[1., 2.],
             tensor_minimum_largest_to_second_ratio=3., normal_scale_agreement_degrees=15.,
             normal_profile_range=[-8., 8.], normal_profile_step=.25,
             normal_crest_search_range=[-2., 2.], minimum_flank_contrast_noise_factor=4.,
             observed_interfaces='half prominence relative to higher of two flanking minima; optical only',
             maximum_tracking_steps=0, no_parameter_fallbacks=True)


def main():
    from prepare_next_validation import require_guard
    guard = require_guard()
    if OUT.exists():
        raise ValueError('Preserve existing local-branch diagnosis')
    OUT.mkdir()
    result = dict(schema='paris4-local-branches-v1', state='started', guard=guard,
                  rules=RULES, source_box_xyz=[LOW, HIGH], box_bounds='inclusive voxel centers',
                  source_origin_world_zyx=[1744, 2256, 4048], source_volume_id='20230205180739',
                  calibration_valid=False, winding_gate_ready=False, pitch_voxels=None,
                  branch_relation='unresolved', same_leaf_inferred=False, manual_labels_opened=False,
                  mask_used_for_measurements=False, result_meshes_opened=False,
                  inputs={}, branches=[],
                  limitations=['Unique CT crests and optical interfaces do not establish anatomical identity',
                               'No inter-slice tracking or joining; this diagnoses initial local ambiguity',
                               'Noise proxy and sampling brackets are not calibrated physical confidence intervals'])
    try:
        import numpy as np
        from PIL import Image, ImageDraw
        import inventory_paris4_radial_labels as inv
        inv.np = np
        for name, path, expected in [('CT', inv.CT, inv.CT_SHA), ('mask', inv.MASK, inv.MASK_SHA),
                                     ('calibration', inv.CAL, inv.CAL_SHA), ('axis', inv.AXIS, inv.AXIS_SHA),
                                     ('helpers', Path(inv.__file__), None), ('script', Path(__file__), None)]:
            digest = inv.sha256(path)
            inv.require(expected is None or digest == expected, name+' hash mismatch')
            result['inputs'][name] = dict(path=str(path), sha256=digest)
        cal = json.loads(inv.CAL.read_text())
        axis = np.loadtxt(inv.AXIS, delimiter=',', skiprows=1)
        inv.require(cal.get('axis_valid') is True and cal['source_sha256'] == inv.CT_SHA
                    and cal['coordinates'] == 'worldZYX' and cal['artifacts'][inv.AXIS.name] == inv.AXIS_SHA,
                    'Invalid prior axis/source evidence')
        inv.require(axis.shape == (146, 3) and np.array_equal(axis, np.asarray(cal['axis_zyx']))
                    and np.isfinite(axis).all() and np.all(np.diff(axis[:, 0]) > 0), 'Invalid axis points')
        inv.require(axis[0, 0] <= 1904 <= axis[-1, 0], 'Axis extrapolation forbidden')
        volume, header = inv.nrrd(inv.CT)
        crop = volume[112:176, 112:160, 144:192].copy()
        del volume
        mask, mask_header = inv.nrrd(inv.MASK)
        labels = mask[112:176, 112:160, 144:192].copy()
        del mask
        result['manual_labels_opened'] = True
        inv.require(header.get('space directions') == mask_header.get('space directions')
                    and header.get('space origin') == mask_header.get('space origin'), 'CT/mask axes mismatch')
        result['headers'] = dict(CT=header, mask=mask_header)
        divisor = 257 if crop.dtype.itemsize == 2 else 1
        lower, upper = np.asarray(LOW, float), np.asarray(HIGH, float)
        palette = np.asarray([inv.label_color(i) for i in range(int(labels.max())+1)], dtype='uint8')

        def inside(points, strict=False):
            return bool(np.all(points > lower) and np.all(points < upper)) if strict else bool(np.all(points >= lower) and np.all(points <= upper))

        def sample(points):
            points = np.asarray(points, float)
            inv.require(inside(points), 'Sampling would leave fixed box')
            local = points-lower
            base = np.minimum(np.floor(local).astype(int), np.asarray(crop.shape)-2)
            fraction = local-base
            values = np.zeros(points.shape[:-1], dtype=float)
            for dx in (0, 1):
                for dy in (0, 1):
                    for dz in (0, 1):
                        w = ((fraction[..., 0] if dx else 1-fraction[..., 0])
                             * (fraction[..., 1] if dy else 1-fraction[..., 1])
                             * (fraction[..., 2] if dz else 1-fraction[..., 2]))
                        values += w*crop[base[..., 0]+dx, base[..., 1]+dy, base[..., 2]+dz]
            return values/divisor

        def analyze_profile(coordinates, raw):
            step = float(coordinates[1]-coordinates[0])
            sigma = RULES['smoothing_sigma_voxels']/step
            half = int(math.ceil(4*sigma))
            grid = np.arange(-half, half+1)
            kernel = np.exp(-.5*(grid/sigma)**2)
            kernel /= kernel.sum()
            smooth = np.convolve(np.pad(raw, half, mode='reflect'), kernel, mode='valid')
            diff = np.diff(raw)
            noise = float(1.4826*np.median(np.abs(diff-np.median(diff)))/math.sqrt(2))
            threshold = max(RULES['prominence_noise_factor']*noise,
                            RULES['prominence_range_fraction']*float(np.ptp(smooth)))
            width = int(round(RULES['local_prominence_halfwidth_voxels']/step))
            peaks = []
            for i in np.where((smooth[1:-1] > smooth[:-2]) & (smooth[1:-1] >= smooth[2:]))[0]+1:
                if i < width or i+width >= len(smooth):
                    continue
                prominence = float(smooth[i]-max(smooth[i-width:i].min(), smooth[i+1:i+width+1].min()))
                peaks.append(dict(sample=int(i), coordinate=float(coordinates[i]),
                                  smoothed_intensity=float(smooth[i]), prominence=prominence,
                                  above_threshold=bool(prominence >= threshold)))
            return smooth, peaks, dict(noise_proxy=noise, prominence_threshold=threshold,
                                       noise_proxy_is_calibrated_sigma=False)

        def save_profile(name, coordinates, points, raw, smooth):
            with (OUT/(name+'.csv')).open('x', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(['coordinate_voxels', 'source_x', 'source_y', 'source_z', 'CT_8bit_equivalent', 'smoothed_CT'])
                writer.writerows(zip(coordinates, points[:, 0], points[:, 1], points[:, 2], raw, smooth))
            canvas = Image.new('RGB', (850, 310), '#161616')
            draw = ImageDraw.Draw(canvas)
            draw.text((10, 8), name+'; gray=raw, orange=smoothed; intensity range0..255 fixed', fill='white')
            for values, color in ((raw, '#aaaaaa'), (smooth, '#ffa850')):
                positions = [(45+760*(float(c)-coordinates[0])/(coordinates[-1]-coordinates[0]),
                              270-220*min(255, max(0, float(v)))/255) for c, v in zip(coordinates, values)]
                draw.line(positions, fill=color, width=1)
            for fraction in (0, .25, .5, .75, 1):
                draw.text((40+760*fraction, 282), f'{coordinates[0]+fraction*(coordinates[-1]-coordinates[0]):.2f}', fill='white')
            canvas.save(OUT/(name+'.png'))

        def save_linked_cuts(name, anchor, anchor_type):
            specs = [('XY', 0, 1, 2), ('YZ', 1, 2, 0), ('XZ', 0, 2, 1)]
            canvas = Image.new('RGB', (1000, 570), '#161616')
            draw = ImageDraw.Draw(canvas)
            draw.text((8, 7), name+'; exact linked source XYZ '+str([round(float(v), 3) for v in anchor]), fill='white')
            draw.text((8, 24), anchor_type+'; TOP raw CT; BOTTOM label overlay35%; zero label unknown', fill='white')
            for column, (plane, horizontal, vertical, fixed) in enumerate(specs):
                u = np.arange(LOW[horizontal], HIGH[horizontal]+1)
                v = np.arange(LOW[vertical], HIGH[vertical]+1)
                uu, vv = np.meshgrid(u, v)
                points = np.broadcast_to(anchor, uu.shape+(3,)).copy()
                points[..., horizontal], points[..., vertical] = uu, vv
                pixels = np.repeat(np.clip(sample(points), 0, 255).astype('uint8')[:, :, None], 3, axis=2)
                indices = np.floor(points-lower+.5).astype(int)
                lab = labels[indices[..., 0], indices[..., 1], indices[..., 2]]
                overlay = pixels.copy()
                sel = lab > 0
                overlay[sel] = (.65*pixels[sel]+.35*palette[lab[sel]]).astype('uint8')
                left = 10+column*330
                draw.text((left, 42), plane+f'; fixed {"XYZ"[fixed]}={anchor[fixed]:.3f}', fill='white')
                for image, top in ((pixels, 64), (overlay, 320)):
                    canvas.paste(Image.fromarray(image).resize((len(u)*4, len(v)*4), Image.Resampling.NEAREST), (left, top))
                    x, y = left+(anchor[horizontal]-u[0])*4, top+(anchor[vertical]-v[0])*4
                    draw.line((x-5, y, x+5, y), fill='#ffbb44')
                    draw.line((x, y-5, x, y+5), fill='#ffbb44')
            canvas.save(OUT/(name+'-linked-cuts.png'))

        def orientation(anchor):
            reports, normals = [], []
            for half, sigma in zip(RULES['tensor_halfwidths_voxels'], RULES['tensor_gaussian_sigmas']):
                grid = np.stack(np.meshgrid(*([np.arange(-half, half+1)]*3), indexing='ij'), axis=-1).reshape(-1, 3)
                points = anchor+grid
                inv.require(inside(points-1, strict=True) and inside(points+1, strict=True), 'Tensor support touches box limit')
                gradients = np.stack([(sample(points+np.eye(3)[i])-sample(points-np.eye(3)[i]))/2 for i in range(3)], axis=1)
                weights = np.exp(-np.sum(grid*grid, axis=1)/(2*sigma*sigma))
                tensor = (gradients.T*weights)@gradients/weights.sum()
                values, vectors = np.linalg.eigh(tensor)
                normal = vectors[:, -1]
                ratio = float(values[-1]/max(float(values[-2]), 1e-12))
                reports.append(dict(halfwidth=half, eigenvalues=values.tolist(), largest_second_ratio=ratio,
                                    normal_xyz=normal.tolist()))
                normals.append(normal)
            angle = math.degrees(math.acos(float(np.clip(abs(np.dot(normals[0], normals[1])), 0, 1))))
            ok = all(r['largest_second_ratio'] >= 3 and r['eigenvalues'][-1] > 1e-12 for r in reports) and angle <= 15
            return normals[-1], dict(scales=reports, normal_scale_difference_degrees=angle,
                                      orientation_valid_for_optical_profile=bool(ok), anatomical_normal_certified=False)

        z = 160.
        cy = float(np.interp(1744+z, axis[:, 0], axis[:, 1]))-2256
        cx = float(np.interp(1744+z, axis[:, 0], axis[:, 2]))-4048
        theta = math.atan2(128-cy, 128-cx)
        direction = np.array([math.cos(theta), math.sin(theta), 0.])
        axis_point = np.array([cx, cy, z])
        radius = np.arange(269., 320.001, .25)
        points = axis_point+radius[:, None]*direction
        raw = sample(points)
        smooth, peaks, evidence = analyze_profile(radius, raw)
        save_profile('seed-radial-profile', radius, points, raw, smooth)
        result['seed_profile'] = dict(theta_radians=theta, axis_source_xyz=axis_point.tolist(), peaks=peaks, **evidence)

        for name, lo, hi in WINDOWS:
            candidates = [p for p in peaks if lo <= p['coordinate'] <= hi and p['above_threshold']]
            branch = dict(name=name, frozen_window=[lo, hi], significant_seed_candidates=candidates,
                          state='inconclusive', stop_reasons=[], optical_interfaces=None,
                          branch_relation='unresolved', anatomical_identity_inferred=False)
            result['branches'].append(branch)
            unique = len(candidates) == 1
            coordinate = candidates[0]['coordinate'] if unique else (lo+hi)/2
            anchor = axis_point+coordinate*direction
            anchor_type = 'unique optical seed' if unique else 'window midpoint for context ONLY; not a seed'
            branch.update(anchor_source_xyz=anchor.tolist(), anchor_type=anchor_type)
            save_linked_cuts(name, anchor, anchor_type)
            if not unique:
                branch['stop_reasons'].append('seed_not_unique' if candidates else 'no_significant_seed_crest')
                continue
            if min(coordinate-lo, hi-coordinate) < RULES['seed_boundary_margin_voxels']:
                branch['stop_reasons'].append('seed_touches_frozen_window_margin')
                continue
            try:
                normal, tensor = orientation(anchor)
            except ValueError as error:
                branch['stop_reasons'].append(str(error))
                continue
            branch['orientation'] = tensor
            if not tensor['orientation_valid_for_optical_profile']:
                branch['stop_reasons'].append('normal_not_unique_or_not_stable_across_fixed_scales')
                continue
            if np.dot(normal, direction) < 0:
                normal = -normal
            t = np.arange(-8., 8.001, .25)
            normal_points = anchor+t[:, None]*normal
            if not inside(normal_points, strict=True):
                branch['stop_reasons'].append('normal_profile_touches_box_limit')
                continue
            normal_raw = sample(normal_points)
            normal_smooth, normal_peaks, normal_evidence = analyze_profile(t, normal_raw)
            save_profile(name+'-normal-profile', t, normal_points, normal_raw, normal_smooth)
            branch['normal_profile'] = dict(normal_xyz=normal.tolist(), peaks=normal_peaks, **normal_evidence)
            # An exact plane containing the same anchor, normal, and a tangent.
            tangent = np.array([0., 0., 1.])-normal*normal[2]
            if np.linalg.norm(tangent) < .1:
                tangent = np.array([0., 1., 0.])-normal*normal[1]
            tangent /= np.linalg.norm(tangent)
            a, b = np.meshgrid(t, t)
            plane_points = anchor+a[:, :, None]*normal+b[:, :, None]*tangent
            if inside(plane_points):
                pixels = np.clip(sample(plane_points), 0, 255).astype('uint8')
                canvas = Image.new('RGB', (400, 345), '#161616')
                canvas.paste(Image.fromarray(pixels).convert('RGB').resize((260, 260), Image.Resampling.NEAREST), (65, 55))
                draw = ImageDraw.Draw(canvas)
                draw.text((8, 8), name+' same-anchor normal/tangent CT plane', fill='white')
                draw.text((8, 26), 'Horizontal: normal -8..8; vertical: tangent -8..8', fill='white')
                draw.line((190, 185, 200, 185), fill='#ffbb44')
                draw.line((195, 180, 195, 190), fill='#ffbb44')
                canvas.save(OUT/(name+'-normal-plane.png'))
                branch['normal_plane'] = dict(normal_xyz=normal.tolist(), tangent_xyz=tangent.tolist(), extent=[-8, 8])
            else:
                branch['normal_plane'] = dict(not_rendered='fixed plane extent leaves box; no padding')
            central = [p for p in normal_peaks if -2 <= p['coordinate'] <= 2 and p['above_threshold']]
            if len(central) != 1:
                branch['stop_reasons'].append('normal_crest_not_unique_near_anchor')
                continue
            peak_index = central[0]['sample']
            left_indices, right_indices = np.where(t < -2)[0], np.where(t > 2)[0]
            li = int(left_indices[np.argmin(normal_smooth[left_indices])])
            ri = int(right_indices[np.argmin(normal_smooth[right_indices])])
            if li == 0 or ri == len(t)-1:
                branch['stop_reasons'].append('flanking_valley_not_contained_in_fixed_profile')
                continue
            baseline = max(float(normal_smooth[li]), float(normal_smooth[ri]))
            contrast = float(normal_smooth[peak_index]-baseline)
            branch['normal_profile'].update(flanking_minima_offsets=[float(t[li]), float(t[ri])], contrast=contrast)
            if contrast <= 0 or contrast < 4*normal_evidence['noise_proxy']:
                branch['stop_reasons'].append('insufficient_normal_flank_contrast')
                continue
            half_height = baseline+contrast/2
            left_crossings = [i for i in range(li, peak_index) if normal_smooth[i] <= half_height < normal_smooth[i+1]]
            right_crossings = [i for i in range(peak_index, ri) if normal_smooth[i] >= half_height > normal_smooth[i+1]]
            if len(left_crossings) != 1 or len(right_crossings) != 1:
                branch['stop_reasons'].append('optical_half_prominence_interfaces_not_unique')
                continue
            branch['optical_interfaces'] = dict(half_height=half_height,
                                                sample_brackets_normal_offsets=[[float(t[i]), float(t[i+1])] for i in (left_crossings[0], right_crossings[0])],
                                                physical_interfaces_certified=False,
                                                uncertainty='0.25-voxel sampling brackets plus unquantified smoothing/partial-volume/interface ambiguity')
            branch['state'] = 'local_optical_profile_characterized_not_anatomical_relation'
        result['state'] = 'completed-inconclusive-local-relation'
        result['stop_reason'] = 'Initial local diagnostic complete; no 3D branch joining or leaf-identity claim is authorized by optical profiles alone'
    except Exception as error:
        result['state'] = 'failed-closed'
        result['error'] = type(error).__name__+': '+str(error)
    from inventory_paris4_radial_labels import sha256
    result['artifacts'] = {p.name: sha256(p) for p in sorted(OUT.iterdir()) if p.is_file()}
    with (OUT/'diagnosis.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(OUT), state=result['state'], branch_relation='unresolved', pitch_voxels=None)), flush=True)
    return 2 if result['state'] == 'failed-closed' else 0


if __name__ == '__main__':
    raise SystemExit(main())
