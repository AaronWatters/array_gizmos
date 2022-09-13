"""
Helpers for colorizing array displays.
"""

from . import color_list
import numpy as np

def colorize_array(a, color_mapping_array=None):
    if color_mapping_array is None:
        maxlabel = a.max()
        color_choices = [(0,0,0)] + color_list.get_colors(maxlabel)
        color_mapping_array = np.array(color_choices, dtype=np.ubyte)
    shape = a.shape
    colors = color_mapping_array[a.flatten()]
    colorized_array = colors.reshape(shape + (3,))
    return colorized_array

def scale256(img, epsilon=1e-11):
    img = np.array(img, dtype=np.float)
    m = img.min()
    M = img.max()
    D = M - m 
    if D < epsilon:
        D = epsilon
    scaled = (255.0 * (img - m)) / D
    return scaled.astype(np.ubyte)

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
