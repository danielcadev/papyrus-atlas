/* Research-only exhaustive/budgeted triangulation search for the saved 19-cycle.
 * Reuses ScrollFiesta's licensed helpers; does not change production or source.
 * CLI: candidate source-step7.vmesh loop-in.obj NEW-output.vmesh node-budget
 * Exit 0: candidate passes existing certificates, STRICT GEOMETRIC AUDIT PENDING;
 * 10: finite search exhausted; 11: budget exhausted;
 * other nonzero: invalid fixture, failed certificate, or I/O error.
 * Compile/link and run ONLY through the project's serial guarded wrapper.
 */
#include "scrollfiesta-comparison/source/src/holefill/hole_fill.c"
#include "scrollfiesta-comparison/source/src/common/mesh_bin.h"
#include "scrollfiesta-comparison/source/src/remesh/intersection_cleanup.h"
#include <errno.h>
#include <inttypes.h>
#include <unistd.h>

enum { RC_N=19, RC_NT=969, RC_NF=17 };
typedef struct {
    int32_t local[3], global[3];
    double lo[3], hi[3];
    int good;
} RCTriangle;
typedef struct { int a,b; } RCInterval;
typedef struct {
    Arena_T arena;
    MeshBinData mesh;
    HFChartMetric metric;
    HFEdgeIndex eidx;
    IntersectionCleanupParams params;
    int32_t map[RC_N], answer[RC_NF*3];
    float local[RC_N*3];
    RCTriangle tri[RC_NT];
    int tid[RC_N][RC_N][RC_N], nt;
    unsigned char compatible[RC_NT][RC_NT];
    unsigned char possible[RC_N][RC_N];
    int chosen[RC_NF];
    uint64_t nodes, budget, complete, pair_prunes, angle_prunes;
    size_t rejected_source, rejected_shape, rejected_edge, accepted_tri;
    int exhausted_budget;
} RCSearch;

/* Decimal OBJ is ONLY a locator. Geometry below comes from binary source. */
static int rc_match_loop(RCSearch *s,const char *path,
                         BoundaryLoop *loops,size_t nl)
{
    double loc[RC_N*3]; char line[512]; size_t n=0,matches=0;
    FILE *f=fopen(path,"r"); if(!f)return 0;
    while(fgets(line,sizeof line,f)) if(line[0]=='v'&&line[1]==' '){
        if(n==RC_N||sscanf(line+2,"%lf%lf%lf",loc+n*3,loc+n*3+1,loc+n*3+2)!=3){
            fclose(f); return 0;
        }
        n++;
    }
    int io=ferror(f); fclose(f); if(io||n!=RC_N)return 0;
    for(size_t q=0;q<nl;q++){
        if(loops[q].len!=RC_N+1||loops[q].verts[0]!=loops[q].verts[RC_N])continue;
        for(int start=0;start<RC_N;start++)for(int dir=-1;dir<=1;dir+=2){
            int match=1;
            for(int k=0;k<RC_N&&match;k++){
                int p=(start+dir*k+RC_N*2)%RC_N;
                int32_t v=loops[q].verts[p];
                for(int d=0;d<3;d++)
                    if(fabs((double)s->mesh.verts[(size_t)v*3+d]-loc[k*3+d])>0.00000051)match=0;
            }
            if(match){
                matches++;
                for(int k=0;k<RC_N;k++)s->map[k]=loops[q].verts[(start+dir*k+RC_N*2)%RC_N];
            }
        }
    }
    if(matches!=1)return 0;
    for(int k=0;k<RC_N;k++){
        for(int j=0;j<k;j++)if(s->map[k]==s->map[j])return 0;
        memcpy(s->local+k*3,s->mesh.verts+(size_t)s->map[k]*3,3*sizeof(float));
    }
    return 1;
}

static int rc_boundary_edge(int a,int b)
{ int d=abs(a-b); return d==1||d==RC_N-1; }

static int rc_fixture_predicates(const IntersectionCleanupParams *p)
{
    float v[]={0,0,0,2,0,0,0,2,0,2,2,0,
        0,0,.1f,2,0,.1f,0,2,.1f,.5f,.5f,-1,.5f,.5f,1,1.5f,.5f,0};
    int32_t a[]={0,1,2},dup[]={0,1,2},adj[]={1,3,2},sep[]={4,5,6},stab[]={7,8,9};
    return IntersectionCleanup_pair_test(v,10,a,dup,p,NULL)>0&&
        IntersectionCleanup_pair_test(v,10,a,adj,p,NULL)==0&&
        IntersectionCleanup_pair_test(v,10,a,sep,p,NULL)==0&&
        IntersectionCleanup_pair_test(v,10,a,stab,p,NULL)>0;
}

