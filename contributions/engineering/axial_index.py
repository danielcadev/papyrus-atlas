"""Exact threshold screening: omit vertices proven farther in Z than the gate."""
import numpy as np
from scipy.spatial import cKDTree

def axial_index(vertices, z, radius=16):
    dz=np.abs(vertices[:,0].astype(np.float64)-z)
    near=dz<=radius
    bound=float(dz[~near].min()) if (~near).any() else float('inf')
    return (cKDTree(vertices[near]) if near.any() else None),bound,int(near.sum()),int((~near).sum())
