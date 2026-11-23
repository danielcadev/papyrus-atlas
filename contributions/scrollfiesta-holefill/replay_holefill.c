/* Replay saved pre-fill geometry without extraction or re-meshing. */
#include "common/mesh_bin.h"
#include "holefill/hole_fill.h"
#include <stdio.h>
int main(int argc,char **argv) {
    if(argc!=3)return 2;
    Arena_T arena=Arena_new_sized(1024*1024);
    MeshBinData m;
    if(MeshBin_read_arena(arena,argv[1],&m))return 3;
    for(size_t i=0;i<m.nv;i++){
        float z=m.verts[3*i]-1808,y=m.verts[3*i+1]-2320,x=m.verts[3*i+2]-4112;
        m.verts[3*i]=x;m.verts[3*i+1]=y;m.verts[3*i+2]=z;
    }
    size_t before=m.nf,nl=0,ni=0,nfill=0;
    int rc=HoleFill_process_ex(arena,&m.verts,&m.faces,&m.nv,&m.nf,NULL,2,&nl,&ni,&nfill);
    fprintf(stderr,"replay rc=%d faces=%zu -> %zu loops=%zu interior=%zu filled=%zu\n",rc,before,m.nf,nl,ni,nfill);
    if(rc)return 4;
    for(size_t i=0;i<m.nv;i++){
        float x=m.verts[3*i],y=m.verts[3*i+1],z=m.verts[3*i+2];
        m.verts[3*i]=z+1808;m.verts[3*i+1]=y+2320;m.verts[3*i+2]=x+4112;
    }
    rc=MeshBin_write(argv[2],m.verts,m.nv,m.faces,m.nf,NULL);
    Arena_dispose(&arena);return rc;
}
