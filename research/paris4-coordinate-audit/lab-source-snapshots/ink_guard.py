"""Ink-specific guard after explicit user authorization of a larger memory cap.

Historical mesh experiments retain their original 384 MiB guard and wrapper.
"""
import os
from pathlib import Path


def require_guard():
    keys=('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VESUVIUS_THREADS','OMP_THREAD_LIMIT')
    assert all(os.environ.get(k)=='1' for k in keys), 'All five thread limits must be one'
    assert os.getpriority(os.PRIO_PROCESS,0)>=19, 'Nice=19 required'
    assert not os.access('/dev/dri',os.R_OK) and not os.access('/dev/kfd',os.R_OK), 'GPU must be inaccessible'
    line=next(s for s in Path('/proc/self/cgroup').read_text().splitlines() if s.startswith('0::'))
    group=Path('/sys/fs/cgroup')/line.split('::',1)[1].lstrip('/')
    quota,period=map(int,(group/'cpu.max').read_text().split())
    assert quota/period<=.25, 'CPUQuota must be <=25%'
    memory=int((group/'memory.max').read_text())
    assert memory<=2*1024**3, 'User-authorized memory cap is 2 GiB'
    assert int((group/'memory.swap.max').read_text())==0, 'No swap'
    assert (group/'io.weight').read_text().strip()=='default 10', 'IOWeight=10 required'
    from guard import start_guard
    start_guard()
    return dict(cgroup=str(group),cpu_max=(group/'cpu.max').read_text().strip(),
                memory_max=memory,memory_swap_max=0,io_weight='default 10',nice=19,
                gpu_inaccessible=True,thread_limits={k:'1' for k in keys},desktop_reserve_mib=3072,
                authorization='User explicitly requested a larger limit during the ink reading task, 2026-10-28')
