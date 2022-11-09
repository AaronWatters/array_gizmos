from . import colorizers
from . import operations3d
import numpy as np
from H5Gizmos import Stack, Slider, Image, CheckBoxes, Text, DropDownSelect

class ImageViewer:
    def __init__(self, array3d, name="3d volume"):
        self.name = name
        self.array3d = array3d
        shape = array3d.shape
        lshape = len(shape)
        self.shape = shape
        self.min = array3d.min()
        self.max = array3d.max()
        dtype = array3d.dtype
        self.colorizable = False
        if lshape == 3:
            print("3d array", shape, self.min, self.max)
            self.colors = False
            if np.issubdtype(dtype, np.integer):
                if self.min >= 0 and self.max <= 1000:
                    self.colorizable = True
                    print("colorizable")
        else:
            assert lshape == 4, "array must be 3d scalars or 4d with colors " + repr(shape)
            assert self.min >= 0 and self.max <= 255, "color intensities should be in range 0..255"
            self.colors = True
        (self.depth, self.width, self.height) = shape[:3]

    def get_image(self, layer, projection=None, colorize=False):
        result = layer0 = self.array3d[layer]
        if projection == "max_value":
            result = layer0 = self.array3d[layer:].max(axis=0)
        if projection == "extruded":
            result = layer0 = operations3d.extrude0(self.array3d[layer:])
        if self.colors:
            if self.max <= 1.0:
                # scale the colors
                result = (layer0 * 255.0).astype(np.ubyte)
        else:
            if colorize:
                #print("colorizing", layer0.shape)
                result = colorizers.colorize_array(result)
        return result

    async def gizmo(self, display_width=600):
        if display_width is None:
            display_width = self.width
        ratio = display_width / self.width
        display_height = ratio * self.height
        self.layer_slider = Slider(
            title="layer", 
            value=0, 
            minimum=0, 
            maximum=self.depth-1, 
            step=1, 
            on_change=self.draw_image)
        self.layer_slider.resize(width=display_width * 0.5)
        self.image_display = Image(height=display_height, width=display_width)
        projections = ["none", "max_value"]
        if self.colorizable:
            projections.append("extruded")
        self.selection = DropDownSelect(
            label_value_pairs=projections,
            selected_value="none",
            legend="projection: ",
            on_click=self.draw_image,
        )
        options = self.selection
        if self.colorizable:
            self.colorize_checkbox = CheckBoxes(
                label_value_pairs = ["colorize"],
                selected_values=["colorize"],
                on_click=self.draw_image,
            )
            options = [self.selection, self.colorize_checkbox]
        dash = Stack([
            "Image: " + repr([self.name, self.shape, self.min, self.max]),
            self.layer_slider, 
            options,
            self.image_display,
        ])
        dash.css({"background-color": "#ddd"})
        await dash.link()
        self.draw_image()

    def draw_image(self, *ignored):
        layer = self.layer_slider.value
        [projection] = self.selection.selected_values
        colorize = False
        if self.colorizable:
            if self.colorize_checkbox.selected_values:
                colorize = True
        image = self.get_image(layer, projection, colorize)
        self.image_display.change_array(image)
