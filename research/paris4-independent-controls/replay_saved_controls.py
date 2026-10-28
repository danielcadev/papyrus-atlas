"""Offline standard-library replay of saved CT controls, not anatomy or fitting."""
import argparse,array,ast,hashlib,json,math,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from release_guard import require_guard

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def load(path):
    with path.open('rb') as stream:
        assert stream.read(6)==b'\x93NUMPY';v=stream.read(2);assert v in (b'\x01\x00',b'\x02\x00')
        n=struct.unpack('<H' if v[0]==1 else '<I',stream.read(2 if v[0]==1 else 4))[0];assert n<65536
        header=ast.literal_eval(stream.read(n).decode('latin1'));assert not header['fortran_order']
        assert header['descr'] in ('|u1','<f4') and sys.byteorder=='little'
        a=array.array('B' if header['descr']=='|u1' else 'f');a.frombytes(stream.read())
        assert len(a)==math.prod(header['shape']);return header['shape'],a

def corr(a,b):
    ma=sum(a)/len(a);mb=sum(b)/len(b);a=[v-ma for v in a];b=[v-mb for v in b]
    return sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    args=parser.parse_args();guard=require_guard();assert guard['memory_max']<=384*1024**2
    args.output.mkdir(exist_ok=False);base=Path(__file__).resolve().parent;checks=[]
    for n in (1,2):
        trial=base/'trials'/f'paris4-independent-controls-v{n}';r=json.loads((trial/'result.json').read_text());passed=[]
        for relative,expected in r['artifacts'].items():assert sha(trial/relative)==expected
        for group in ('new_reserved_control','original_repaired_ROI'):
            shape,a=load(trial/(group+'-old-target.npy'));vshape,b=load(trial/(group+'-modern-footprint.npy'))
            assert vshape==tuple(i+8 for i in shape);values={}
            for s in ((0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4)):
                q=[b[((i+4+s[0])*vshape[1]+j+4+s[1])*vshape[2]+k+4+s[2]]
                   for i in range(shape[0]) for j in range(shape[1]) for k in range(shape[2])]
                key='_'.join(map(str,s));values[key]=corr(a,q)
                assert abs(values[key]-r['validation'][group]['controls_native_zyx'][key])<1e-10
            p=values['0_0_0'];margin=p-max(v for k,v in values.items() if k!='0_0_0');ok=p>=.6 and margin>=.1
            assert ok==r['validation'][group]['gate_passed'] and not ok;passed.append(ok)
            checks.append(dict(trial=trial.name,group=group,primary_pearson=p,margin=margin,gate_passed=ok))
        fit=r['global_fit'];x=fit['parameters']
        boundary=any(abs(v)>=1.99999 for v in x[:3]) or any(abs(v)>=.00999 for v in x[3:])
        assert boundary==fit['at_parameter_boundary']
        accepted=all(passed) and not boundary and fit['converged'];assert accepted==r['registration_accepted'] and not accepted
    result=dict(guard=guard,passed=True,checks=checks,registration_accepted=False,letters_verified=0,
        scope='Saved arrays, raw CT correlations and fixed gates only. Not fitting, source scan sampling, anatomical point truth or ink.')
    (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
