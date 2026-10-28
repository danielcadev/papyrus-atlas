"""Run one native CLI, preserving desktop RAM and recording exact exit/logs."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time
from guard import available_mib

parser=argparse.ArgumentParser()
parser.add_argument('--name',required=True)
parser.add_argument('--timeout',type=float,default=120)
parser.add_argument('--cwd')
parser.add_argument('command',nargs=argparse.REMAINDER)
args=parser.parse_args()
command=args.command
if command and command[0]=='--':command=command[1:]
assert command
root=Path(__file__).resolve().parent/'native'
log=root/(args.name+'.log')
status=root/(args.name+'.status.json')
assert not log.exists(),f'Preserve existing log: {log}'
assert available_mib()>=3072,'Desktop reserve already below 3 GiB'
assert not os.access('/dev/dri',os.R_OK) and not os.access('/dev/kfd',os.R_OK),'GPU devices must be inaccessible'
env=os.environ.copy()
env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
           CUDA_VISIBLE_DEVICES='-1',HIP_VISIBLE_DEVICES='-1',ROCR_VISIBLE_DEVICES='',
           VC_GRID_CACHE_BYTES=str(16*1024**2),VC_GRID_CACHE_ENTRIES='32',
           QT_QPA_PLATFORM='offscreen',MALLOC_ARENA_MAX='1')
begin=time.monotonic()
minimum=available_mib()
reason='completed'
with log.open('w') as output:
    process=subprocess.Popen(command,cwd=args.cwd,env=env,stdout=output,
                             stderr=subprocess.STDOUT,start_new_session=True)
    while process.poll() is None:
        available=available_mib()
        minimum=min(minimum,available)
        if available<3072 or time.monotonic()-begin>args.timeout:
            reason='desktop reserve' if available<3072 else 'wall timeout'
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL)
            break
        time.sleep(0.2)
    code=process.wait()
result=dict(command=command,returncode=code,reason=reason,
            elapsed_seconds=time.monotonic()-begin,minimum_available_mib=minimum,
            max_child_rss_mib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss/1024,
            gpu_devices_inaccessible=True,log=str(log))
status.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
print(log.read_text()[-7000:],flush=True)
raise SystemExit(code if code>=0 else 1)
