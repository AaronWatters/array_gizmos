"""
View source image and segmentation layers paired and mixed.
"""

from . import colorizers
from . import loaders
import numpy as np
import H5Gizmos as gz

speckle = True

def segment_paths(label_path, image_path, name="segmentation layers",verbose=True):
    if verbose:
        print("loading label volume from", label_path)
    labelVolume = loaders.load_tiff(label_path)
    if verbose:
        print("loading image volume from", image_path)
    imageVolume = loaders.load_tiff(image_path)
    return SegmentationLayers(labelVolume, imageVolume, name=name)

def serve_segment_paths(label_path, image_path, name="segmentation layers", display_width=600):
    seg = segment_paths(label_path, image_path, name=name)
    gz.serve(seg.gizmo(display_width=display_width))

class SegmentationLayers:

    def __init__(self, labelVolume, imageVolume, name="segmentation layers"):
        # check that volumes are 3d
        assert len(labelVolume.shape) == 3, (
            "label volume must be 3d, not " + repr(labelVolume.shape)
        )
        # check that labelVolume and imageVolume have same shape
        assert labelVolume.shape == imageVolume.shape, (
            "label and image volumes must have same shape " + 
            repr(labelVolume.shape) + " " + repr(imageVolume.shape)
        )
        # labels should be integers
        assert np.issubdtype(labelVolume.dtype, np.integer), (
            "label volume should have integer type, not " + repr(labelVolume.dtype)
        )
        # labels should be positive
        assert labelVolume.min() >= 0, (
            "label volume should have non-negative values, min is " + repr(labelVolume.min())
        )
        self.name = name
        self.labelVolume = labelVolume
        self.imageVolume = imageVolume
        self.max_label = labelVolume.max()
        # get colorizer mapping array
        color_choices = [(0,0,0)] + colorizers.color_list.get_colors(self.max_label)
        self.color_mapping_array = np.array(color_choices, dtype=np.ubyte)
        self.max_layer = labelVolume.shape[0]
        self.current_layer = self.max_layer // 2
        (self.width, self.height) = labelVolume.shape[1:]
        self.mix_lambda = 0.5
        #self.get_images()

    def get_images(self):
        layer = self.current_layer
        label_layer = self.labelVolume[layer]
        image_layer = self.imageVolume[layer]
        colorized_labels = colorizers.colorize_array(label_layer, self.color_mapping_array)
        if speckle:
            colorized_labels = colorizers.speckle_background(colorized_labels, label_layer)
        ilayer = colorizers.scale256(image_layer)
        gray_image = np.stack([ilayer, ilayer, ilayer], axis=-1)
        self.label_image = colorized_labels
        self.intensity_image = ilayer.astype(np.ubyte)
        self.mixed_image = (
            (self.mix_lambda * colorized_labels) + 
            ((1.0 - self.mix_lambda) * gray_image)
        ).astype(np.ubyte)

    def update_image(self):
        self.get_images()
        self.image_display.change_array(self.mixed_image, scale=False, url=False)

    def change(self, event):
        self.current_layer = int(self.layer_slider.value)
        self.mix_lambda = float(self.mix_slider.value)
        self.update_image()

    async def gizmo(self, display_width=600):
        ratio = display_width / self.width
        display_height = int(ratio * self.height)
        self.image_display = gz.Image(
            height=display_height, 
            width=display_width, 
            pixelated=True
        )
        #self.image_display.on_pixel(self.move, "mousemove")
        self.layer_text = gz.Text(f"Layer {self.current_layer} of {self.max_layer - 1}")
        self.layer_slider = gz.Slider(
            title="layer", 
            value=self.current_layer, 
            minimum=0, 
            maximum=self.max_layer - 1, 
            step=1, 
            on_change=self.change,
        )
        self.layer_slider.resize(width=display_width * 0.5)
        self.mix_slider = gz.Slider(
            title="mix", 
            value=self.mix_lambda, 
            minimum=0, 
            maximum=1, 
            step=0.01, 
            on_change=self.change,
        )
        self.mix_slider.resize(width=display_width * 0.5)
        self.dash = gz.Stack([
            self.name,
            self.layer_text,
            self.layer_slider,
            self.image_display,
            ["mix:", self.mix_slider],
        ])
        await self.dash.link()
        self.update_image()
        return self.dash
    