"""Require the unchanged CPU-only software experiment resource envelope."""
import os
from pathlib import Path
from guard import start_guard

def require_guard():
    keys=('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VESUVIUS_THREADS','OMP_THREAD_LIMIT')
    assert all(os.environ.get(key)=='1' for key in keys)
    assert os.getpriority(os.PRIO_PROCESS,0)>=19
    assert not os.access('/dev/dri',os.R_OK) and not os.access('/dev/kfd',os.R_OK)
    line=next(line for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
    group=Path('/sys/fs/cgroup')/line.split('::',1)[1].lstrip('/')
    quota,period=map(int,(group/'cpu.max').read_text().split())
    memory=int((group/'memory.max').read_text())
    assert quota/period<=.25 and memory<=384*1024**2
    assert int((group/'memory.swap.max').read_text())==0
    assert (group/'io.weight').read_text().strip()=='default 10'
    start_guard()
    return dict(cpu_max=f'{quota} {period}',memory_max=memory,memory_swap_max=0,
        io_weight=10,nice=19,gpu_inaccessible=True,numerical_threads=1,desktop_reserve_mib=3072)
