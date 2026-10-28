"""Replay saved raw-CT controls with the standard library; no registration fitting."""
import argparse
import array
import ast
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from release_guard import require_guard


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def load_array(path):
    with path.open('rb') as stream:
        assert stream.read(6)==b'\x93NUMPY'
        version=stream.read(2)
        assert version in (b'\x01\x00',b'\x02\x00')
        size=struct.unpack('<H' if version[0]==1 else '<I',stream.read(2 if version[0]==1 else 4))[0]
        assert size<65536
        header=ast.literal_eval(stream.read(size).decode('latin1'))
        assert not header['fortran_order']
        payload=stream.read()
    dtype=header['descr'];shape=header['shape']
    assert dtype in ('|u1','<f4') and sys.byteorder=='little'
    values=array.array('B' if dtype=='|u1' else 'f');values.frombytes(payload)
    assert len(values)==math.prod(shape)
    return shape,values


def corr(a,b):
    ma=sum(a)/len(a);mb=sum(b)/len(b)
    a=[x-ma for x in a];b=[x-mb for x in b]
    return sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    args=parser.parse_args();guard=require_guard();assert guard['memory_max']<=384*1024**2
    out=args.output.resolve();out.mkdir(exist_ok=False)
    base=Path(__file__).resolve().parent
    shape,target=load_array(base/'old-native-validation-zyx.npy');assert shape==(32,32,32)
    results=[]
    for name in ('paris4-exterior-collar-v1','paris4-exterior-gradient-support-v2'):
        folder=base/'trials'/name;result=json.loads((folder/'result.json').read_text())
        for relative,expected in result['artifacts'].items():assert sha(folder/relative)==expected
        shape,volume=load_array(folder/'modern-footprint-corrected-affine-native-zyx.npy');assert shape==(40,40,40)
        controls={}
        for shift in ((0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4)):
            b=[volume[((i+4+shift[0])*40+j+4+shift[1])*40+k+4+shift[2]]
               for i in range(32) for j in range(32) for k in range(32)]
            key='_'.join(map(str,shift));value=corr(target,b)
            assert abs(value-result['pearson_by_control_native_zyx'][key])<1e-10
            controls[key]=value
        p=controls['0_0_0'];margin=p-max(v for k,v in controls.items() if k!='0_0_0')
        x=result['fit']['parameters'];boundary=any(abs(v)>=3.9999 for v in x[:3]) or any(abs(v)>=.009999 for v in x[3:])
        passed=p>=.6 and margin>=.1 and not boundary
        assert passed==result['diagnostic_structural_coherence_gate_passed']
        assert not passed
        results.append(dict(trial=name,primary_pearson=p,margin=margin,gate_passed=passed))
    receipt=dict(guard=guard,passed=True,checks=results,scope='Saved CT correlations and gates only; not fitting, raw scan sampling, anatomy or ink.',
        target_sha256=sha(base/'old-native-validation-zyx.npy'),ink_used=False,letters_verified=0)
    (out/'result.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)


if __name__=='__main__':main()
