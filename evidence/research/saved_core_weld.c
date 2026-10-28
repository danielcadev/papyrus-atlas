/* Saved-mesh adapter to the EXISTING ScrollFiesta ChartZipper implementation.
 * ScrollFiesta attribution/license remain in scrollfiesta-comparison/source.
 * No extraction, source repair, parameter tuning, or unarmed physical weld.
 * Invoke only via run_saved_core_weld.py in the guarded project wrapper.
 */
#include "common/arena.h"
#include "common/mesh_bin.h"
#include "common/pipeline_constants.h"
#include "flatten/topology_invariants.h"
#include "remesh/chart_zipper.h"
#include "remesh/orient_mesh.h"
#include "remesh/seam_planes.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void topology(FILE *f, const TopologyAuditReport *r)
{
    fprintf(f,"{\"components\":%zu,\"disks\":%zu,\"all_disks\":%s,"
        "\"invalid_surfaces\":%zu,\"inconsistent_winding\":%zu,"
        "\"beta1\":%lld,\"component_details\":[",r->face_components,
        r->disk_components,r->all_components_are_disks?"true":"false",
        r->invalid_surface_components,r->inconsistent_winding_components,
        (long long)r->beta_1);
    for(size_t i=0;i<r->face_components;i++) {
        const TopologyComponentInvariant *c=&r->component[i];
        fprintf(f,"%s{\"id\":%zu,\"faces\":%zu,\"boundary_loops\":%zu,"
            "\"nonmanifold_edges\":%zu,\"nonmanifold_vertices\":%zu,"
            "\"defect_mask\":%u}",i?",":"",i,c->faces,c->boundary_loops,
            c->nonmanifold_edges,c->nonmanifold_vertices,c->defect_mask);
    }
    fprintf(f,"]}");
}

int main(int argc,char **argv)
{
    if(argc!=4 && argc!=5) return 2;
    /* input VMESH, new candidate VMESH, new native JSON, optional calibration */
    MeshBinData m={0};
    TopologyAuditReport before={0}, after={0};
    ChartZipperStats zs={0};
    BpaBridgeGate gate={0};
    ChartZipperParams p;
    ChartZipper_default_params(&p);
    const float origin[3]={1840,2320,4048};
    if(MeshBin_read_malloc(argv[1],&m)!=0 || m.nv>100000 || m.nf>50000) return 3;
    float *local=malloc(m.nv*3*sizeof(float));
    uint8_t *used=calloc(m.nv,1);
    if(!local||!used) return 3;
    for(size_t v=0;v<m.nv;v++) for(int d=0;d<3;d++) {
        local[3*v+d]=m.verts[3*v+d]-origin[d];
        if(!isfinite(local[3*v+d]) ||
           (double)local[3*v+d]+origin[d]!=(double)m.verts[3*v+d]) return 3;
    }
    for(size_t i=0;i<m.nf*3;i++) used[m.faces[i]]=1;
    SeamPlane planes[64];
    size_t np=SeamPlanes_detect(local,m.nv,used,p.cube_size,p.band,planes,64);
    int plane_ok=np==1 && planes[0].axis==2 && planes[0].coord==128;
    if(TopologyAudit_analyze(local,m.nv,m.faces,m.nf,NULL,&before)!=0) return 3;
    FILE *report=fopen(argv[3],"wx"); if(!report) return 3;
    fprintf(report,"{\"before\":");topology(report,&before);
    fprintf(report,",\"plane_count\":%zu,\"plane_world_x_4176_verified\":%s",
        np,plane_ok?"true":"false");
    /* The preflight is useful without inventing missing anatomical calibration. */
    if(argc==4 || !plane_ok || !before.all_components_are_disks ||
       before.inconsistent_winding_components) {
        fprintf(report,",\"weld_attempted\":false,\"calibration_supplied\":%s}\n",
            argc==5?"true":"false");
        fclose(report);return 4;
    }
    FILE *cal=fopen(argv[4],"r"); size_t n=0;
    if(!cal || fscanf(cal,"%lf %zu",&gate.pitch,&n)!=2 ||
       !isfinite(gate.pitch) || gate.pitch<=0 || n<2 || n>4096) return 3;
    double *axis=malloc(n*3*sizeof(double));if(!axis)return 3;
    for(size_t i=0;i<n;i++) {
        double z,y,x;
        if(fscanf(cal,"%lf %lf %lf",&z,&y,&x)!=3 ||
           !isfinite(z)||!isfinite(y)||!isfinite(x)) return 3;
        axis[i]=z-origin[0];axis[n+i]=y-origin[1];axis[2*n+i]=x-origin[2];
        if(i && axis[i]<=axis[i-1])return 3;
    }
    fclose(cal);gate.axis_z=axis;gate.axis_y=axis+n;gate.axis_x=axis+2*n;
    gate.axis_n=n;gate.tol=SEAM_WIND_TOL_DEFAULT_TURNS;
    gate.hard=SEAM_WIND_HARD_TOL_DEFAULT_TURNS;
    Arena_T arena=Arena_new_sized(1024*1024);
    int32_t *faces=NULL;size_t nf=0,nb=0,flipped=0,cc=0,resid=0;
    if(ChartZipper_process(arena,local,m.nv,m.faces,m.nf,
        before.vertex_component,before.face_components,&gate,&p,
        &faces,&nf,&nb,&zs)!=0) return 5;
    /* Existing grid_weld reconciliation. Any source flip is detected below
     * and by the independent global-coordinate multiset certificate. */
    OrientMesh_consistent(arena,local,m.nv,NULL,faces,nf,&flipped,&cc,&resid);
    if(TopologyAudit_analyze(local,m.nv,faces,nf,NULL,&after)!=0)return 5;
    int prefix=nf>=m.nf && memcmp(faces,m.faces,m.nf*3*sizeof(int32_t))==0;
    fprintf(report,",\"weld_attempted\":true,\"gate_armed\":true,"
        "\"source_prefix_exact\":%s,\"source_faces\":%zu,\"faces\":%zu,"
        "\"bridge_faces\":%zu,\"accepted_transactions\":%zu,"
        "\"embedded_certificate\":%s,\"orientation_flips\":%zu,"
        "\"orientation_residual\":%zu,\"candidates\":%zu,"
        "\"ambiguous\":%zu,\"geometry_rejected\":%zu,"
        "\"conflict_transactions\":%zu,\"after\":",
        prefix?"true":"false",m.nf,nf,nb,zs.accepted_transactions,
        zs.embedded_certificate?"true":"false",flipped,resid,zs.candidates,
        zs.ambiguous_candidates,zs.geometry_candidates,zs.conflict_transactions);
    topology(report,&after);fprintf(report,"}\n");if(fclose(report))return 5;
    /* This is a candidate, even if all internal guards passed. The Python
     * runner requires exact source retention and an all-triangle 3D audit. */
    if(MeshBin_write(argv[2],m.verts,m.nv,faces,nf,NULL)!=0)return 5;
    TopologyAudit_dispose(&before);TopologyAudit_dispose(&after);
    Arena_dispose(&arena);MeshBin_dispose(&m);free(local);free(used);free(axis);
    return 0;
}
