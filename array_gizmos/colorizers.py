"""
Helpers for colorizing array displays.
"""

from . import color_list
import numpy as np
from scipy import signal

def colorize_array(a, color_mapping_array=None):
    if color_mapping_array is None:
        maxlabel = a.max()
        color_choices = [(0,0,0)] + color_list.get_colors(maxlabel)
        color_mapping_array = np.array(color_choices, dtype=np.ubyte)
    shape = a.shape
    colors = color_mapping_array[a.flatten()]
    colorized_array = colors.reshape(shape + (3,))
    return colorized_array

def scale256(img, epsilon=1e-11, minimum=None):
    return scaleN(img, epsilon=epsilon, minimum=minimum, to_max=255.0, dtype=np.ubyte)

def scaleN(img, epsilon=1e-11, minimum=None, to_max=10000.0, dtype=np.int):
    img = np.array(img, dtype=np.float)
    m = img.min()
    if minimum is not None:
        m = minimum
    M = img.max()
    D = M - m 
    if D < epsilon:
        D = epsilon
    scaled = (to_max * (img - m)) / D
    return scaled.astype(dtype)

edge_array = np.array([
    [1,1,1],
    [1,-8,1],
    [1,1,1],
])

def boundary_image(labels, target_label, edge_array=edge_array):
    mask = (labels == target_label).astype(np.ubyte)
    test = signal.convolve2d(mask, edge_array, boundary='symm', mode='same')
    return (test!=0).astype(np.ubyte)

def center_shapes(A1, A2):
    """
    If A1 and A2 shapes don't match in 2d then embed into larger arrays
    """
    s1 = A1.shape[:2]
    s2 = A2.shape[:2]
    if s1 != s2:
        sM = (M1, M2) = tuple(np.maximum(s1, s2))
        def fit(A, M1, M2):
            (m1, m2) = A.shape[:2]
            Aout = np.zeros( (M1, M2) + A.shape[2:], dtype=A.dtype)
            shift1 = int((M1 - m1)/2)
            shift2 = int((M2 - m2)/2)
            Aout[shift1:shift1+m1, shift2:shift2+m2] = A
            return Aout
        if sM != s1:
            A1 = fit(A1, M1, M2)
        if sM != s2:
            A2 = fit(A2, M1, M2)
    return (A1, A2)


def overlay_color(img, mask, color, center=False):
    img = to_rgb(img, scaled=False)
    if center:
        (img, mask) = center_shapes(img, mask)
        if hasattr(color, "shape"):
            (img, color) = center_shapes(img, color)
    mask3 = np.zeros(mask.shape + (3,), dtype=np.ubyte)
    mask3[:] = mask.reshape(mask.shape + (1,))
    result = np.choose(mask3, [img, color])
    return result

def overlay_color_delete(img, mask, color, center=False):
    img = to_rgb(img, scaled=False)
    img2d = img.shape[:2]
    mshape = mask.shape
    if center and img2d != mshape:
        # reshape the mask centered in the img2d shape
        cmask = np.zeros(img2d, dtype=mask.dtype)
        (imgI, imgJ) = img2d
        (maskI, maskJ) = mshape
        def centered_indices(dest, source):
            dstart = sstart = 0
            dend = dest
            send = source
            if source <= dest:
                shift = int((dest - source) / 2)
                dstart = shift
                dend = shift + source
            else:
                assert source > dest
                skip = int((source - dest) / 2)
                sstart = skip
                send = skip + dest
            return (dstart, dend, sstart, send)
        (cIstart, cIend, mIstart, mIend) = centered_indices(imgI, maskI)
        (cJstart, cJend, mJstart, mJend) = centered_indices(imgJ, maskJ)
        cmask[cIstart: cIend, cJstart: cJend] = mask[mIstart: mIend, mJstart: mJend]
        mask = cmask
    assert mask.shape == img2d, repr([mask.shape, img2d])
    mask3 = np.zeros(mask.shape + (3,), dtype=np.ubyte)
    mask3[:] = mask.reshape(mask.shape + (1,))
    #color = np.array(color, dtype=np.ubyte).reshape((1,1,3))
    if hasattr(color, "shape"):
        assert color.shape == img.shape, "color shape doesn't match img: " +repr([color.shape, img.shape])
    else:
        color = np.array(color, dtype=np.ubyte).reshape((1,1,3))
    result = np.choose(mask3, [img, color])
    return result

def to_rgb(arr, scaled=True):
    "Make into a 3 color array if needed and rescale if requested."
    s = arr.shape
    ls = len(s)
    if ls > 2:
        assert ls == 3, "Array should be 2d grey or 2d rgb: " + repr(s)
        assert s[2] == 3, "Function expects 3 colors exactly: " + repr(s)
        if scaled:
            arr = scale256(arr)
        return arr
    assert (ls == 2), "Image array should be 2d: " + repr(s)
    s3 = s + (3,)
    s1 = s + (1,)
    if scaled:
        arr = scale256(arr)
    arr1 = arr.reshape(s1)
    result = np.zeros(s3, dtype=arr1.dtype)
    result[:] = arr1
    return result

# pseudocolor support
h = 255
white = [h, h, h]
yellow = [h, h, 0]
magenta = [h, 0, h]
magenta = [h, h//2, h] # lighter magenta to avoid blue streak
red = [h, 0, 0]
cyan = [0, h, h]
green = [0, h, 0]
blue = [0, 0, h]
black = [0, 0, 0]

interpolator = np.array([
    black,
    blue,
    green,
    cyan,
    magenta,
    red,
    yellow,
    white,
])

def interpolate255(i, interpolator=interpolator):
    assert i >= 0 and i <= 255
    nint = len(interpolator)
    lam = i * 1.0/255.0
    if lam == 1:
        return interpolator[-1].astype(np.int)
    ir = (nint - 1) * lam
    i0 = int(ir)
    i1 = i0 + 1
    if i1 >= nint:
        return interpolator[-1].astype(np.int)
    delta = ir - i0
    e0 = interpolator[i0]
    e1 = interpolator[i1]
    cr = (1 - delta) * e0 + delta * e1
    return cr.astype(np.int)

pseudo_color_mapping = np.array([interpolate255(i) for i in range(256)]).astype(np.ubyte)

def pseudo_colorize(a):
    return colorize_array(a, pseudo_color_mapping)

def enhance_contrast(img, cutoff=0.1, int_max=10000):
    if not np.issubdtype(img.dtype, np.integer):
        # convert to integer type
        img = scaleN(img, to_max=int_max)
    (unique, count) = np.unique(img, return_counts=True)
    size = img.size
    def breakpoint(delta):
        stop = delta * size
        total = 0
        for (i, c) in enumerate(count):
            total += c
            if total > stop:
                return i
        return len(count)
    low_index = breakpoint(cutoff)
    high_index = breakpoint(1.0 - cutoff)
    length = max(unique) + 1
    mapping = np.zeros((length,), dtype=np.ubyte)
    low = unique[low_index]
    high = unique[high_index]
    # print("low", low, "high", high)
    if low < high:
        delta = 255.0 / (high - low)
    else:
        delta = 255.0
    for i in range(length):
        if i < low:
            v = 0
        elif i > high:
            v = 255
        else:
            v = int(delta * (i - low))
        mapping[i] = v
    result = mapping[img]
    return result

