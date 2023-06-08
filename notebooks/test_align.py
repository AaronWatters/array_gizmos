
from H5Gizmos import serve
import numpy as np

from array_gizmos import align_volumes

def get_array(from_path):
    "This function defines how to read a label volume as a np array."
    loaded = np.load(from_path)
    return loaded["a"]

def get_volume_for_ts(ts):
    "This function defines how to use a label number to get a label volume."
    path = "a%s.npz" % ts
    return get_array(path)

# Specify the geometry of the label volumes
dI = 0.014  # The distance between A[1,1,1] and A[2,1,1]
dJ = 0.00158  # The distance between A[1,1,1] and A[1,2,1]
dK = 0.00168  # The distance between A[1,1,1] and A[1,1,2]
dIJK = (dI, dJ, dK)

# Use resampling to force the voxels to have this cubic side size:
dvoxel = 0.005

# Create a VolumeSequence object for reading volume data by timestamp.
Seq = align_volumes.VolumeSequence(dIJK, get_volume_for_ts)

# Create a timestamp pair object using the Sequence and the required cubic side size.
Pair = align_volumes.TimeStampPair(374, 375, Seq, dvoxel)

# Start the user interface for comparing the volume Pair.
serve(Pair.link())
