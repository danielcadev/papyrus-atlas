/* Experimental bounded recovery of a whole rejected chart cycle.
 * Included by hole_fill.c after hf_triangle_emitted. ScrollFiesta helpers and
 * their license remain applicable. No source edits, merges or Steiner points.
 * Native predicates have shared-point blind spots: offline exact auditing of
 * the whole resulting mesh remains necessary before accepting an experiment.
 */
#include "../remesh/intersection_cleanup.h"

#define HS_MAX_N 19
#define HS_MAX_T 969
#define HS_NODE_CAP UINT64_C(2000000)
#define HS_PAIR_CAP UINT64_C(20000000)
#define HS_BYTE_CAP ((size_t)128*1024*1024)

typedef struct {
    int32_t local[3],global[3];
    double lo[3],hi[3];
    unsigned char good;
} HSTriangle;
typedef struct { int a,b; } HSInterval;
typedef struct {
    Arena_T arena;
    const HFChartMetric *metric;
    const HFEdgeIndex *eidx;
    const float *verts;
    const int32_t *faces,*map;
    size_t nv,nf,n;
    float local[HS_MAX_N*3];
    HSTriangle tri[HS_MAX_T];
    int tid[HS_MAX_N][HS_MAX_N][HS_MAX_N],nt;
    unsigned char compatible[HS_MAX_T][HS_MAX_T];
    unsigned char possible[HS_MAX_N][HS_MAX_N];
    int chosen[HS_MAX_N-2];
    int32_t answer[(HS_MAX_N-2)*3];
    IntersectionCleanupParams params;
    uint64_t nodes,pairs;
    int capped;
} HSSearch;

static int hs_enabled(void)
{
    const char *v=getenv("VES_HOLE_RECOVERY_SEARCH");
    return v&&strcmp(v,"1")==0;
}

static int hs_pair_ok(HSSearch *s,const float *v,size_t nv,
                      const int32_t *a,const int32_t *b)
{
    if(s->pairs==HS_PAIR_CAP){s->capped=1;return 0;}
    s->pairs++;
    return !hf_same_triangle(v,a,b)&&
        IntersectionCleanup_pair_test(v,nv,a,b,&s->params,NULL)==0;
}

/* Prior patches live in private local index spaces. Preserve actual source
 * identity for topology checks, and copy just two triangles for the geometric
 * predicate (which also recognizes shared coordinates). No mesh-size scratch. */
static int hs_prior_ok(HSSearch *s,const HSTriangle *t,
                       const HoleFillResult *fills,size_t nfill)
{
    const int32_t a[3]={0,1,2},b[3]={3,4,5};float v[18];
    for(int k=0;k<3;k++)memcpy(v+k*3,s->verts+(size_t)t->global[k]*3,3*sizeof(float));
    for(size_t p=0;p<nfill;p++)for(size_t f=0;f<fills[p].nf;f++){
        const HoleFillResult *r=&fills[p];const int32_t *u=r->faces+f*3;
        for(int k=0;k<3;k++){
            if(u[k]<0||(size_t)u[k]>=r->nv)return 0;
            memcpy(v+9+k*3,r->verts+(size_t)u[k]*3,3*sizeof(float));
            int32_t x=u[k],y=u[(k+1)%3];
            if(x>=0&&y>=0&&(size_t)x<r->n_boundary&&(size_t)y<r->n_boundary){
                x=r->boundary_map[x];y=r->boundary_map[y];
                for(int e=0;e<3;e++){
                    int32_t c=t->global[e],d=t->global[(e+1)%3];
                    if((c==x&&d==y)||(c==y&&d==x))return 0;
                }
            }
        }
        if(!hs_pair_ok(s,v,6,a,b))return 0;
    }
    return 1;
}

