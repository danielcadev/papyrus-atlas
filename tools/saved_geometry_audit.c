/* Native read-only positive-area/interpenetration audit, including hinges. */
#include "common/arena.h"
#include "common/mesh_bin.h"
#include "remesh/intersection_cleanup.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

static int visit(size_t a,size_t b,int kind,void *context)
{
    return fprintf((FILE *)context,"%zu,%zu,%d\n",a,b,kind)<0;
}

int main(int argc,char **argv)
{
    if (argc!=4 && argc!=7) return 2;
    IntersectionCleanupParams params;
    IntersectionCleanup_default_params(&params);
    params.gap_max=0.0;
    params.include_hinges=1;
    /* Positive overlap, shared-edge touch, separated parallel face and stab. */
    float fixture[]={0,0,0,2,0,0,0,2,0, 2,2,0,
                     0,0,.1f,2,0,.1f,0,2,.1f,
                     .5f,.5f,-1,.5f,.5f,1,1.5f,.5f,0};
    int32_t a[]={0,1,2}, duplicate[]={0,1,2}, adjacent[]={1,3,2},
            parallel[]={4,5,6},crossing[]={7,8,9};
    if (IntersectionCleanup_pair_test(fixture,10,a,duplicate,&params,NULL)<=0 ||
        IntersectionCleanup_pair_test(fixture,10,a,adjacent,&params,NULL)!=0 ||
        IntersectionCleanup_pair_test(fixture,10,a,parallel,&params,NULL)!=0 ||
        IntersectionCleanup_pair_test(fixture,10,a,crossing,&params,NULL)<=0) return 3;
    Arena_T arena=Arena_new_sized(1024*1024);
    MeshBinData mesh;
    if (MeshBin_read_arena(arena,argv[1],&mesh)!=0) return 4;
    float origin[]={768,2408,3536};
    if (argc==7) {
        for (int d=0;d<3;d++) {
            char *end=NULL;
            origin[d]=strtof(argv[d+4],&end);
            if (!end || *end || !isfinite(origin[d])) return 2;
        }
    }
    for (size_t v=0;v<mesh.nv;v++)
        for (int d=0;d<3;d++) mesh.verts[v*3+d]-=origin[d];
    FILE *pairs=fopen(argv[3],"w"); if (!pairs) return 5;
    fprintf(pairs,"face0,face1,kind\n");
    IntersectionCleanupStats stats;
    int rc=IntersectionCleanup_audit_visit(mesh.verts,mesh.nv,mesh.faces,mesh.nf,NULL,
                                          &params,NULL,visit,pairs,&stats);
    if (fclose(pairs)) return 6;
    if (rc!=0) return 7;
    FILE *out=fopen(argv[2],"w");if (!out) return 8;
    fprintf(out,"{\"faces\":%zu,\"candidates\":%zu,\"overlap\":%zu,\"stab\":%zu,\"fold\":%zu,\"conflicts\":%zu,\"gap_max\":0,\"include_hinges\":true,\"predicate_fixture_checks\":4,\"read_only\":true}\n",
        mesh.nf,stats.candidate_pairs,stats.overlap_pairs,stats.stab_pairs,
        stats.fold_pairs,stats.conflicts);
    if (fclose(out)) return 9;
    printf("%s: conflicts=%zu (overlap=%zu stab=%zu fold=%zu), 4/4 predicate fixtures\n",
        argv[1],stats.conflicts,stats.overlap_pairs,stats.stab_pairs,stats.fold_pairs);
    Arena_dispose(&arena);
    return 0;
}
