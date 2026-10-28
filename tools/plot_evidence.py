"""Render English before/after views from unchanged recorded binary32 meshes."""
from pathlib import Path
from collections import Counter
import argparse,json,os,struct,sys,tempfile
from release_guard import require_guard
from bootstrap import digest

def main():
    require_guard();package=Path(__file__).resolve().parent.parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--dependency-dir',type=Path,help='Optional existing Python module directory; not bundled.')
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    if args.dependency_dir:sys.path.insert(0,str(args.dependency_dir))
    cache=tempfile.TemporaryDirectory(prefix='vesuvius-release-plot-')
    os.environ['MPLCONFIGDIR']=cache.name
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    base=package/'evidence/research/scrollfiesta-comparison'
    def stage(folder,name):
        files=list(folder.glob(f'*/*{name}/*_all.vmesh'));assert len(files)==1;return files[0]
    def read(path):
        with path.open('rb') as stream:
            h=struct.unpack('<8sIIIIQQQQQ',stream.read(64))
            v=np.frombuffer(stream.read(h[5]*12),'<f4').reshape(-1,3).astype(float)
            stream.seek(h[9]);f=np.frombuffer(stream.read(h[6]*12),'<i4').reshape(-1,3)
        return (v-[1808,2320,4112])[:,::-1][f]
    pairs=[('Boundary grafting',stage(base/'fresh-yplus32-v2/control-obj','step7_cc_bpa'),
            stage(base/'hole-recovery-v5/full-y32-01-obj','step7_cc_bpa'),27,'#d58212'),
           ('Hole recovery',stage(base/'holefill-repair-v4/y32-obj','step11_kibble'),
            stage(base/'hole-recovery-v5/full-y32-01-obj','step11_kibble'),17,'#147d72')]
    fig=plt.figure(figsize=(12,12),facecolor='white');inputs={}
    def key(tri):return tuple(sorted(map(tuple,tri)))
    for row,(label,before_path,after_path,count,color) in enumerate(pairs):
        before,after=read(before_path),read(after_path)
        remaining=Counter(map(key,before));added=[]
        for tri in after:
            k=key(tri)
            if remaining[k]:remaining[k]-=1
            else:added.append(tri)
        assert not +remaining and len(added)==count
        added=np.asarray(added);low=added.min(axis=(0,1))-1.2;high=added.max(axis=(0,1))+1.2
        for col,triangles in enumerate((before,after)):
            ax=fig.add_subplot(2,2,row*2+col+1,projection='3d',computed_zorder=False)
            near=np.all((triangles.max(1)>=low)&(triangles.min(1)<=high),axis=1)
            ax.add_collection3d(Poly3DCollection(triangles[near],facecolors='#aac0cd',edgecolors='#637d8c',
                linewidths=.22,alpha=.42,zorder=1))
            if col:ax.add_collection3d(Poly3DCollection(added,facecolors=color,edgecolors=color,linewidths=.6,alpha=.96,zorder=2))
            ax.set(xlim=(low[0],high[0]),ylim=(low[1],high[1]),zlim=(low[2],high[2]),
                xlabel='Local X (voxel)',ylabel='Local Y',zlabel='Local Z',
                title=f'{label}: {"after" if col else "before"}\n{len(triangles):,} total faces'+(f' | +{count} highlighted' if col else ''))
            ax.view_init(elev=28,azim=-63);ax.set_box_aspect(high-low);ax.tick_params(labelsize=8)
        inputs[str(before_path.relative_to(package))]=digest(before_path)
        inputs[str(after_path.relative_to(package))]=digest(after_path)
    fig.suptitle('Source preservation and complete hole recovery',fontsize=17,y=.98)
    fig.text(.5,.03,'Stored meshes, common camera and coordinates within each row. Grey: retained geometry.\n'
             'Highlighted: 27 recovered source faces / 17 added hole faces. Geometry evidence; no text or anatomical claim.',
             ha='center',fontsize=10)
    fig.subplots_adjust(left=.01,right=.97,bottom=.12,top=.91,wspace=.06,hspace=.55)
    image=args.output/'before-after.png';fig.savefig(image,dpi=170);plt.close(fig);cache.cleanup()
    record=dict(inputs=inputs,image_sha256=digest(image),matplotlib_version=matplotlib.__version__,
        coordinates='Local XYZ from stored global ZYX minus origin [1808,2320,4112]',
        camera=dict(elevation=28,azimuth=-63),scope='Measured geometry illustration only; no CT, ink or anatomical inference.')
    (args.output/'provenance.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)

if __name__=='__main__':main()
