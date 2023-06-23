"""
3d rotations and translations in airplane and cartesian modes.
"""

import numpy as np
from numpy.linalg import norm

def ar(*vectors):
    "Convenience."
    return np.array(vectors, dtype=np.float64)

def apply_transform_matrix(transform_matrix, v3d):
    [x, y, z] = v3d
    v4d = ar([x, y, z, 1]).reshape((4, 1))
    result4d = np.dot(transform_matrix, v4d)
    print(v4d.ravel(), "-->", result4d.ravel())
    return result4d.ravel()[:3]

def translation_matrix(tx, ty, tz):
    return ar(
        [1, 0, 0, tx,],
        [0, 1, 0, ty,],
        [0, 0, 1, tz,],
        [0, 0, 0, 1]
    )

def yaw_matrix(radians):
    "Yaw: rotation about X axis."
    c = np.cos(radians)
    s = np.sin(radians)
    return ar(
        [1, 0, 0, 0],
        [0, c,-s, 0],
        [0, s, c, 0],
        [0, 0, 0, 1],
    )

def roll_matrix(radians):
    "Roll: rotation about Z axis."
    c = np.cos(radians)
    s = np.sin(radians)
    return ar(
        [c,-s, 0, 0],
        [s, c, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    )

def pitch_matrix(radians):
    "Pitch: rotation about Y axis."
    c = np.cos(radians)
    s = np.sin(radians)
    return ar(
        [c, 0, s, 0],
        [0, 1, 0, 0],
        [-s,0, c, 0],
        [0, 0, 0, 1],
    )

def airplane_matrix(translate, yaw, pitch, roll):
    T = translation_matrix(*translate)
    R = roll_matrix(roll)
    Y = yaw_matrix(yaw)
    P = pitch_matrix(pitch)
    TYPR = np.dot(T,
                  np.dot(Y,
                         np.dot(P, R)))
    return TYPR

"""historical
def get_translation(TYPR):
    return apply_transform_matrix(TYPR, [0,0,0])

def get_yaw(YPR):
    [x,y,z] = apply_transform_matrix(YPR, [0,0,1])
    h = norm([x, z])
    print("yaw y, h", y, h)
    return np.arctan2(y, h)

def get_pitch(PR):
    print("get pitch")
    [x,y,z] = apply_transform_matrix(PR, [0,0,1])
    return np.arctan2(x, z)

def get_roll(R):
    [x,y,z] = apply_transform_matrix(R, [1, 0, 0])
    return np.arctan2(x, y)

def airplane_parameters(TYPR):
    "Determine the airplane parameters equivalent to translation and rotation matrix."
    translation = get_translation(TYPR)
    inv_t = -translation
    invtM = translation_matrix(*inv_t)
    YPR = np.dot(invtM, TYPR)
    print("YPR")
    print(YPR)
    yaw = get_yaw(YPR)
    invY = yaw_matrix(-yaw)
    PR = np.dot(invY, YPR)
    print("yaw", yaw, "PR")
    print(PR)
    pitch = get_pitch(PR)
    invP = pitch_matrix(-pitch)
    R = np.dot(invP, PR)
    roll = get_roll(R)
    return (translation, roll, pitch, yaw)
"""

# https://www.geometrictools.com/Documentation/EulerAngles.pdf
# Factor RxRyRz case.

def airplane_parameters(TYPR, epsilon=1e-10):
    sy = TYPR[0,2]
    assert TYPR.shape == (4,4), "not a transform matrix: " + TYPR.shape
    assert np.all(np.abs(TYPR[:3,:3]) < 1 + epsilon), "bad rotation: " + repr(TYPR)
    one = 1 - epsilon
    if sy < one:
        if sy > -one:
            thetay = np.arcsin(sy)
            thetax = np.arctan2(-TYPR[1,2], TYPR[2,2])
            thetaz = np.arctan2(-TYPR[0,1], TYPR[0,0])
        else: # sy ~= -1
            thetay = -np.pi / 2.0
            thetax = -np.arctan2(TYPR[1,0], TYPR[1,1])
            thetaz = 0.0
    else: # sy ~= 1
        thetay = np.pi / 2.0
        thetax = np.arctan2(TYPR[1,0], TYPR[1,1])
        thetaz = 0.0
    translation = TYPR[0:3, 3].ravel()
    return (translation, thetax, thetay, thetaz)
