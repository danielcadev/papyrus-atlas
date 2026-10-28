from pathlib import Path
import subprocess
from guard import start_guard
start_guard()
p=Path(__file__).resolve().parent;b=p/'scrollfiesta-comparison';s=b/'source/src'
subprocess.run(['cc','-O2','-std=gnu17','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I',str(s),str(p/'test_boundary_graft.c'),str(s/'common/arena.c'),str(s/'common/except.c'),str(s/'common/csr.c'),'-lm','-o',str(b/'build/test_boundary_graft')],check=True)
subprocess.run([str(b/'build/test_boundary_graft')],check=True)
subprocess.run(['cmake','--build',str(b/'build'),'--target','cube_mesh','--parallel','1'],check=True)
