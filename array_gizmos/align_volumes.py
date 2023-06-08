"""
Tools for aligning microscopy label volumes.
"""

import numpy as np
from . import operations3d
import H5Gizmos as gz
from . import colorizers
from . import color_list
from jp_doodle import gz_aircraft_axes
from jp_doodle import gz_slider

class Volume3D:

    def __init__(self, array, corner000xyz = (0,0,0), dxdydz=(1,1,1), dtype=np.float32):
        #assert np.issubdtype(array.dtype, int), "array should be integral: " + repr(array.dtype)
        #print("Volume3D", array.dtype, array.shape, corner000xyz, dxdydz)
        assert array.min() >= 0, "array should be non-negative %s" % array.min()
        assert array.max() <= 2, "array should have values 0, 1, or 2 %s" % array.max()
        self.array = array
        self.corner000 = np.array(corner000xyz, dtype=dtype)
        self.dxdydz = np.array(dxdydz, dtype=dtype)
        M = self.dxdydz.max()
        assert M > 0, "voxel dimensions must be positive. " + repr(self.dxdydz)
        self.rectified = (M == self.dxdydz.min())
        self.dtype = dtype
        shape = np.array(array.shape)
        self.cubic = (shape.min() == shape.max())

    def nonzeros(self):
        slicing = operations3d.positive_slicing(self.array)
        mins = slicing[:, 0]
        corner = mins * self.dxdydz
        nonzero_array = operations3d.slice3(self.array, slicing)
        #print("nonzero", nonzero_array.shape)
        volume = Volume3D(nonzero_array, corner, self.dxdydz, self.dtype)
        return (volume, slicing)
    
    def rectify(self, dvoxel):
        dxdydz = (dvoxel,) * 3
        dI, dJ, dK = self.dxdydz
        rectified = operations3d.rectify(self.array, dI, dJ, dK, dvoxel)
        #(self.array.shape, "rectified", rectified.shape)
        return Volume3D(rectified, self.corner000, dxdydz, self.dtype)
    
    def dimensions(self):
        return np.array(self.array.shape) * self.dxdydz
    
    def centroid(self):
        return self.corner000 + 0.5 * self.dimensions()
    
    def minxyz(self):
        return self.corner000
    
    def maxxyz(self):
        return self.corner000 + self.dimensions()
    
    def width(self):
        "size of largest dimension"
        return self.dimensions().max()
    
    def voxel_size_for_resolution(self, resolution):
        assert resolution > 1, "resolution should be largish, positive: " + repr(resolution)
        return self.width() / resolution
    
    def index_xyz(self, xyz):
        return ((xyz - self.corner000) / self.dxdydz).astype(np.int32)
    
    def rotatable(self):
        assert self.rectified, "rectify before constructing rotatable: " + repr(self.dxdydz)
        centroid = self.centroid()
        dxdydz = self.dxdydz
        buffer = operations3d.rotation_buffer(self.array)
        buffer_corner = centroid - 0.5 * (np.array(buffer.shape) * dxdydz)
        return Volume3D(buffer, buffer_corner, dxdydz, self.dtype)
    
    def rotate(self, roll, pitch, yaw):
        #assert self.cubic, "only rotate cubic volume: " + repr(self.array.shape)
        buffer = operations3d.rotate3d(self.array, roll, -pitch, - yaw)
        return Volume3D(buffer, self.corner000, self.dxdydz, self.dtype)
    
    def translate(self, txyz):
        txyz = np.array(txyz, dtype=self.dtype)
        return Volume3D(self.array, self.corner000 + txyz, self.dxdydz, self.dtype)
    
    def speckle(self, ratio, stride=1):
        array = self.array
        if stride > 1:
            array = array[::stride, ::stride, ::stride]
        speckled = operations3d.speckle(array, ratio)
        return Volume3D(speckled, self.corner000, self.dxdydz, self.dtype)
    
    def combine_nonzeros(self, other):
        dxdydz = self.dxdydz
        #dtype = self.dtype
        #assert dtype == other.dtype, "only combine same dtypes."
        dtype = self.array.dtype
        #print(repr((dxdydz, other.dxdydz)))
        assert np.allclose(dxdydz, other.dxdydz), "only combine with similar dimensions."
        mins = np.minimum(self.minxyz(), other.minxyz())
        maxes = np.maximum(self.maxxyz(), other.maxxyz())
        extent = (maxes - mins) + dxdydz  # extra space
        combined_shape = (extent / dxdydz).astype(np.int32)
        buffer = np.zeros(combined_shape, dtype=dtype)
        result = Volume3D(buffer, mins, dxdydz, self.dtype)
        result.embed_positive(self)
        result.embed_positive(other)
        return result
    
    def embed_positive(self, other):
        m = self.minxyz()
        M = self.maxxyz()
        m0 = other.minxyz()
        M0 = other.maxxyz()
        assert np.all(m <= m0), "mins out of range: " + repr([m, m0])
        assert np.all(M >= M0), "maxes out of range: " + repr([M, M0])
        [i, j, k] = self.index_xyz(m0)
        [I, J, K] = other.array.shape
        sarray = self.array
        oarray = other.array
        positive = (oarray > 0)
        sarray[i:i+I, j:j+J, k:k+K] = np.where(positive, oarray, sarray[i:i+I, j:j+J, k:k+K])


