
"""
Segmentation Editor

Interactive tool for editing segmentation masks in images.

Click: change IJK position.
Shift + Click: change selected label.
Ctrl + Click: Update region with selected label.
"""

import numpy as np
import H5Gizmos as h5
from . import color_list
from . import colorizers

def print(*args, **kwargs):
    from H5Gizmos.python.gizmo_server import force_print
    force_print(*args, **kwargs)

class VolumeMix:
    def __init__(
            self, 
            volumeImage, 
            volumeMask, 
            maxLabel=None, 
            dI=1, 
            dJ=1, 
            dK=1,
            zoom=1.0,
            dw=10,):
        self.zoom = zoom
        self.volumeImage = volumeImage
        self.volumeMask = volumeMask
        print("VolumeMix initialized with shapes:", volumeImage.shape, volumeMask.shape)
        self.dI = dI
        self.dJ = dJ
        self.dK = dK
        self.dw = dw
        if maxLabel is None:
            self.maxLabel = volumeMask.max()
        else:
            self.maxLabel = maxLabel
        color_choices = [(0,0,0)] + color_list.get_colors(self.maxLabel)
        self.color_mapping_array = np.array(color_choices, dtype=np.ubyte)
        self.shape = np.array(volumeImage.shape)
        self.IJK = self.shape[:3] // 2
        mixJK = imageMix(maxLabel=self.maxLabel, dI=dJ, dJ=dK, volumeIndices=(1, 2), parent=self, dw=dw)
        mixJI = imageMix(maxLabel=self.maxLabel, dI=dI, dJ=dJ, volumeIndices=(1, 0), parent=self, dw=dw)
        mixIK = imageMix(maxLabel=self.maxLabel, dI=dI, dJ=dK, volumeIndices=(0, 2), parent=self, dw=dw)
        self.mixes = {
            "JK": mixJK,
            "JI": mixJI,
            "IK": mixIK,
        }
        self.positionMixes()
        self.selectedLabel = 0  # Default selected label

    def paint(self, IJK):
        """
        Paint the selected label at the specified IJK position.
        """
        if self.selectedLabel < 0 or self.selectedLabel >= len(self.color_mapping_array):
            raise ValueError("Selected label out of range: " + str(self.selectedLabel))
        print("Painting label", self.selectedLabel, "at position", IJK)
        mask = self.volumeMask
        shape = np.array(mask.shape)
        I, J, K = IJK
        si, sj, sk = shape[:3]
        dw = self.dw
        wI = max(1, dw // self.dI)
        wJ = max(1, dw // self.dJ)
        wK = max(1, dw // self.dK)
        i1 = max(0, I - wI)
        i2 = min(si - 1, I + wI)
        j1 = max(0, J - wJ)
        j2 = min(sj - 1, J + wJ)
        k1 = max(0, K - wK)
        k2 = min(sk - 1, K + wK)
        self.volumeMask[i1:i2+1, j1:j2+1, k1:k2+1] = self.selectedLabel
        for mix in self.mixes.values():
            mix.slice_volumes(self.volumeImage, self.volumeMask, IJK)

    def selectedColor(self):
        return self.color_mapping_array[self.selectedLabel]
    
    def changeLabel(self, label):
        """
        Change the selected label for the segmentation.
        """
        if label < 0 or label >= len(self.color_mapping_array):
            raise ValueError("Label out of range: " + str(label))
        self.selectedLabel = label
        color = self.selectedColor()
        print("Selected label:", label, "Color:", color)
        self.colorDiv.css({
            "backgroundColor": color_list.rgbhtml(self.selectedColor()),
        })

    def positionMixes(self, IJK=None):
        #p(("========= Positioning mixes with IJK:", IJK)
        shape = self.shape
        if IJK is None:
            IJK = shape // 2
        self.IJK = IJK
        assert np.all(IJK < shape[:3]), "IJK indices out of bounds: " + repr(IJK) + " for shape: " + repr(shape )
        selectedLabel = self.volumeMask[IJK[0], IJK[1], IJK[2]]
        #self.changeLabel(selectedLabel) # not needed here, done in click
        for mix in self.mixes.values():
            mix.slice_volumes(self.volumeImage, self.volumeMask, self.IJK)
        return selectedLabel

    def gizmo(self):
        """
        Create a H5Gizmos gizmo for displaying the volume mix.
        """
        self.positionMixes()
        zoom = self.zoom
        self.colorDiv = h5.Html("<div>color</div>")
        color = color_list.rgbhtml(self.selectedColor())
        print("Selected color:", color)
        self.colorDiv.css({
            "width": "100px",
            "height": "20px",
            "background-color": color,
            "border": "1px solid black",
        })
        display = h5.Stack([
            [
                self.mixes["JK"].gizmo(zoom),
                self.mixes["JI"].gizmo(zoom),
            ],
            [
                self.mixes["IK"].gizmo(zoom),
                self.colorDiv,
            ],
        ])
        return display
    
class imageMix:
    def __init__(
            self, 
            image=None, 
            mask=None, 
            maxLabel=None, 
            dI=1, dJ=1, 
            volumeIndices=None,
            parent=None,
            dw=1):
        self.volumeIndices = volumeIndices
        self.image = image
        self.mask = mask
        self.dI = dI
        self.dJ = dJ
        self.dw = dw
        self.parent = parent
        if maxLabel is None:
            self.maxLabel = mask.max()
        else:
            self.maxLabel = maxLabel
        color_choices = [(0,0,0)] + color_list.get_colors(self.maxLabel)
        self.color_mapping_array = np.array(color_choices, dtype=np.ubyte)
        self.selected_color = (255,255,255)  # Default selected color
        self.selected_label = 0  # default to background
        self.lamda = 0.5  # default blending factor
        self.mousePosition = None
        self.display = None
        self.IJK = [0, 0, 0]  # Default IJK position
        self.tracking = False  # Whether to track mouse position

    def position3d(self, IJK, mouseposition):
        [a, b] = mouseposition
        #if self.transposed():
        #    [b, a] = [a, b]
        result = np.array(IJK)
        [index0, index1] = self.volumeIndices
        result[index0] = a
        result[index1] = b
        #p("position3d", IJK, mouseposition, self.volumeIndices, "->", result)
        self.IJK = result
        return result
    
    def projection2d(self, IJK):
        [index0, index1] = self.volumeIndices
        result = np.array([IJK[index0], IJK[index1]])
        return result

    def slicedIndex(self):
        volumeIndices = self.volumeIndices
        assert volumeIndices is not None, "volumeIndices must be set"
        all = set(range(3))
        other = all - set(volumeIndices)
        assert len(other) == 1, "Invalid volumeIndices " + repr(volumeIndices)
        return other.pop()
    
    def transposed(self):
        [i1, i2] = self.volumeIndices
        return i1 > i2

    def slice_volumes(self, volumeImage, volumeMask, IJK):
        """
        Slice the image and mask volumes at the specified IJK indices.
        """
        slicedIndex = self.slicedIndex()
        self.IJK = IJK
        self.mousePosition = self.projection2d(IJK)
        #p("Slicing volumes at IJK:", IJK, "slicedIndex:", slicedIndex, self.volumeIndices)
        def slice_volume(volume, IJK):
            [I, J, K] = IJK
            if slicedIndex == 0:
                result = volume[I, :, :]
            elif slicedIndex == 1:
                result = volume[:, J, :]
            elif slicedIndex == 2:
                result = volume[:, :, K]
            else:
                raise ValueError("Invalid slicedIndex: " + str(slicedIndex))
            if self.transposed():
                result = result.T
            return result
        image_slice = slice_volume(volumeImage, IJK)
        mask_slice = slice_volume(volumeMask, IJK)
        #p()
        #p("Indices:", IJK, "VolumeIndices", self.volumeIndices, "Sliced index:", slicedIndex)
        #p("From volumes:", volumeImage.shape, volumeMask.shape)
        #p("Sliced image shape:", image_slice.shape, "Sliced mask shape:", mask_slice.shape)
        return self.change_images(image_slice, mask_slice)

    def change_images(self, image, mask):
        imsh = image.shape
        msh = mask.shape
        assert imsh == msh, "Image and mask shapes must match: " + repr((imsh, msh))
        if len(imsh) !=2:
            raise ValueError("Image and mask must be 2D slices, got shapes: " + repr((imsh, msh)))
        self.image = image
        self.mask = mask
        if self.display is not None:
            self.update(self.lamda)

    def colorized_mask(self):
        return colorizers.colorize_array(self.mask, self.color_mapping_array)
    
    def rgb_image(self):
        return colorizers.to_rgb(self.image)
    
    def combined(self, lamda=0.5, mousePosition=None, selectedColor=None):
        """
        Combine the image and mask into a single RGB image.
        The mask is colorized and blended with the image.
        """
        if selectedColor is None:
            selectedColor = self.selected_color
        if mousePosition is None:
            mousePosition = self.mousePosition
        colorized_mask = self.colorized_mask()
        rgb_image = self.rgb_image()
        combined_image = (lamda * rgb_image + (1 - lamda) * colorized_mask).astype(np.ubyte)
        (rows, cols,) = combined_image.shape[:2]
        #p("mousePosition:", mousePosition, "selectedColor:", selectedColor, "shape:", combined_image.shape)
        if mousePosition is not None and selectedColor is not None:
            y, x = mousePosition
            #print("Mouse position:", x, y, "cols", cols, "rows", rows)
            if 0 <= x < cols and 0 <= y < rows:
                ##p( ("Drawing box at", x, y, "with color", selectedColor)
                # draw a di/dj box around the mouse position
                dw = self.dw
                if self.transposed():
                    wI = max(1, dw // self.dI)
                    wJ = max(1, dw // self.dJ)
                else:
                    wI = max(1, dw // self.dJ)
                    wJ = max(1, dw // self.dI)
                x1 = max(0, x - wI)
                x2 = min(cols-1, x + wI)
                y1 = max(0, y - wJ)
                y2 = min(rows-1, y + wJ)
                # just the border of the box
                combined_image[y1:y2, x1, :] = selectedColor
                combined_image[y1:y2, x2, :] = selectedColor
                combined_image[y1, x1:x2, :] = selectedColor
                combined_image[y2, x1:x2, :] = selectedColor
            else:
                print("Mouse position out of bounds:", mousePosition, "for image shape:", combined_image.shape)
        else:
            print("No mousePosition or selectedColor provided, skipping drawing box.")
        return combined_image
    
    def gizmo(self, zoom=1.0):
        """
        Create a H5Gizmos gizmo for displaying the combined image.
        """
        combined_image = self.combined()
        shape = combined_image.shape
        #p("for", self.volumeIndices, "shape:", shape, "dI:", self.dI, "dJ:", self.dJ)
        [I, J] = shape[:2]
        if (self.transposed()):
            width = int(J * self.dI)
            height = int(I * self.dJ)
        else:
            height = int(I * self.dI)
            width = int(J * self.dJ)
        self.panel = h5.Image(
            array=combined_image,
            width=width * zoom,
            height=height * zoom,
            pixelated=True,
        )
        self.panel.on_pixel(self.move, "mousemove")
        self.panel.on_pixel(self.click, "click")
        #self.display.on_pixel(self.move, "click")
        #return self.display
        self.lSlider = h5.Slider(
            title="Blending factor (lamda)", 
            value=self.lamda, 
            minimum=0.0, 
            maximum=1.0, 
            step=0.01, 
            on_change=self.update
        )
        self.lSlider.resize(width=width * 0.5)
        self.display = h5.Stack([
            self.lSlider,
            self.panel,
        ])
        return self.display
    
    def move0(self, event): # not used
        #self.display.#p(event)
        selectedColor = self.selected_color
        column = event["pixel_column"]
        row = event["pixel_row"]
        mousePosition = (row, column)
        lamda = self.lamda
        self.update(lamda=lamda, mousePosition=mousePosition, selectedColor=selectedColor)

    def click(self, event):
        self.tracking = not self.tracking
        label = self.move(event)
        shifted = event.get("shiftKey", False)
        if shifted:
            print("Shifted click painting at ", self.IJK)
            self.parent.paint(self.IJK)
            self.tracking = False # stop tracking after painting
        elif label is not None:
            print("Clicked label:", label, "at position:", self.IJK)
            self.parent.changeLabel(label)
        return label

    def move(self, event):
        if not self.tracking:
            return None
        column = event["pixel_column"]
        row = event["pixel_row"]
        #print("Click at row, col:", row, column, self.volumeIndices)
        mousePosition = (row, column)
        IJK = self.position3d(self.IJK, mousePosition)
        #print("Click at IJK:", IJK)
        if self.parent is not None:
            #oldIJK = self.parent.IJK
            label = self.parent.positionMixes(IJK)
            return label

    """ not used
    def position(self, IJK, volumeImage=None, volumeMask=None):
        mousePosition = []
        for index in self.volumeIndices:
            mousePosition.append(IJK[index])
        self.mousePosition = tuple(mousePosition)
        self.slice"""

    def update(self, lamda=0.5, mousePosition=None, selectedColor=None):
        """
        Update the combined image with new parameters.
        """
        self.lamda = lamda
        combined_image = self.combined(lamda, mousePosition, selectedColor)
        self.panel.change_array(combined_image)
