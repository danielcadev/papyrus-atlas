"""Collect completed verification, seal a release inventory and stream its archive."""
from pathlib import Path
import gzip,hashlib,json,shutil,tarfile
from ink_guard import require_guard
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent;project=root.parent
package=project/'releases/software-progress-prize-2026-10-v1'
assert not (package/'MANIFEST.json').exists()
def digest(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):result.update(block)
    return result.hexdigest()
def copy(source,target):
    assert source.is_file(),source
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert digest(source)==digest(target),target
    else:shutil.copyfile(source,target)
work=root/'software-release-clean-v1/reproduction'
verified=json.loads((work/'verification.json').read_text());assert verified['passed']
assert verified['exact_new_contacts']==0 and verified['exact_new_contact_pairs']==267
assert verified['results']['graft']['added_faces']==27
assert verified['results']['v5-recovery']['final_sha256']=='b93672d63891ad10c079215a5d7296f9ba4a7a5134e25750f8ba35761c11d65f'
assert digest(verified['results']['v5-recovery']['final'])==verified['results']['v5-recovery']['final_sha256']
for path in sorted(work.rglob('*')):
    if not path.is_file():continue
    relative=path.relative_to(work)
    if relative.parts[0] in ('build','tiff-config','tiff-include'):continue
    with path.open('rb') as stream:magic=stream.read(8)
    if magic[:4]==b'\x7fELF' or magic[:2]==b'MZ' or magic==b'!<arch>\n':continue
    if path.suffix in ('.npy','.raw'):continue
    copy(path,package/'verification/reproduction'/relative)
for label,folder,filename in (
 ('bootstrap-local','software-release-clean-v1','bootstrap-result.json'),
 ('bootstrap-online','software-release-online-bootstrap-v1','bootstrap-result.json'),
 ('public-data-online','software-release-online-data-v1/data','input-downloads.json'),
 ('reference-input-check','software-release-input-check-v1/result','input-verification.json')):
    source=root/folder/filename;result=json.loads(source.read_text());assert result['passed']
    copy(source,package/'verification'/f'{label}.json')
for source in sorted((root/'native').glob('software-release-*.*')):
    if not source.is_file() or source.name.startswith('software-release-seal-'):continue
    copy(source,package/'verification/resources/project-wrapper'/source.name)
for folder in ('software-release-online-data-v1/logs','software-release-input-check-v1/logs'):
    for source in sorted((root/folder).glob('*')):
        if source.is_file():copy(source,package/'verification/resources/release-wrapper'/source.name)
for name in ('package_software_progress_prize.py','inspect_software_release_inputs.py','seal_software_progress_prize.py'):
    copy(root/name,package/'verification/assembly-sources'/name)
planning=package/'verification/planning';planning.mkdir(parents=True,exist_ok=True)
for name in ('SUBMISSION_DRAFT.md','assembly-result.json'):
    if (package/name).exists():
        assert not (planning/name).exists();(package/name).rename(planning/name)
index=json.loads((package/'evidence-index.json').read_text())
for record in index['copied']:
    path=package/'evidence'/record['path']
    assert digest(path)==record['sha256'] and path.stat().st_size==record['bytes']
# Bytecode caches are disposable runtime outputs, not source or scientific evidence.
for cache in sorted(package.rglob('__pycache__'),reverse=True):shutil.rmtree(cache)
for path in package.rglob('*'):
    if not path.is_file():continue
    with path.open('rb') as stream:magic=stream.read(8)
    assert magic[:4]!=b'\x7fELF' and magic[:2]!=b'MZ' and magic!=b'!<arch>\n',path
    assert path.suffix not in ('.pyc','.nrrd','.npy','.tif','.tiff','.raw'),path
required=('README.md','LICENSE','ATTRIBUTION.md','METHODS.md','REPRODUCE.md','RESULTS.md',
          'SUBMISSION.md','VERIFICATION.md','figures-v2/before-after.png','tools/verify_release.py')
assert all((package/name).is_file() for name in required)
status=dict(status='verified_local_release_ready_for_upload',published=False,submitted=False,
 guard=guard,clean_reproduction_passed=True,upstream_online_retrieval_passed=True,
 public_ct_annotation_online_retrieval_passed=True,source_fixture_gold_digests_passed=True,
 graft_recovered_source_faces=27,hole_recovered_faces=17,final_hole_faces=5160,
 v5_final_sha256=verified['results']['v5-recovery']['final_sha256'],
 exact_new_pairs=267,exact_new_contacts=0,historical_evidence_files=len(index['copied']),
 external_or_omitted_inputs_executables=len(index['external_or_omitted']),
 historical_mutable_reference_drift=index['historical_manifest_drift'],
 human_submission_fields_remaining=['name','email','team description','public contribution URL','terms acceptance'],
 scope='MIT contribution patches and helpers with attributed historical geometry evidence. Upstream checkout, third-party implementations/binaries and original arrays are not redistributed. No new text or guaranteed prize.')
(package/'release-status.json').write_text(json.dumps(status,indent=2)+'\n')
files={str(path.relative_to(package)):dict(bytes=path.stat().st_size,sha256=digest(path))
       for path in sorted(package.rglob('*')) if path.is_file()}
manifest=package/'MANIFEST.json'
manifest.write_text(json.dumps(dict(schema='vesuvius-software-progress-release-v1',files=files,
    full_benchmark_passed=True,source_upstream_commit=verified['upstream_commit']),indent=2)+'\n')
for relative,record in files.items():assert digest(package/relative)==record['sha256']
archive=package.with_suffix('.tar.gz');assert not archive.exists()
with archive.open('xb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0,compresslevel=6) as compressed:
    with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as stream:
        for path in sorted(package.rglob('*')):
            if not path.is_file():continue
            assert not path.is_symlink()
            info=stream.gettarinfo(str(path),arcname=package.name+'/'+str(path.relative_to(package)))
            info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
            info.mode=0o755 if path.suffix=='.sh' else 0o644
            with path.open('rb') as source:stream.addfile(info,source)
sha=digest(archive)
checksum=Path(str(archive)+'.sha256');assert not checksum.exists()
checksum.write_text(f'{sha}  {archive.name}\n')
result=dict(passed=True,guard=guard,archive=str(archive),bytes=archive.stat().st_size,
 archive_sha256=sha,manifest_sha256=digest(manifest),manifest_files=len(files),
 historical_evidence_files=len(index['copied']),scope='Sealed local package. Extraction/inventory replay follows separately; not published or submitted.')
receipt=project/'releases/software-progress-prize-2026-10-v1-build-verification.json'
assert not receipt.exists();receipt.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
