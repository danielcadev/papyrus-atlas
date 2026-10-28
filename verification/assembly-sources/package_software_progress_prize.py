"""Assemble a patch-only software submission and preserve evidence provenance."""
from pathlib import Path
import ast,difflib,hashlib,json,shutil,tarfile
from ink_guard import require_guard
guard=require_guard();assert guard['memory_max']<=384*1024**2
import numpy as np
root=Path(__file__).resolve().parent;project=root.parent;base=root/'scrollfiesta-comparison'
dest=project/'releases/software-progress-prize-2026-10-v1';dest.mkdir(parents=True,exist_ok=False)
def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def put(relative,data):
    target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(data if isinstance(data,bytes) else data.encode())
def jput(relative,value):put(relative,json.dumps(value,indent=2)+'\n')
archive_info=json.loads((base/'source-manifest.json').read_text())
assert digest(base/'source.tar.gz')==archive_info['sha256']
needed=('src/common/mls_project.c','src/pipeline/pipeline_cube.c','src/split/overlap_sep.c','src/holefill/hole_fill.c')
with tarfile.open(base/'source.tar.gz','r:gz') as archive:
    prefix=archive.getmembers()[0].name.split('/')[0]+'/'
    original={name:archive.extractfile(prefix+name).read() for name in needed}
    original_license=archive.extractfile(prefix+'LICENSE').read()
    cmake=archive.extractfile(prefix+'CMakeLists.txt').read()
state=original.copy();stages=[]
def patch_stage(filename,updates):
    before={};after={};parts=[]
    for name,new in updates.items():
        old=state.get(name,b'');before[name]=sha(old) if name in state else None;after[name]=sha(new)
        parts.append(''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),
            fromfile='a/'+name if name in state else '/dev/null',tofile='b/'+name)))
        state[name]=new
    data=''.join(parts).encode();assert data
    put('patches/'+filename,data);stages.append(dict(file=filename,sha256=sha(data),before=before,after=after))
patch_stage('0001-experimental-baseline.patch',{
 'src/common/mls_project.c':(base/'source/src/common/mls_project.c').read_bytes(),
 'src/pipeline/pipeline_cube.c':(base/'source/src/pipeline/pipeline_cube.c').read_bytes(),
 'src/split/overlap_sep.c':(base/'overlap_sep.before-boundary-graft.c').read_bytes()})
patch_stage('0002-boundary-grafting-v2.patch',{'src/split/overlap_sep.c':(base/'source/src/split/overlap_sep.c').read_bytes()})
patch_stage('0003-holefill-duplicate-v4.patch',{'src/holefill/hole_fill.c':(base/'hole-recovery-v5/hole_fill.v4.c').read_bytes()})
patch_stage('0004-bounded-hole-recovery-v5.patch',{
 'src/holefill/hole_fill.c':(base/'hole-recovery-v5/source-v5/hole_fill.c').read_bytes(),
 'src/holefill/hole_recovery_search.inc':(base/'hole-recovery-v5/source-v5/hole_recovery_search.inc').read_bytes()})
upstream={key:archive_info[key] for key in ('repository','commit','url','sha256','compressed_bytes')}
jput('patches/series.json',dict(upstream=upstream,patches=stages,
 final_sources={**{name:sha(data) for name,data in state.items()},'CMakeLists.txt':sha(cmake)},
 scope='Pinned experimental baseline dependencies, boundary grafting v2 and hole recovery v5 only; later v6 exact-contact changes excluded.'))
put('LICENSES/ScrollFiesta-MIT.txt',original_license)
put('fixtures/overlap_sep.before-graft.c',(base/'overlap_sep.before-boundary-graft.c').read_bytes())
put('public-data.json',(root/'data/manifest.json').read_bytes())
for path in sorted((root/'software_release_templates').glob('*')):
    if path.is_file():put('tools/'+path.name,path.read_bytes())
for name in ('guard.py','test_boundary_graft.c','exact_mesh_certificate.py','exact_patch_intersections.py','saved_geometry_audit.c'):
    put('tools/'+name,(root/name).read_bytes())
runner=(root/'run_native_guarded.py').read_text().replace("root=Path(__file__).resolve().parent/'native'", "root=Path(os.environ.get('VES_RELEASE_LOG_DIR',str(Path(__file__).resolve().parent/'native')));root.mkdir(parents=True,exist_ok=True)")
put('tools/run_native_guarded.py',runner)
# Archive historical evidence verbatim. Original raw data and non-redistributable
# executables remain local; their byte identities and retrieval source are recorded.
manifest_path=base/'hole-recovery-v5/evidence-manifest-v1.json'
old_manifest=json.loads(manifest_path.read_text());paths={project/entry['path'] for entry in old_manifest['files']}
paths.add(manifest_path)
for folder in ('fresh-yplus32-v2','holefill-repair','holefill-repair-v4','independent-central32','independent-xplus32','boundary-graft-soft-obj'):
    paths.update(path for path in (base/folder).rglob('*') if path.is_file())
for pattern in ('boundary-graft-*','split-ownership-*','split-coverage-*','mls-edge-*.patch'):
    paths.update(path for path in base.glob(pattern) if path.is_file())
