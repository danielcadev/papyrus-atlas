import argparse
from collections import Counter
import itertools
import json
from pathlib import Path
import resource
import numpy as np
from PIL import Image,ImageDraw
from guard import start_guard
from inspect_cube import read_nrrd

ROOT=Path(__file__).resolve().parent
NATIVE=ROOT/'native'


def local_zarr(path):
    a=np.empty((128,128,128),dtype=np.uint8)
    for z,y,x in itertools.product(range(4),repeat=3):
        data=np.fromfile(path/'0'/str(z)/str(y)/str(x),dtype=np.uint8).reshape(32,32,32)
        a[z*32:(z+1)*32,y*32:(y+1)*32,x*32:(x+1)*32]=data
    return a


def identities(labels,points,radius=2):
    rounded=np.rint(points).astype(int)
    offsets=sorted((p for p in itertools.product(range(-radius,radius+1),repeat=3)
                    if sum(x*x for x in p)<=radius**2),key=lambda x:sum(v*v for v in x))
    found=np.zeros(len(points),dtype=np.uint16)
    for offset in offsets:
        pos=rounded+offset
        valid=np.all((pos>=0)&(pos<256),axis=1)&(found==0)
        idx=np.flatnonzero(valid)
        if len(idx):found[idx]=labels[tuple(pos[idx].T)]
    return found


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='grow-output-step2')
    parser.add_argument('--name',default='native-evaluation')
    parser.add_argument('--prediction',default='prediction-old-frame.zarr')
    parser.add_argument('--new-after-generation',type=int)
    parser.add_argument('--support',help='Independent local foreground used only to assess mesh support')
    args=parser.parse_args()
    start_guard()
    out=NATIVE/args.output
    coordinates=np.stack([np.asarray(Image.open(out/f'{axis}.tif'),dtype=np.float32) for axis in 'xyz'],axis=-1)
    valid=np.all(np.isfinite(coordinates)&(coordinates>=0),axis=-1)
    points=coordinates[valid]
    original_reference_point=np.array([53,56,32])
    reference_distances=np.linalg.norm(points-original_reference_point,axis=1)
    generations=np.asarray(Image.open(out/'generations.tif'))
    seed_points=coordinates[valid&(generations==1)]
    labels,_=read_nrrd(ROOT/'data/00768_02408_03536_mask.nrrd')
    assert json.loads((NATIVE/'prepared-input.json').read_text())['native_to_zyx']==[2,1,0]
    # Verified NRRD native axes are XYZ, so native label lookup uses XYZ directly.
    ids=identities(labels,points)
    band=(points[:,0]>=48)&(points[:,0]<59)&(points[:,2]>=24)&(points[:,2]<41)
    local_failure_roi=band&(points[:,1]>=40)&(points[:,1]<112)
    prediction=local_zarr(NATIVE/args.prediction)
    foreground=np.argwhere(prediction>0)
    seed_zyx=np.array([32,104,16])
    distances=np.sum((foreground-seed_zyx)**2,axis=1)
    nearest=foreground[int(np.argmin(distances))]
    result=dict(output=args.output,prediction=args.prediction,valid_vertices=len(points),grid_shape=list(valid.shape),
                bounds_xyz=[points.min(axis=0).tolist(),points.max(axis=0).tolist()],
                nearest_reference_instance_counts={str(k):v for k,v in sorted(Counter(map(int,ids)).items())},
                expected_instance=390,expected_fraction=float(np.mean(ids==390)),
                unlabelled_fraction=float(np.mean(ids==0)),
                foreign_labelled_fraction=float(np.mean((ids!=390)&(ids!=0))),
                reaches_failure_band=bool(band.any()),vertices_in_failure_band=int(band.sum()),
                failure_band_reference_counts={str(k):v for k,v in sorted(Counter(map(int,ids[band])).items())},
                original_local_failure_roi_xyz=[[48,59],[40,112],[24,41]],
                reaches_original_local_failure_roi=bool(local_failure_roi.any()),
                vertices_in_original_local_failure_roi=int(local_failure_roi.sum()),
                original_local_failure_roi_reference_counts={str(k):v for k,v in sorted(Counter(map(int,ids[local_failure_roi])).items())},
                original_reference_point_xyz=original_reference_point.tolist(),
                nearest_original_reference_distance=float(reference_distances.min()),
                nearest_original_reference_mesh_xyz=points[reference_distances.argmin()].tolist(),
                seed_prediction_value=int(prediction[tuple(seed_zyx)]),
                nearest_predicted_seed_distance=float(np.sqrt(distances.min())),
                nearest_predicted_seed_xyz=nearest[::-1].tolist(),
                nearest_predicted_seed_reference_id=int(labels[tuple(nearest[::-1])]),
                initial_generation_vertex_count=len(seed_points),
                initial_generation_center_xyz=seed_points.mean(axis=0).tolist() if len(seed_points) else None,
                initial_generation_center_seed_distance=float(np.linalg.norm(seed_points.mean(axis=0)-np.array([16,104,32]))) if len(seed_points) else None,
                nearest_mesh_vertex_seed_distance=float(np.linalg.norm(points-np.array([16,104,32]),axis=1).min()),
                production_binary_executed=True,manual_ids_used_only_for_evaluation=True,
                limitation='3-D vertex fractions differ from earlier 2-D trajectory counts; the inputs also differ.',
                max_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    if not local_failure_roi.any():
        result['conclusion']='Inconclusive for the original jump: no vertices in the original local 3-D failure ROI. Reaching only its X/Z band is insufficient.'
    elif result['foreign_labelled_fraction']>0:
        result['conclusion']='Foreign annotated instances are present; not a demonstrated clean continuation.'
    else:
        result['conclusion']='Reaches band without detected foreign annotated vertices; limited to this input/ROI.'
    if args.new_after_generation is not None:
        new=generations[valid]>args.new_after_generation
        result['new_vertices_evaluation']=dict(after_generation=args.new_after_generation,
            vertices=int(new.sum()),reference_counts={str(k):v for k,v in sorted(Counter(map(int,ids[new])).items())},
            failure_band_vertices=int(np.sum(new&band)),
            failure_band_reference_counts={str(k):v for k,v in sorted(Counter(map(int,ids[new&band])).items())})
    if args.support:
        support=local_zarr(NATIVE/args.support)>0
        rounded=np.rint(points).astype(int)
        supported=np.zeros(len(points),dtype=bool)
        for delta in itertools.product(range(-2,3),repeat=3):
            if sum(v*v for v in delta)>4:continue
            sample=rounded+delta
            good=np.all((sample>=0)&(sample<128),axis=1)
            ix=np.flatnonzero(good)
            supported[ix]|=support[tuple(sample[ix,::-1].T)]
        result['foreground_support_radius2']=dict(source=args.support,
            supported_vertices=int(supported.sum()),fraction=float(supported.mean()),
            original_local_roi_supported_vertices=int(np.sum(supported&local_failure_roi)))
    (NATIVE/(args.name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    # Standalone CT/prediction/mesh overlay at the original failed Z section.
    ct=local_zarr(NATIVE/'ct-old-frame.zarr')
    gray=ct[32].astype(float)
    lo,hi=np.percentile(gray,[2,98])
    gray=np.clip((gray-lo)/max(hi-lo,1)*255,0,255).astype(np.uint8)
    canvas=Image.new('RGB',(800,460),'#121a22')
    draw=ImageDraw.Draw(canvas)
    plane_label=labels[:128,:128,32].T
    for panel in range(2):
        rgb=np.repeat(gray[:,:,None],3,axis=2)
        if panel==0:
            m=prediction[32]>0
            rgb[m]=(rgb[m].astype(np.uint16)+np.array([255,70,180]))//2
        else:
            for identity,color in [(390,[65,180,245]),(394,[245,137,60])]:
                m=plane_label==identity
                rgb[m]=(rgb[m].astype(np.uint16)+np.asarray(color))//2
        pic=Image.fromarray(rgb)
        d=ImageDraw.Draw(pic)
        near=points[np.abs(points[:,2]-32)<=2]
        for x,y,z in near:d.ellipse((x-0.7,y-0.7,x+0.7,y+0.7),fill='#39ff55')
        d.rectangle((48,40,58,112),outline='red')
        d.ellipse((14,102,18,106),outline='yellow')
        canvas.paste(pic.resize((384,384)),(8+panel*400,35))
    draw.text((10,10),'CT + tracer input foreground (pink)',fill='white')
    draw.text((410,10),'CT + manual reference: blue 390 / orange 394',fill='white')
    draw.text((10,430),'Green: GrowPatch vertices near Z=32; yellow: seed; red: X band of the original switch',fill='white')
    canvas.save(NATIVE/(args.name+'.png'))
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
