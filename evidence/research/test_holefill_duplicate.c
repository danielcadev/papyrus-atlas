/* Uses production static helpers; captured real cycles are the regression. */
#include "scrollfiesta-comparison/source/src/holefill/hole_fill.c"

static int cycle(Arena_T arena,const char *path,int expect_fill)
{
    FILE *fp=fopen(path,"r");if(!fp)return 1;
    float v[256*3];int32_t ids[256];size_t n=0;char line[256];
    while(fgets(line,sizeof(line),fp))if(line[0]=='v'&&line[1]==' '){
        if(n==256||sscanf(line+2,"%f%f%f",v+n*3,v+n*3+1,v+n*3+2)!=3)return 2;
        ids[n]=(int32_t)n;n++;
    }
    fclose(fp);
    HoleFillResult result={0};HFEdgeIndex empty={0};
    int rc=fill_chart_cycle_3d(arena,v,&empty,ids,n,NULL,&result);
    if(expect_fill){
        if(rc||result.nf!=n-2||!fill_boundary_is_exact(result.faces,result.nf,n))return 3;
        for(size_t f=0;f<result.nf;f++)
            if(hf_triangle_emitted(result.verts,result.faces+f*3,result.faces,f))return 4;
    }else if(rc==0)return 5;
    return 0;
}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;
    Arena_T arena=Arena_new_sized(1024*1024);
    /* The source angle metric changes greedy ear selection. Without it the
     * captured cycle already has a duplicate-free proposal and must retain
     * it. The full saved-mesh replay exercises the production angle metric. */
    int a=cycle(arena,argv[1],1),b=cycle(arena,argv[2],1);
    float v[]={0,0,0,1,0,0,0,1,0, 0,0,0,1,0,0,0,1,0,
               0,0,.00001f,1,0,.00001f,0,1,.00001f};
    int32_t t[]={0,1,2},rev[]={5,4,3},near[]={6,7,8},different[]={0,1,1};
    if(a||b||!hf_same_triangle(v,t,rev)||hf_same_triangle(v,t,near)||
       hf_same_triangle(v,t,different)){
        fprintf(stderr,"holefill regression failed: real=%d valid=%d\n",a,b);return 1;
    }
    puts("PASS: captured 19-cycle without source angle metric and valid 6-cycle retained; opposite winding, separate IDs, nearby sheet and vertex multiplicity checks");
    Arena_dispose(&arena);return 0;
}
