#include "split/overlap_sep.c"

int main(void)
{
    Arena_T arena = Arena_new_sized(4096);
    int32_t labels[37], original[37];
    for (int i=0;i<32;i++) labels[i]=i/16;
    for (int i=32;i<37;i++) labels[i]=i-30;
    memcpy(original,labels,sizeof labels);
    /* 32 can attach only to B; 33 is blocked; 34 is reached through 32;
     * 35 conflicts with already recovered 32; 36 is unreachable. */
    int32_t a[]={32,32,33,34,35,36}, b[]={0,16,0,32,34,33};
    int32_t oa[]={32,33,35}, ob[]={0,0,32};
    assert(recover_tiny_boundary_faces(arena,labels,37,7,a,b,6,oa,ob,3,0)==0);
    assert(memcmp(labels,original,sizeof labels)==0);
    assert(recover_tiny_boundary_faces(arena,labels,37,7,a,b,6,oa,ob,3,1)==2);
    for(int i=0;i<32;i++) assert(labels[i]==original[i]);
    assert(labels[32]==1 && labels[34]==1);
    assert(labels[33]==3 && labels[35]==5 && labels[36]==6);
    int32_t first[37];memcpy(first,labels,sizeof labels);
    memcpy(labels,original,sizeof labels);
    assert(recover_tiny_boundary_faces(arena,labels,37,7,a,b,6,oa,ob,3,1)==2);
    assert(memcmp(first,labels,sizeof labels)==0);
    /* 32 initially blocks on A, then retries when 33 supplies B. */
    int32_t ra[]={32,33,32}, rb[]={0,16,33}, ro_a[]={32}, ro_b[]={0};
    memcpy(labels,original,sizeof labels);
    assert(recover_tiny_boundary_faces(arena,labels,37,7,ra,rb,3,ro_a,ro_b,1,1)==2);
    assert(labels[32]==1 && labels[33]==1);
    /* Invalid input and a pre-existing joined constraint leave labels intact. */
    memcpy(labels,original,sizeof labels);
    int32_t invalid[]={37};
    assert(recover_tiny_boundary_faces(arena,labels,37,7,invalid,rb,1,oa,ob,3,1)==0);
    int32_t joined_a[]={0}, joined_b[]={1};
    assert(recover_tiny_boundary_faces(arena,labels,37,7,a,b,6,joined_a,joined_b,1,1)==0);
    assert(memcmp(labels,original,sizeof labels)==0);
    /* Distinct vertices with coincident projections saturate the raw-pair
     * cap. The detector must expose incomplete evidence to the recovery. */
    int32_t faces[64*3]; float projection[64*3*2];
    for(int t=0;t<64;t++) {
        for(int j=0;j<3;j++) faces[3*t+j]=3*t+j;
        float xy[]={0,0,1,0,0,1};
        memcpy(projection+6*t,xy,sizeof xy);
    }
    int32_t *pa=NULL,*pb=NULL;size_t np=0;
    assert(detect_overlaps(arena,faces,64,projection,192,&pa,&pb,&np)==0);
    assert(np>0);
    assert(detect_overlaps(arena,faces,2,projection,6,&pa,&pb,&np)==1);
    assert(np==1);
    Arena_dispose(&arena);
    puts("boundary graft: alternative owner, blocked, chain, current conflicts, retry, determinism, fail-closed and detector saturation passed");
    return 0;
}
