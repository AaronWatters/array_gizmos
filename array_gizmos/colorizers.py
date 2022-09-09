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