static int rc_prepare(RCSearch *s)
{
    int flip=-1;
    for(int i=0;i<RC_N;i++){
        int32_t a=s->map[i],b=s->map[(i+1)%RC_N];
        int ab=hf_eidx_find(&s->eidx,a,b)!=INT32_MAX;
        int ba=hf_eidx_find(&s->eidx,b,a)!=INT32_MAX;
        if(ab==ba||(flip>=0&&flip!=ab))return 0;
        flip=ab;
        if(s->metric.boundary_degree[a]!=2||!isfinite(s->metric.lower[a])||
           !isfinite(s->metric.upper[a])||s->metric.lower[a]<=0)return 0;
        fprintf(stderr,"metric[%d] source_id=%d lower=%.17g upper=%.17g\n",
                i,a,s->metric.lower[a],s->metric.upper[a]);
    }
    memset(s->tid,0xff,sizeof s->tid);
    for(int i=0;i<RC_N-2;i++)for(int k=i+1;k<RC_N-1;k++)for(int j=k+1;j<RC_N;j++){
        int ti=s->nt++; RCTriangle *t=&s->tri[ti];
        s->tid[i][k][j]=ti;
        t->local[0]=i;t->local[1]=flip?j:k;t->local[2]=flip?k:j;
        for(int h=0;h<3;h++)t->global[h]=s->map[t->local[h]];
        int ok=1;
        for(int h=0;h<3;h++){
            int a=t->local[h],b=t->local[(h+1)%3];
            if(!rc_boundary_edge(a,b)&&loop_diag_in_mesh(s->map[a],s->map[b],&s->eidx))ok=0;
        }
        if(!ok){s->rejected_edge++;continue;}
        /* Same scale-relative shape floor as the production 3-D ear helper. */
        double scale=0,area=pf_tri_area(s->local,i,k,j);
        for(int h=0;h<3;h++)for(int d=0;d<3;d++){
            double x=(double)s->local[t->local[h]*3+d]-s->local[t->local[(h+1)%3]*3+d];
            scale+=x*x;
        }
        if(!(scale>0)||!(4*area*area>1e-12*scale*scale)||
           !hf_ear_angles(s->local,t->local[0],t->local[1],t->local[2],t->lo,t->hi)){
            s->rejected_shape++;continue;
        }
        for(size_t f=0;f<s->mesh.nf;f++){
            const int32_t *src=s->mesh.faces+f*3;
            if(hf_same_triangle(s->mesh.verts,t->global,src)||
               IntersectionCleanup_pair_test(s->mesh.verts,s->mesh.nv,t->global,src,&s->params,NULL)!=0){ok=0;break;}
        }
        if(!ok){s->rejected_source++;continue;}
        t->good=1;s->accepted_tri++;
    }
    for(int a=0;a<s->nt;a++)if(s->tri[a].good)
        for(int b=0;b<a;b++)if(s->tri[b].good){
            int ok=!hf_same_triangle(s->mesh.verts,s->tri[a].global,s->tri[b].global)&&
                IntersectionCleanup_pair_test(s->mesh.verts,s->mesh.nv,
                    s->tri[a].global,s->tri[b].global,&s->params,NULL)==0;
            s->compatible[a][b]=s->compatible[b][a]=(unsigned char)ok;
        }
    for(int i=0;i<RC_N-1;i++)s->possible[i][i+1]=1;
    for(int len=2;len<RC_N;len++)for(int i=0;i+len<RC_N;i++){
        int j=i+len;
        for(int k=i+1;k<j;k++)if(s->tri[s->tid[i][k][j]].good&&
            s->possible[i][k]&&s->possible[k][j])s->possible[i][j]=1;
    }
    return 1;
}

/* Canonical root-edge recursion enumerates each polygon triangulation once.
 * Pending intervals are independent combinatorially, but still tested for
 * geometric intersections and for the coupled source-angle certificate. */