for pattern in ('boundary-graft-*','hf-full-*','hf-recovery-*','ves-v5-evidence-*'):
    paths.update(path for path in (root/'native').glob(pattern) if path.is_file())
for name in ('BOUNDARY_GRAFT_REPORT.md','HOLEFILL_DUPLICATE_REPORT.md','SPLIT_OWNERSHIP_REPORT.md','MLS_EDGE_REPORT.md','HALO_VALIDATION_REPORT.md'):
    paths.add(base/name)
for pattern in ('*boundary_graft*.py','*hole_recovery*.py','*holefill*.py','test_boundary_graft.c','test_holefill_duplicate.c',
                'independent_split_common.py','evaluate_independent_split_crop.py','evaluate_saved_hole_candidate.py','inspect_cube.py'):
    paths.update(path for path in root.glob(pattern) if path.is_file())
# Include project-local Python helper imports used by archived evaluators.
pending=[path for path in paths if path.suffix=='.py']
while pending:
    path=pending.pop()
    for node in ast.walk(ast.parse(path.read_text())):
        names=[node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module else [alias.name.split('.')[0] for alias in node.names] if isinstance(node,ast.Import) else []
        for name in names:
            local=root/(name+'.py')
            if local.is_file() and local not in paths:paths.add(local);pending.append(local)
excluded=[];copied=[];drift=[]
old_expected={entry['path']:entry for entry in old_manifest['files']}
for path in sorted(paths):
    relative=str(path.relative_to(project));record=dict(path=relative)
    if not path.is_file():excluded.append(dict(**record,reason='Historical path no longer exists'));continue
    actual=digest(path);record.update(bytes=path.stat().st_size,sha256=actual)
    if relative in old_expected and actual!=old_expected[relative]['sha256']:
        drift.append(dict(**record,historical_sha256=old_expected[relative]['sha256']))
    with path.open('rb') as stream:magic=stream.read(4)
    reason=None
    if magic==b'\x7fELF' or magic[:2]==b'MZ':reason='Compiled upstream/dependency executable; retrieve upstream and build locally'
    elif path.suffix.lower() in ('.nrrd','.tif','.tiff','.npy'):reason='Raw/array data not relicensed or bundled; retain locally with digest and public-data retrieval recipe'
    if reason:excluded.append(dict(**record,reason=reason));continue
    target=dest/'evidence'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    assert digest(target)==actual;copied.append(record)
jput('evidence-index.json',dict(copied=copied,external_or_omitted=excluded,historical_manifest_drift=drift,
 historic_manifest_sha256=digest(manifest_path),
 scope='Relevant local histories, controls, successful/failed outputs and source snapshots. Immutable historical files retain their language. Mutable historical references are explicitly distinguished from matching frozen artifacts. No third-party binary or upstream archive is redistributed.'))
def stage(folder,name):
    paths=list(folder.glob(f'*/*{name}/*_all.vmesh'));assert len(paths)==1;return paths[0]
v4=stage(base/'holefill-repair-v4/y32-obj','step11_kibble')
v5=stage(base/'hole-recovery-v5/full-y32-01-obj','step11_kibble')
source=stage(base/'hole-recovery-v5/full-y32-01-obj','step7_cc_bpa')
control=stage(base/'fresh-yplus32-v2/control-obj','step7_cc_bpa')
for path in (v4,v5,source,control):assert (dest/'evidence'/path.relative_to(project)).is_file()
prediction=np.load(base/'fresh-yplus32-v2/prediction.npy',allow_pickle=False)
jput('expected-results.json',dict(prediction_raw_sha256=sha(prediction.tobytes()),
 grafted_source_sha256=digest(source),ungrafted_source_sha256=digest(control),
 **{name:dict(mesh='evidence/'+str(path.relative_to(project)),sha256=digest(path)) for name,path in [('v4-control',v4),('v5-recovery',v5)]}))
put('SUBMISSION_DRAFT.md',(root/'SOFTWARE_PROGRESS_PRIZE_SUBMISSION_DRAFT.md').read_bytes())
put('README.md','''# Source-preserving boundary grafting and bounded hole recovery

Local candidate package for a Vesuvius Challenge Progress Prize. Not submitted.

This release contains dependency-ordered patches against public ScrollFiesta,
English instructions, real-data before/after evidence and independent exact
new-face intersection checks. It does not claim recovered text or verified
whole-scroll/same-sheet continuity. See SUBMISSION_DRAFT.md for measured scope.

The two methods are deterministic computational geometry. AI assistance in
research and coding is separate from the algorithm; no new AI-laboratory model
or discovery is claimed or required to run them. The +32Y input uses Otsu.

Upstream and third-party dependencies are downloaded directly, not bundled or
relicensed. Read LICENSES/ScrollFiesta-MIT.txt and ATTRIBUTION.md before building.
Historical evidence remains verbatim, including its original language.

Reproduction instructions and verified results are supplied in REPRODUCE.md
and VERIFICATION.md. The release digest manifest is written after verification.
''')
jput('assembly-result.json',dict(guard=guard,status='assembled_unverified_candidate',package=str(dest),
 copied_evidence_files=len(copied),omitted_or_external_files=len(excluded),historical_drift=len(drift)))
print(json.dumps(dict(package=str(dest),evidence_files=len(copied),excluded=len(excluded),historical_drift=drift)),flush=True)
