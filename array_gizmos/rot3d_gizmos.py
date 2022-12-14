"""
Gizmo visualizations for 3d array rotations.
"""

import numpy as np
from . import operations3d
from H5Gizmos import Stack, Slider, Image, Shelf, Button, Text, RangeSlider
from . import colorizers
from . import color_list

def adjusted_labels_and_image(labels, image, width=600, adjustment="reduce"):
    slicing = operations3d.positive_slicing(labels)
    slabels = operations3d.slice3(labels, slicing)
    simage = operations3d.slice3(image, slicing)
    tlabels = slabels
    timage = simage
    if adjustment == "reduce":
        tlabels = operations3d.reduced_shape(slabels)
        timage = operations3d.reduced_shape(simage)
    elif adjustment == "expand":
        tlabels = operations3d.expanded_shape(slabels)
        timage = operations3d.expanded_shape(simage)
    elif adjustment is not None:
        try:
            size = int(adjustment)
        except ValueError:
            raise ValueError("adjustment should be reduce, expand, integer or None: " + repr(adjustment))
        tlabels = operations3d.specific_shape(slabels, size)
        timage = operations3d.specific_shape(simage, size)
    return LabelsAndImage(tlabels, timage, width=width)

class LabelsAndImage:
    # xxx Historical???

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
        