static int hs_prepare(HSSearch *s,const HoleFillResult *fills,size_t nfill)
{
    int n=(int)s->n,flip=-1;
    for(size_t p=0;p<nfill;p++)
        if(fills[p].n_merge||fills[p].n_boundary>fills[p].nv)return 0;
    for(int i=0;i<n;i++){
        int32_t a=s->map[i],b=s->map[(i+1)%n];
        if(a<0||b<0||(size_t)a>=s->nv||(size_t)b>=s->nv)return 0;
        for(int j=0;j<i;j++)if(s->map[j]==a)return 0;
        int ab=hf_eidx_find(s->eidx,a,b)!=INT32_MAX;
        int ba=hf_eidx_find(s->eidx,b,a)!=INT32_MAX;
        if(ab==ba||(flip>=0&&flip!=ab)||s->metric->boundary_degree[a]!=2||
           !isfinite(s->metric->lower[a])||!isfinite(s->metric->upper[a]))return 0;
        flip=ab;memcpy(s->local+i*3,s->verts+(size_t)a*3,3*sizeof(float));
    }
    memset(s->tid,0xff,sizeof s->tid);
    for(int i=0;i<n-2;i++)for(int k=i+1;k<n-1;k++)for(int j=k+1;j<n;j++){
        int ti=s->nt++;HSTriangle *t=&s->tri[ti];s->tid[i][k][j]=ti;
        t->local[0]=i;t->local[1]=flip?j:k;t->local[2]=flip?k:j;
        int ok=1;
        for(int h=0;h<3;h++){
            int a=t->local[h],b=t->local[(h+1)%3],d=abs(a-b);
            t->global[h]=s->map[a];
            if(d!=1&&d!=n-1&&loop_diag_in_mesh(s->map[a],s->map[b],s->eidx))ok=0;
        }
        if(!ok)continue;
        double scale=0,area=pf_tri_area(s->local,i,k,j);
        for(int h=0;h<3;h++)for(int d=0;d<3;d++){
            double x=(double)s->local[t->local[h]*3+d]-s->local[t->local[(h+1)%3]*3+d];scale+=x*x;
        }
        if(!(scale>0)||!(4*area*area>1e-12*scale*scale)||
           !hf_ear_angles(s->local,t->local[0],t->local[1],t->local[2],t->lo,t->hi))continue;
        for(size_t f=0;f<s->nf;f++)
            if(!hs_pair_ok(s,s->verts,s->nv,t->global,s->faces+f*3)){ok=0;break;}
        if(s->capped)return 0;
        if(ok)ok=hs_prior_ok(s,t,fills,nfill);
        if(s->capped)return 0;
        t->good=(unsigned char)ok;
    }
    for(int a=0;a<s->nt;a++)if(s->tri[a].good)
        for(int b=0;b<a;b++)if(s->tri[b].good){
            int ok=hs_pair_ok(s,s->verts,s->nv,s->tri[a].global,s->tri[b].global);
            if(s->capped)return 0;
            s->compatible[a][b]=s->compatible[b][a]=(unsigned char)ok;
        }
    for(int i=0;i<n-1;i++)s->possible[i][i+1]=1;
    for(int len=2;len<n;len++)for(int i=0;i+len<n;i++){
        int j=i+len;
        for(int k=i+1;k<j;k++)if(s->tri[s->tid[i][k][j]].good&&
            s->possible[i][k]&&s->possible[k][j])s->possible[i][j]=1;
    }
    return s->possible[0][n-1];
}