class VolumeSequence:

    def __init__(self, dIJK, get_volume_for_ts):
        self.dIJK = np.array(dIJK, dtype=np.float64)
        self.get_volume_for_ts = get_volume_for_ts

    def get_volume(self, for_ts, dvoxel, marker=None):
        volume_array = self.get_volume_for_ts(for_ts)
        if marker is not None:
            # replace nonzeros with marker
            assert 0 < marker < 256, "marker should be positive unsigned byte value"
            volume_array = (volume_array != 0).astype(np.ubyte) * marker
        return TimeStampVolume(for_ts, self, volume_array, dvoxel)

class TimeStampVolume:

    def __init__(self, ts_num, from_sequence, volume_array, dvoxel):
        self.ts_num = ts_num
        self.from_sequence = from_sequence
        #self.volume_array = volume_array
        dxdydz = from_sequence.dIJK
        unsliced = Volume3D(volume_array, dxdydz=dxdydz)
        (self.sliced, self.slicing) = unsliced.nonzeros()
        self.width = self.sliced.width()
        self.dvoxel = dvoxel
        self.rectify(dvoxel)

    def json_parameters(self):
        return dict(
            description="Time stamp volume parameters",
            timestamp_number=self.ts_num,
            source_dimensions=self.dxdydz.tolist(),
            dvoxel=float(self.dvoxel),
        )

    def rectify(self, dvoxel):
        self.dvoxel = dvoxel
        self.rectified = self.sliced.rectify(dvoxel)
        self.rotatable = self.rectified.rotatable()
        self.rotated = self.rotatable
        self.translated = self.rotatable
        self.speckled = self.rotatable

    def transform(self, roll, pitch, yaw, txyz):
        self.rotated = self.speckled.rotate(roll, pitch, yaw)
        self.translated = self.rotated.translate(txyz)

    def combined(self, other):
        return self.translated.combine_nonzeros(other.translated)
    
    def speckle(self, ratio, stride=1):
        self.speckled = self.rotatable.speckle(ratio, stride)
        self.rotated = self.speckled
        self.translated = self.speckled