class AdjustableLabelsAndImage:

    def __init__(self, labels, image, width=600, title="Image and Labels"):
        if image is not None:
            assert labels.shape == image.shape, "shapes don't match: " + repr([labels.shape, image.shape])
        self.title = title
        self.labels = labels
        self.image = image
        self.width = width
        slicing = operations3d.positive_slicing(labels)
        self.slabels = operations3d.slice3(labels, slicing)
        if image is not None:
            self.simage = operations3d.slice3(image, slicing)
        self.multi_resolution = False

    def info(self, msg):
        self.info_area.text(msg)

    async def gizmo(self):
        self.info_area = Text("Image and Labels")
        shape = self.slabels.shape
        min_res = min(*shape)
        # force min to be 100 or less
        min_res = min(100, min_res)
        max_res = max(*shape)
        # but at least 50 if possible
        if max_res > 50:
            min_res = max(50, min_res)
        self.default_resolution = min_res
        width = self.width
        reset_button = Button("Reset", on_click=self.reset_click)
        top_controls = reset_button
        if (min_res < max_res):
            self.multi_resolution = True
            self.resolution_slider = Slider(
                title="resolution", 
                value=min_res, 
                minimum=min_res, 
                maximum=max_res, 
                step=1, 
                on_change=self.setup_images)
            self.resolution_slider.resize(width=width)
            top_controls = ["resolution", self.resolution_slider, reset_button]
        limit = np.pi
        self.theta_slider = Slider(
            title="theta", 
            value=0, 
            minimum=-limit, 
            maximum=+limit, 
            step=0.02, 
            on_change=self.draw_image)
        self.theta_slider.resize(width=width)
        [I, J, K] = shape
        self.I_slider = RangeSlider(
            minimum=0,
            maximum=I,
            low_value=0,
            high_value=I,
            step=1,
            title="I slider",
            on_change=self.setup_images,
        )
        self.I_slider.resize(width=width)
        self.J_slider = RangeSlider(
            minimum=0,
            maximum=J,
            low_value=0,
            high_value=J,
            step=1,
            title="J slider",
            on_change=self.setup_images,
        )
        self.J_slider.resize(width=width)
        self.K_slider = RangeSlider(
            minimum=0,
            maximum=K,
            low_value=0,
            high_value=K,
            step=1,
            title="K slider",
            on_change=self.setup_images,
        )
        self.K_slider.resize(width=width)
        self.phi_slider = Slider(
            title="theta", 
            value=0, 
            minimum=-limit, 
            maximum=+limit, 
            step=0.02, 
            on_change=self.draw_image)
        self.phi_slider.resize(width=width)
        self.labels_display = Image(height=width, width=width)
        if self.image is None:
            displays = self.labels_display
        else:
            self.image_display = Image(height=width, width=width)
            displays = Shelf([
                self.image_display,
                self.labels_display,
            ])
        self.slicing_info = Text("Slicing: none")
        dash = Stack([ 
            self.title,
            self.info_area,
            top_controls,
            ["theta", self.theta_slider],
            ["phi", self.phi_slider],
            displays,
            ["I", self.I_slider],
            ["J", self.J_slider],
            ["K", self.K_slider],
            self.slicing_info,
        ])
        dash.css({"background-color": "#ddd"})
        await dash.link()
        self.setup_images()

    def get_resolution(self):
        if self.multi_resolution:
            return self.resolution_slider.value
        else:
            return self.default_resolution

    def chunk(self, array):
        size = self.get_resolution()
        [imin, imax] = self.I_slider.values
        [jmin, jmax] = self.J_slider.values
        [kmin, kmax] = self.K_slider.values
        self.slicing_info.html(repr( ([imin, imax], [jmin, jmax], [kmin, kmax])))
        segment = np.zeros(array.shape, dtype=array.dtype)
        segment[imin:imax, jmin:jmax, kmin:kmax] = array[imin:imax, jmin:jmax, kmin:kmax]
        truncated = operations3d.specific_shape(segment, size)
        buffer = operations3d.rotation_buffer(truncated)
        return buffer

    def setup_images(self, *ignored):
        size = self.get_resolution()
        self.info("... Setting image resolution: " + repr(size))
        self.labels_buffer = self.chunk(self.slabels)
        if self.image is not None:
            self.image_buffer = self.chunk(self.simage)
        #self.tlabels = operations3d.specific_shape(self.slabels, size)
        #self.timage = operations3d.specific_shape(self.simage, size)
        #self.image_buffer = operations3d.rotation_buffer(self.timage)
        #self.labels_buffer = operations3d.rotation_buffer(self.tlabels)
        #self.info("drawing images at resolution: " + repr(size))
        self.labels_display.on_pixel(self.pixel_callback)
        self.selected_label = None
        self.draw_image()

    def draw_image(self, *ignored):
        theta = self.theta_slider.value
        phi = self.phi_slider.value
        self.info("rotating: " + repr([theta, phi]))
        if self.image is not None:
            rotated_img = operations3d.rotate3d(self.image_buffer, theta, phi)
        rotated_labels = operations3d.rotate3d(self.labels_buffer, theta, phi)
        self.info("projection: " + repr(self.labels_buffer.shape))
        if self.image is not None:
            proj_img = rotated_img.max(axis=0)
        proj_labels = operations3d.extrude0(rotated_labels)
        self.proj_labels = proj_labels
        if self.image is not None:
            scale_img = colorizers.scale256(proj_img)
        color_labels = colorizers.colorize_array(proj_labels)
        self.proj_labels = proj_labels
        if self.image is not None:
            #color_image = colorizers.pseudo_colorize(scale_img)
            color_image = colorizers.to_rgb(scale_img, scaled=False)
            label = self.selected_label
            if label:
                boundary = colorizers.boundary_image(label, proj_labels)
                color = color_list.indexed_color(label-1)
                white = [255,255,255]
                color_image = colorizers.overlay_color(color_image, boundary, color)
                color_labels = colorizers.overlay_color(color_labels, boundary, white)
                self.info("highlighting: " + repr(label))
            # xxx mark selected label...
            self.image_display.change_array(color_image)
        self.labels_display.change_array(color_labels)

    def pixel_callback(self, event):
        row = event["pixel_row"]
        column = event["pixel_column"]
        labels = self.proj_labels
        label = labels[row, column]
        self.info("clicked label: " + repr(label))
        if label:
            self.selected_label = label
            self.draw_image()

    def reset_click(self, *ignored):
        self.I_slider.reset()
        self.J_slider.reset()
        self.K_slider.reset()
        self.resolution_slider.reset()
        