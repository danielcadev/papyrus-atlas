"""Render fixed-window orthogonal CT comparison; no ink visualization."""
from pathlib import Path
import json
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
import numpy as np
from PIL import Image,ImageDraw
from inspect_cube import read_nrrd
root=Path(__file__).resolve().parent;out=root/'paris4-structural-context-v1';out.mkdir(exist_ok=False)
old,_=read_nrrd(root/'data/01744_02256_04048_volume.nrrd');old=old[84:172,116:204,84:172]
modern=np.load(root/'paris4-registration-anchors-v1/corrected-footprint-fit-v1/modern-footprint-grid-native-zyx.npy')
canvas=Image.new('RGB',(1110,1110),'#151922');draw=ImageDraw.Draw(canvas)
headers=['Old CT (54 keV)','Modern nominal footprint (78 keV)','Old red / modern cyan']
for c,label in enumerate(headers):draw.text((c*370+16,15),label,fill='white')
for axis,name in enumerate(('native Z','native Y','native X')):
    a=np.take(old,44,axis=axis);b=np.take(modern,44,axis=axis)
    rgb=np.stack((a,b,b),axis=-1).clip(0,255).astype(np.uint8)
    for c,array in enumerate((a,b,rgb)):
        array=np.clip(array,0,255).astype(np.uint8)
        im=Image.fromarray(array).convert('RGB').resize((352,352),Image.Resampling.NEAREST)
        canvas.paste(im,(c*370+8,axis*352+42));draw.text((c*370+12,axis*352+46),name,fill='#ffdc6b')
canvas.save(out/'ct-orthogonal-context.png')
(out/'receipt.json').write_text(json.dumps(dict(guard=guard,axes='native old-volume ZYX',native_center=[128,160,128],window=[0,255],scale='Nearest display only; source intensities unchanged.',
    no_ink_or_letters=True,registration_accepted=False,image_sha256=digest(out/'ct-orthogonal-context.png')),indent=2)+'\n')
print(str(out/'ct-orthogonal-context.png'),flush=True)
