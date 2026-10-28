"""Build a clean patched upstream and reproduce both saved real-data results."""
from pathlib import Path
import argparse,ctypes.util,gzip,hashlib,json,os,shutil,struct,subprocess,sys,urllib.request
from release_guard import require_guard
from bootstrap import digest
from exact_mesh_certificate import inspect_mesh

def main():
    guard=require_guard();package=Path(__file__).resolve().parent.parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--work',required=True,type=Path)
    p.add_argument('--volume',type=Path,help='Optional byte-verified public CT NRRD; otherwise downloaded.')
    p.add_argument('--tiff-library',type=Path,help='Optional installed libtiff runtime library.')
    p.add_argument('--check-inputs-only',action='store_true',help='Verify source, golden meshes and control fixture digests without rerunning the benchmark.')
    args=p.parse_args();source=args.source.resolve();work=args.work.resolve();work.mkdir(parents=True,exist_ok=False)
    spec=json.loads((package/'patches/series.json').read_text())
    expected=json.loads((package/'expected-results.json').read_text())
    for relative,sha in spec['final_sources'].items():assert digest(source/relative)==sha
    for name in ('v4-control','v5-recovery'):
        assert digest(package/expected[name]['mesh'])==expected[name]['sha256']
    control_sha=spec['patches'][1]['before']['src/split/overlap_sep.c']
    assert digest(package/'fixtures/overlap_sep.before-graft.c')==control_sha
    if args.check_inputs_only:
        result=dict(passed=True,guard=guard,scope='Source, golden mesh and before-graft fixture digests only; no repeated benchmark.')
        (work/'input-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
        return
    commands=[]
    def run(command,label,**kwargs):
        commands.append(dict(label=label,command=[str(x) for x in command]))
        (work/'commands.json').write_text(json.dumps(commands,indent=2))
        with (work/(label+'.log')).open('x') as log:
            subprocess.run([str(x) for x in command],stdout=log,stderr=subprocess.STDOUT,check=True,**kwargs)
        print(json.dumps(dict(completed=label)),flush=True)
    try:
        # Configure headers from the upstream's exact vendored TIFF source.
        # The library itself is supplied by the operating system, not this release.
        tiffsource=source/'deps/src/tiff-4.7.1'
        run(['cmake','-S',tiffsource,'-B',work/'tiff-config','-G','Ninja',
             '-Dtiff-tools=OFF','-Dtiff-tests=OFF','-Dtiff-contrib=OFF','-Dtiff-docs=OFF'],'configure-tiff')
        headers=work/'tiff-include';headers.mkdir()
        for name in ('tiff.h','tiffio.h','tiffvers.h','tiffconf.h'):
            candidates=[tiffsource/'libtiff'/name,work/'tiff-config/libtiff'/name]
            selected=next((path for path in candidates if path.is_file()),None)
            assert selected is not None,name
            shutil.copyfile(selected,headers/name)
        library=args.tiff_library
        if library is None:
            name=ctypes.util.find_library('tiff');assert name,'Install libtiff runtime/development package'
            candidates=[Path(folder)/name for folder in ('/lib64','/usr/lib64','/lib/x86_64-linux-gnu','/usr/lib/x86_64-linux-gnu')]
            library=next((path for path in candidates if path.is_file()),None)
        assert library and library.is_file(),'Specify --tiff-library /absolute/path/to/libtiff.so'
        build=work/'build'
        run(['cmake','-S',source,'-B',build,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
             '-DCMAKE_C_FLAGS_RELEASE=-O2 -DNDEBUG','-DCMAKE_CXX_FLAGS_RELEASE=-O2 -DNDEBUG',
             '-DSCROLLFIESTA_BUILD_TOOLS=ON','-DSCROLLFIESTA_BUILD_TESTS=OFF',
             '-DSCROLLFIESTA_WITH_TIFF=ON','-DSCROLLFIESTA_INSTALL=OFF',
             '-DTIFF_LIBRARY='+str(library),'-DTIFF_INCLUDE_DIR='+str(headers)],'configure')
        run(['cmake','--build',build,'--target','cube_mesh','--parallel','1'],'build')
        tests=package/'tools/test_boundary_graft.c'
        run(['cc','-O2','-std=gnu17','-ffunction-sections','-fdata-sections','-Wl,--gc-sections',
             '-I',source/'src',tests,source/'src/common/arena.c',source/'src/common/except.c',
             source/'src/common/csr.c','-lm','-o',work/'test-boundary-graft'],'build-graft-controls')
        run([work/'test-boundary-graft'],'graft-controls')
        import numpy as np
        data=json.loads((package/'public-data.json').read_text());entry=next(x for x in data['files'] if x['file'].endswith('_volume.nrrd'))
        volume=args.volume
        if volume is None:
            volume=work/entry['file']
            with urllib.request.urlopen(entry['url'],timeout=60) as response,volume.open('xb') as output:
                while block:=response.read(1024*1024):output.write(block)
        assert digest(volume)==entry['sha256']
        with volume.open('rb') as stream:
            lines=[]
            while line:=stream.readline():
                if not line.strip():break
                lines.append(line.decode().rstrip())
            fields=dict(line.split(': ',1) for line in lines if ': ' in line and not line.startswith('#'))
            assert fields['dimension']=='3' and fields['sizes']=='256 256 256'
            dtype={'unsigned char':'u1','uint8':'u1','unsigned short':'<u2','uint16':'<u2'}[fields['type']]
            count=256**3*np.dtype(dtype).itemsize
            assert fields['encoding'] in ('gzip','raw')
            payload=gzip.GzipFile(fileobj=stream).read(count+1) if fields['encoding']=='gzip' else stream.read(count+1)
            assert len(payload)==count
            ct=np.frombuffer(payload,dtype=dtype).reshape((256,256,256),order='F')
        raw=(ct[64:192,64:192,64:192].transpose(2,1,0)//(257 if ct.dtype.itemsize==2 else 1)).astype('uint8')
        window=raw[48:80,80:112,48:80]
        hist=np.bincount(window.ravel(),minlength=256).astype(float);prob=hist/hist.sum()
        weight=prob.cumsum();mean=(prob*np.arange(256)).cumsum();score=np.full(256,-np.inf)
        good=(weight>0)&(weight<1);score[good]=(mean[-1]*weight[good]-mean[good])**2/(weight[good]*(1-weight[good]))
        threshold=int(score.argmax());prediction=np.zeros_like(raw)
        prediction[48:80,80:112,48:80]=(window>threshold).astype('uint8')*255
        assert hashlib.sha256(prediction.tobytes()).hexdigest()==expected['prediction_raw_sha256']
        prediction_path=work/'prediction.raw';prediction_path.write_bytes(prediction.tobytes())
        np.save(work/'prediction.npy',prediction,allow_pickle=False)
        env=os.environ.copy()
        for key in ('MLS_RADIUS_VOX','MLS_PERTURB_EPS'):env.pop(key,None)
        env.update(MLS_EDGE_ADAPT='soft',VES_OVERLAP_COVERAGE_GUARD='1')
        reports={}
        def stage(folder,name):
            paths=list(folder.glob(f'*/*{name}/*_all.vmesh'));assert len(paths)==1,(folder,name)
            return paths[0]
        for name,flag,count in [('v4-control','0',5143),('v5-recovery','1',5160)]:
            env['VES_HOLE_RECOVERY_SEARCH']=flag;obj=work/(name+'-obj')
            with prediction_path.open('rb') as inp:
                run([build/'cube_mesh','--stdin-raw','128','1808','2320','4112',
                     '--dump-obj',obj,'--no-simplify'],name,stdin=inp,env=env)
            log=(work/(name+'.log')).read_text()
            assert 'Status: OK' in log and 'boundary recovery: 27 faces' in log
            guards=[line for line in log.splitlines() if 'Guard:' in line]
            assert guards and all('Guard: 0 NM-edge(s) (-0 faces), 0 pinch split(s), 0 reorient flip(s)' in line for line in guards)
            pre=stage(obj,'step7_cc_bpa');final=stage(obj,'step11_kibble')
            assert digest(pre)==expected['grafted_source_sha256']
            facts=inspect_mesh(final);gold=inspect_mesh(package/expected[name]['mesh'])
            assert facts.report['faces']==count and facts.oriented_faces==gold.oriented_faces
            assert facts.report['exact_duplicate_groups']==0 and facts.report['degenerate_faces']==0
            reports[name]=dict(source_sha256=digest(pre),final_sha256=digest(final),faces=count,
                exact_oriented_geometry_matches_frozen_result=True,final=str(final))
        run([sys.executable,package/'tools/exact_patch_intersections.py','--source',reports['v4-control']['final'],
             '--candidate',reports['v5-recovery']['final'],'--output',work/'v5-exact-patch.json'],'v5-exact')
        exact=json.loads((work/'v5-exact-patch.json').read_text());assert exact['passed'] and exact['added_faces']==17
        # A pre-graft control changes only overlap_sep.c. Restore it even on failure.
        overlap=source/'src/split/overlap_sep.c';saved=overlap.read_bytes()
        try:
            before=package/'fixtures/overlap_sep.before-graft.c';overlap.write_bytes(before.read_bytes())
            run(['cmake','--build',build,'--target','cube_mesh','--parallel','1'],'build-pre-graft-control')
            obj=work/'pre-graft-obj';env['VES_HOLE_RECOVERY_SEARCH']='0'
            with prediction_path.open('rb') as inp:
                run([build/'cube_mesh','--stdin-raw','128','1808','2320','4112','--dump-obj',obj,'--no-simplify'],
                    'pre-graft-control',stdin=inp,env=env)
            original=stage(obj,'step7_cc_bpa');assert digest(original)==expected['ungrafted_source_sha256']
            before_facts=inspect_mesh(original);after_facts=inspect_mesh(stage(work/'v5-recovery-obj','step7_cc_bpa'))
            assert not before_facts.oriented_faces-after_facts.oriented_faces
            assert sum((after_facts.oriented_faces-before_facts.oriented_faces).values())==27
            reports['graft']=dict(source_faces_retained=True,added_faces=27,control_sha256=digest(original))
        finally:overlap.write_bytes(saved)
        run(['cmake','--build',build,'--target','cube_mesh','--parallel','1'],'restore-v5-build')
        result=dict(passed=True,guard=guard,results=reports,threshold=threshold,
            upstream_commit=spec['upstream']['commit'],compiler_flags='C/C++ Release -O2 -DNDEBUG',
            numpy_version=np.__version__,exact_new_contact_pairs=exact['exact_pairs_checked'],
            exact_new_contacts=exact['conflicts'],scope='Fresh build and full real-data pipeline replay. Frozen metric reports reused only after exact oriented geometry equality. No anatomy or text claim.')
        (work/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
    except BaseException as exc:
        (work/'verification-failed.json').write_text(json.dumps(dict(passed=False,error=f'{type(exc).__name__}: {exc}',guard=guard),indent=2))
        raise

if __name__=='__main__':main()
