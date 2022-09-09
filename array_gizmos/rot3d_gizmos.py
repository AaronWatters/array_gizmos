"""
Gizmo visualizations for 3d array rotations.
"""

from turtle import color
import numpy as np
import math
from . import operations3d
from H5Gizmos import Stack, Slider, Image, Shelf
from . import colorizers

def strideLabelsAndImage(labels, image, width=600, strideI=True):
    slicing = operations3d.positive_slicing(labels)
    slabels = operations3d.slice3(labels, slicing)
    simage = operations3d.slice3(image, slicing)
    tlabels = slabels
    timage = simage
    if strideI:
        [I, J, K] = simage.shape
        m = min(J, K)
        if I < m:
            stride = int(m / I)
            tlabels = slabels[:, ::stride, ::stride]
            timage = simage[:, ::stride, ::stride]
    return LabelsAndImage(tlabels, timage, width=width)

class LabelsAndImage:

    def __init__(self, labels, image, width=600):
        assert labels.shape == image.shape, "shapes don't match: " + repr([labels.shape, image.shape])
        self.labels = labels
        self.image = image
        self.width = width
        self.image_buffer = operations3d.rotation_buffer(image)
        self.labels_buffer = operations3d.rotation_buffer(labels)

    async def gizmo(self):
        width = self.width
        limit = np.pi
        self.theta_slider = Slider(
            title="theta", 
            value=0, 
            minimum=-limit, 
            maximum=+limit, 
            step=0.02, 
            on_change=self.draw_image)
        self.theta_slider.resize(width=width)
        self.phi_slider = Slider(
            title="theta", 
            value=0, 
            minimum=-limit, 
            maximum=+limit, 
            step=0.02, 
            on_change=self.draw_image)
        self.phi_slider.resize(width=width)
        self.image_display = Image(height=width, width=width)
        self.labels_display = Image(height=width, width=width)
        displays = Shelf([
            self.image_display,
            self.labels_display,
        ])
        dash = Stack([ 
            self.theta_slider,
            self.phi_slider,
            displays,
        ])
        await dash.link()
        self.draw_image()
 
    def draw_image(self, *ignored):
        theta = self.theta_slider.value
        phi = self.phi_slider.value
        rotated_img = operations3d.rotate3d(self.image_buffer, theta, phi)
        rotated_labels = operations3d.rotate3d(self.labels_buffer, theta, phi)
        proj_img = rotated_img.max(axis=0)
        proj_labels = operations3d.extrude0(rotated_labels)
        scale_img = colorizers.scale256(proj_img)
        color_labels = colorizers.colorize_array(proj_labels)
        self.image_display.change_array(scale_img)
        self.labels_display.change_array(color_labels)
        