static int rc_search(RCSearch *s,const RCInterval *pending,int np,int depth)
{
    if(s->nodes>=s->budget){s->exhausted_budget=1;return 0;}
    s->nodes++;
    double lo[RC_N],hi[RC_N];
    for(int v=0;v<RC_N;v++){lo[v]=s->metric.lower[s->map[v]];hi[v]=s->metric.upper[s->map[v]];}
    for(int z=0;z<depth;z++){
        RCTriangle *t=&s->tri[s->chosen[z]];
        for(int k=0;k<3;k++){lo[t->local[k]]+=t->lo[k];hi[t->local[k]]+=t->hi[k];}
    }
    for(int v=0;v<RC_N;v++){
        int open=0;
        for(int z=0;z<np;z++)if(v>=pending[z].a&&v<=pending[z].b)open=1;
        if(lo[v]>INTRINSIC_ANGLE_TAU+INTRINSIC_ANGLE_TOL||
           (!open&&!IntrinsicAngle_closed_fan_possible(lo[v],hi[v]))){s->angle_prunes++;return 0;}
    }
    if(!np){
        if(depth!=RC_NF)return 0;
        s->complete++;
        for(int z=0;z<depth;z++)memcpy(s->answer+z*3,s->tri[s->chosen[z]].local,3*sizeof(int32_t));
        HoleFillResult result={0};
        result.verts=s->local;result.faces=s->answer;result.nv=RC_N;result.nf=RC_NF;
        result.n_boundary=RC_N;result.boundary_map=s->map;
        if(!fill_boundary_is_exact(result.faces,result.nf,RC_N)||
           !hf_chart_fill_possible(s->arena,&s->metric,&result))return 0;
        orient_fill(result.faces,result.nf,&s->eidx,s->map,RC_N);
        return 1;
    }
    RCInterval p=pending[np-1];
    for(int k=p.a+1;k<p.b;k++){
        int ti=s->tid[p.a][k][p.b];
        if(!s->tri[ti].good||!s->possible[p.a][k]||!s->possible[k][p.b])continue;
        int ok=1;
        for(int z=0;z<depth;z++)if(!s->compatible[ti][s->chosen[z]]){ok=0;break;}
        if(!ok){s->pair_prunes++;continue;}
        RCInterval next[RC_N];int nn=np-1;
        memcpy(next,pending,(size_t)nn*sizeof *next);
        if(k-p.a>1)next[nn++]=(RCInterval){p.a,k};
        if(p.b-k>1)next[nn++]=(RCInterval){k,p.b};
        s->chosen[depth]=ti;
        if(rc_search(s,next,nn,depth+1))return 1;
        if(s->exhausted_budget)return 0;
    }
    return 0;
}