static int hs_search(HSSearch *s,const HSInterval *pending,int np,int depth)
{
    if(s->nodes==HS_NODE_CAP){s->capped=1;return 0;}s->nodes++;
    double lo[HS_MAX_N],hi[HS_MAX_N];
    for(size_t v=0;v<s->n;v++){lo[v]=s->metric->lower[s->map[v]];hi[v]=s->metric->upper[s->map[v]];}
    for(int z=0;z<depth;z++){
        const HSTriangle *t=&s->tri[s->chosen[z]];
        for(int k=0;k<3;k++){lo[t->local[k]]+=t->lo[k];hi[t->local[k]]+=t->hi[k];}
    }
    for(int v=0;v<(int)s->n;v++){
        int open=0;for(int z=0;z<np;z++)if(v>=pending[z].a&&v<=pending[z].b)open=1;
        if(lo[v]>INTRINSIC_ANGLE_TAU+INTRINSIC_ANGLE_TOL||
           (!open&&!IntrinsicAngle_closed_fan_possible(lo[v],hi[v])))return 0;
    }
    if(!np){
        if(depth!=(int)s->n-2)return 0;
        for(int z=0;z<depth;z++)memcpy(s->answer+z*3,s->tri[s->chosen[z]].local,3*sizeof(int32_t));
        HoleFillResult r={0};r.verts=s->local;r.faces=s->answer;
        r.nv=r.n_boundary=s->n;r.nf=s->n-2;r.boundary_map=(int32_t *)s->map;
        if(!fill_boundary_is_exact(r.faces,r.nf,s->n)||!hf_chart_fill_possible(s->arena,s->metric,&r))return 0;
        orient_fill(r.faces,r.nf,s->eidx,s->map,s->n);return 1;
    }
    HSInterval p=pending[np-1];
    for(int k=p.a+1;k<p.b;k++){
        int ti=s->tid[p.a][k][p.b],ok=1;
        if(!s->tri[ti].good||!s->possible[p.a][k]||!s->possible[k][p.b])continue;
        for(int z=0;z<depth;z++)if(!s->compatible[ti][s->chosen[z]]){ok=0;break;}
        if(!ok)continue;
        HSInterval next[HS_MAX_N];int nn=np-1;memcpy(next,pending,(size_t)nn*sizeof *next);
        if(k-p.a>1)next[nn++]=(HSInterval){p.a,k};
        if(p.b-k>1)next[nn++]=(HSInterval){k,p.b};
        s->chosen[depth]=ti;
        if(hs_search(s,next,nn,depth+1))return 1;
        if(s->capped)return 0;
    }
    return 0;
}

static int hf_recover_duplicate_cycle(Arena_T arena,const float *verts,size_t nv,
    const int32_t *faces,size_t nf,const HFEdgeIndex *eidx,
    const int32_t *loop,size_t n,const HFChartMetric *metric,
    const HoleFillResult *prior,size_t nprior,HoleFillResult *out)
{
    if(!hs_enabled()||!metric||metric->nv!=nv||n<3||n>HS_MAX_N||
       !verts||!faces||!loop||!eidx||!out||nv>(size_t)INT32_MAX||
       sizeof(HSSearch)>HS_BYTE_CAP)return -2;
    HSSearch *s=calloc(1,sizeof *s);if(!s)return -2;
    s->arena=arena;s->verts=verts;s->nv=nv;s->faces=faces;s->nf=nf;
    s->eidx=eidx;s->map=loop;s->n=n;s->metric=metric;
    IntersectionCleanup_default_params(&s->params);s->params.gap_max=0;s->params.include_hinges=1;
    HSInterval root={0,(int)n-1};
    int ok=hs_prepare(s,prior,nprior)&&hs_search(s,&root,1,0);
    fprintf(stderr,"  [hole_recovery] n=%zu result=%s nodes=%llu pairs=%llu strict_geometry=offline_required\n",
        n,ok?"candidate":s->capped?"budget_exhausted":"no_candidate",
        (unsigned long long)s->nodes,(unsigned long long)s->pairs);
    if(!ok){free(s);return -2;}
    /* Stack-copy the tiny successful result before freeing bounded scratch.
     * Arena allocation exceptions can then use the caller's usual handling. */
    float v[HS_MAX_N*3];int32_t f[(HS_MAX_N-2)*3],b[HS_MAX_N];
    memcpy(v,s->local,n*3*sizeof(float));memcpy(f,s->answer,(n-2)*3*sizeof(int32_t));
    memcpy(b,loop,n*sizeof(int32_t));free(s);
    HoleFillResult r={0};r.nv=r.n_boundary=n;r.nf=n-2;
    r.verts=ARENA_ALLOC(arena,n*3*sizeof(float));
    r.faces=ARENA_ALLOC(arena,(n-2)*3*sizeof(int32_t));
    r.boundary_map=ARENA_ALLOC(arena,n*sizeof(int32_t));
    memcpy(r.verts,v,n*3*sizeof(float));memcpy(r.faces,f,(n-2)*3*sizeof(int32_t));
    memcpy(r.boundary_map,b,n*sizeof(int32_t));*out=r;return 0;
}