class TimeStampPair:


    colors = np.array([
        [0,0,0],
        [255,0,0],
        [0,255,255]
    ])

    def __init__(self, ts_volume1, ts_volume2, from_sequence, dvoxel):
        self.volume1 = from_sequence.get_volume(ts_volume1, dvoxel, marker=1)
        self.volume2 = from_sequence.get_volume(ts_volume2, dvoxel, marker=2)
        self.from_sequence = from_sequence
        self.dvoxel = dvoxel
        self.width = self.volume2.width

    async def link(self):
        dashboard = self.make_dashboard()
        await dashboard.link()
        self.sample_arrays()

    def make_dashboard(self, width=700):
        """Basic graphic layout."""
        ratios = "1 0.5 0.1 0.05 0.02 0.01".split()
        strides = "1 2 3 4 5".split()
        self.select_ratio = gz.DropDownSelect(ratios, selected_value="0.05", on_click=self.dropdown_callback,)
        self.ratio = 0.05
        self.select_ratio.resize(width=100)
        self.select_stride = gz.DropDownSelect(strides, selected_value="1", on_click=self.dropdown_callback,)
        self.stride = 1
        self.select_stride.resize(width=80)
        self.info_area = gz.Text("Overlayed segmentation")
        self.translation_area = gz.Text("translation: (0,0,0)")
        self.reset_button = gz.Button("Reset", on_click=self.reset_translations)
        self.rotations = gz_aircraft_axes.AircraftAxes(on_change=self.draw_image)
        self.rotations1 = gz_aircraft_axes.AircraftAxes(on_change=self.draw_image, )
        self.x_slider = gz.Slider(
            minimum=-10,
            maximum=10,
            on_change=self.draw_image,
            value=0,
            step=1,
        )
        self.y_slider = gz.Slider(
            minimum=-10,
            maximum=10,
            on_change=self.draw_image,
            value=0,
            step=1,
            orientation="vertical",
        )
        self.y_slider.resize(height=width * 0.95)
        self.z_slider = gz.Slider(
            minimum=-10,
            maximum=10,
            on_change=self.draw_image,
            value=0,
            step=1,
        )
        self.xyz_area = gz.Text("0,0,0")
        self.labels_display = gz.Image(height=width, width=width)
        dash = gz.Stack([
            self.info_area,
            [
                [
                    [
                        self.labels_display,
                        self.y_slider,
                    ],
                    self.z_slider,
                ],
                [
                    "speckle ratio", self.select_ratio,
                    "stride", self.select_stride,
                    "rotate both", self.rotations, 
                    "rotate newer", self.rotations1,
                    self.x_slider,
                    #self.y_slider,
                    #self.z_slider,
                ]
            ],
            [self.reset_button, self.translation_area],
        ])
        dash.css({"background-color": "#ddd"})
        self.dashboard = dash
        return dash
    
    def reset_translations(self, *ignored):
        self.x_slider.set_value(0)
        self.y_slider.set_value(0)
        self.z_slider.set_value(0)
        self.draw_image()

    def dropdown_callback(self, *ignored):
        """After gizmo is live, sample the volumes and compute the image display."""
        [ratio_str] = self.select_ratio.selected_values
        self.ratio = float(ratio_str)
        [stride_str] = self.select_stride.selected_values
        self.stride = int(stride_str)
        self.sample_arrays()
        self.draw_image()

    def sample_arrays(self, *ignored):
        ratio = self.ratio
        stride = self.stride
        self.volume1.speckle(ratio, stride)
        self.volume2.speckle(ratio, stride)

    def draw_image(self, *ignored):
        """After gizmo is live, compute the image display."""
        dwidth = self.width * 0.01
        roll = self.rotations.roll
        yaw = self.rotations.yaw
        pitch = self.rotations.pitch
        roll1 = self.rotations1.roll
        yaw1 = self.rotations1.yaw
        pitch1 = self.rotations1.pitch
        dx = dwidth * self.x_slider.value
        dy = - dwidth * self.y_slider.value
        dz = dwidth * self.z_slider.value
        translation = (dx, dy, dz)
        self.translation_area.text("translation: " + repr(translation))
        self.volume2.transform(roll1, pitch1, yaw1, translation)
        combined_volume = self.volume2.combined(self.volume1)
        rotated = combined_volume.rotate(roll, pitch, yaw)
        projected = operations3d.extrude0(rotated.array)
        #print("dtype", projected.dtype, projected.max(), projected.min(), projected.shape)
        colored = colorizers.colorize_array(projected, self.colors)
        self.labels_display.change_array(colored)

