
from H5Gizmos import serve
import numpy as np

def get_array(from_path):
    loaded = np.load(from_path)
    return loaded["a"]

a374 = get_array("a374.npz")
a375 = get_array("a375.npz")

from array_gizmos import rot3d_gizmos

OL = rot3d_gizmos.OverlayedLabels(a374, a375)

serve(OL.gizmo())