int main(int argc,char **argv)
{
    if(argc!=5){fprintf(stderr,"usage: %s source-step7.vmesh loop-in.obj NEW-output.vmesh node-budget\n",argv[0]);return 2;}
    char *end=NULL;errno=0;uint64_t budget=strtoull(argv[4],&end,10);
    if(errno||!end||*end||!budget||argv[4][0]=='-'||access(argv[3],F_OK)==0)return 2;
    RCSearch *s=calloc(1,sizeof *s);if(!s)return 3;
    s->arena=Arena_new_sized(1024*1024);s->budget=budget;
    if(MeshBin_read_arena(s->arena,argv[1],&s->mesh)||s->mesh.nf!=5139||
       !s->mesh.nv||s->mesh.nv>INT32_MAX)return 3;
    /* Preserve original global float32s for an exactly identical output prefix. */
    float *global=malloc(s->mesh.nv*3*sizeof(float));if(!global)return 3;
    memcpy(global,s->mesh.verts,s->mesh.nv*3*sizeof(float));
    for(size_t v=0;v<s->mesh.nv;v++){
        float z=global[v*3]-1808,y=global[v*3+1]-2320,x=global[v*3+2]-4112;
        s->mesh.verts[v*3]=x;s->mesh.verts[v*3+1]=y;s->mesh.verts[v*3+2]=z;
        if(!isfinite(x)||!isfinite(y)||!isfinite(z))return 3;
    }
    for(size_t f=0;f<s->mesh.nf*3;f++)
        if(s->mesh.faces[f]<0||(size_t)s->mesh.faces[f]>=s->mesh.nv)return 3;
    IntersectionCleanup_default_params(&s->params);s->params.gap_max=0;s->params.include_hinges=1;
    if(!rc_fixture_predicates(&s->params))return 4;
    IntersectionCleanupStats before={0};
    if(IntersectionCleanup_audit(s->mesh.verts,s->mesh.nv,s->mesh.faces,s->mesh.nf,NULL,
       &s->params,NULL,&before)||before.conflicts)return 4;
    UEdge *edges=NULL;BoundaryLoop *loops=NULL;
    size_t ne=find_boundary_edges(s->arena,s->mesh.faces,s->mesh.nf,&edges);
    size_t nl=chain_into_loops(s->arena,edges,ne,s->mesh.nv,s->mesh.verts,&loops);
    if(!rc_match_loop(s,argv[2],loops,nl))return 5;
    hf_eidx_build(s->arena,s->mesh.faces,s->mesh.nf,s->mesh.nv,edges,ne,&s->eidx);
    s->metric.nv=s->mesh.nv;
    s->metric.lower=ARENA_CALLOC(s->arena,s->mesh.nv,sizeof(double));
    s->metric.upper=ARENA_CALLOC(s->arena,s->mesh.nv,sizeof(double));
    s->metric.boundary_degree=ARENA_CALLOC(s->arena,s->mesh.nv,sizeof(int32_t));
    for(size_t e=0;e<ne;e++){s->metric.boundary_degree[edges[e].v0]++;s->metric.boundary_degree[edges[e].v1]++;}
    hf_chart_metric_sum(s->mesh.verts,s->mesh.faces,s->mesh.nf,&s->metric);
    /* Real source metric and real edge index are mandatory: NULL-metric replay
     * of this decimal OBJ does not reproduce the production failure. */
    Arena_Mark mark=Arena_save(s->arena);HoleFillResult baseline={0};
    int oldrc=fill_chart_cycle_3d(s->arena,s->mesh.verts,&s->eidx,s->map,RC_N,&s->metric,&baseline);
    fprintf(stderr,"source_faces=%zu source_conflicts=%zu real_metric_v4_rc=%d\n",s->mesh.nf,before.conflicts,oldrc);
    Arena_restore(s->arena,mark);
    if(oldrc!=-2)return 6;
    if(!rc_prepare(s))return 7;
    fprintf(stderr,"triangles=%d admissible=%zu reject_edge=%zu reject_shape=%zu reject_source=%zu root_possible=%d\n",
       s->nt,s->accepted_tri,s->rejected_edge,s->rejected_shape,s->rejected_source,s->possible[0][RC_N-1]);
    RCInterval root={0,RC_N-1};
    int found=s->possible[0][RC_N-1]&&rc_search(s,&root,1,0);
    fprintf(stderr,"result=%s nodes=%" PRIu64 " complete=%" PRIu64 " pair_prunes=%" PRIu64 " angle_prunes=%" PRIu64 "\n",
       found?"candidate":s->exhausted_budget?"budget_inconclusive":"exhausted_no_boundary_vertex_triangulation",
       s->nodes,s->complete,s->pair_prunes,s->angle_prunes);
    if(!found){int rc=s->exhausted_budget?11:10;free(global);Arena_dispose(&s->arena);free(s);return rc;}
    size_t nf=s->mesh.nf+RC_NF;
    int32_t *faces=malloc(nf*3*sizeof(int32_t));if(!faces)return 3;
    memcpy(faces,s->mesh.faces,s->mesh.nf*3*sizeof(int32_t));
    for(int f=0;f<RC_NF;f++)for(int k=0;k<3;k++)faces[(s->mesh.nf+f)*3+k]=s->map[s->answer[f*3+k]];
    IntersectionCleanupStats after={0};
    if(IntersectionCleanup_audit(s->mesh.verts,s->mesh.nv,faces,nf,NULL,&s->params,NULL,&after)||after.conflicts)return 8;
    /* Explicit duplicates independent of adjacency exceptions in the auditor. */
    for(size_t f=s->mesh.nf;f<nf;f++)for(size_t g=0;g<f;g++)
        if(hf_same_triangle(s->mesh.verts,faces+f*3,faces+g*3))return 8;
    if(memcmp(faces,s->mesh.faces,s->mesh.nf*3*sizeof(int32_t)))return 8;
    double area=0;for(int f=0;f<RC_NF;f++)area+=pf_tri_area(s->local,s->answer[f*3],s->answer[f*3+1],s->answer[f*3+2]);
    /* The native pair predicate suppresses some STAB cases with shared points.
     * Therefore this is a research candidate, not an embeddedness certificate.
     * Acceptance requires an independent check that each intersection is wholly
     * contained in the pair's actual common geometric point or edge. */
    fprintf(stderr,"candidate_existing_certificates_pass faces=%zu added=%d added_area=%.17g full_native_conflicts=%zu source_prefix_exact=1 vertex_array_exact=1 merges=0 strict_geometric_audit=PENDING\n",
            nf,RC_NF,area,after.conflicts);
    int rc=MeshBin_write(argv[3],global,s->mesh.nv,faces,nf,NULL);
    free(faces);free(global);Arena_dispose(&s->arena);free(s);return rc?9:0;
}
