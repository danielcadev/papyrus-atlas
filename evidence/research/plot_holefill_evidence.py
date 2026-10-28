"""Measured saved-geometry illustration, with registered real CT context."""
from pathlib import Path
from collections import Counter
import struct,json,hashlib
import numpy as np
from guard import start_guard
start_guard()
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
p=Path(__file__).resolve().parent;b=p/'scrollfiesta-comparison';d=b/'holefill-repair-v4'
out=d/'holefill-ct-evidence-v2.png';assert not out.exists()
def read(folder,stage):
    paths=list(folder.glob(f'*/*{stage}/*_all.vmesh'));assert len(paths)==1
    path=paths[0];data=path.read_bytes();h=struct.unpack('<8sIIIIQQQQQ',data[:64])
    v=np.frombuffer(data,dtype='<f4',count=h[5]*3,offset=h[7]).reshape(-1,3)
    f=np.frombuffer(data,dtype='<i4',count=h[6]*3,offset=h[9]).reshape(-1,3)
    return ((v-[1808,2320,4112])[:,::-1])[f],path
source,sp=read(d/'y32-obj','step7_cc_bpa')
before,bp=read(b/'fresh-yplus32-v2/corrected-obj','step11_kibble')
after,ap=read(d/'y32-obj','step11_kibble')
def key(t):return tuple(sorted(map(tuple,t)))
sourcekeys=set(map(key,source));afterkeys=set(map(key,after));counts=Counter(map(key,before))
dup=[t for t in before if counts[key(t)]>1];assert len(dup)==2
removed=np.array([t for t in before if key(t) not in afterkeys]);assert len(removed)==17
center=np.mean(dup[0],axis=0)
low=np.array([57,92,49]);high=np.array([68,100,57])
near=((source>=low)&(source<=high)).all(2).any(1)
local=source[near]
fig=plt.figure(figsize=(17,5.7))
fig.subplots_adjust(left=.02,right=.98,wspace=.25,top=.83,bottom=.19)
for col,(title,show_removed) in enumerate([('v2: relleno con duplicado',True),('v4: fuente conservada; ciclo abierto',False)]):
    ax=fig.add_subplot(1,3,col+1,projection='3d',computed_zorder=False)
    ax.add_collection3d(Poly3DCollection(local,facecolors='#98aab8',edgecolors='#607789',linewidths=.25,alpha=.38,zorder=1))
    if show_removed:
        ax.add_collection3d(Poly3DCollection(removed,facecolors='#e7b048',edgecolors='#7d5c1e',linewidths=.6,alpha=.8,zorder=2))
        ax.add_collection3d(Poly3DCollection(dup,facecolors='#ce313d',edgecolors='#96051a',linewidths=1.5,alpha=1,zorder=3))
        outline=np.vstack([dup[0],dup[0][0]])
        ax.plot(*outline.T,color='#ce313d',linewidth=2.2,zorder=4)
    else:
        loop=np.vstack([dup[0],dup[0][0]])
        ax.plot(*loop.T,color='#ce313d',linewidth=1.2,linestyle='--')
    ax.set(xlim=(low[0],high[0]),ylim=(low[1],high[1]),zlim=(low[2],high[2]),
           xlabel='X (vóxel)',ylabel='Y',zlabel='Z',title=title)
    ax.view_init(elev=28,azim=-63);ax.set_box_aspect(high-low)
    ax.set_zticks([50,52,54,56]);ax.tick_params(labelsize=8)
rawpath=b/'fresh-yplus32-v2/raw.npy';raw=np.load(rawpath,mmap_mode='r');assert raw.shape==(128,128,128)
ax=fig.add_subplot(1,3,3)
ax.imshow(raw[52,91:102,56:70],cmap='gray',vmin=0,vmax=255,origin='lower',
          extent=(55.5,69.5,90.5,101.5),interpolation='nearest')
ax.scatter([center[0]],[center[1]],s=180,facecolors='none',edgecolors='#ff5b61',linewidths=1.4)
ax.set(xlabel='X (vóxel)',ylabel='Y (vóxel)',title='CT real: corte Z=52; centro proyectado')
fig.suptitle('PHercParis4 · ventana +32Y · evidencia local de la reparación',fontsize=15)
fig.supxlabel('Gris: superficie fuente. Ocre: 17 caras de la propuesta rechazada. Rojo: par coincidente (área individual 0,210723 vóxel²).\n'
               'El CT aporta contexto registrado; esta figura no certifica identidad de hoja. La línea discontinua marca la ubicación previa.',fontsize=9)
fig.savefig(out,dpi=160);plt.close(fig)
record=dict(image=str(out),inputs={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [sp,bp,ap,rawpath]},
            coordinates='parent native XYZ, origin global ZYX [1808,2320,4112]',
            ct_z_slice=52,duplicate_centroid_xyz=center.tolist(),removed_generated_faces=17,
            source_faces_in_local_view=len(local),image_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
            limitation='Registered CT context and saved float32 meshes, not a fiber-following or sheet-identity certificate')
(d/'holefill-ct-evidence-v2.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
