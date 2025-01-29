"""
Detail and summary view of 2d array with histograms.
"""

import numpy as np

import H5Gizmos as h5

VBars_fragment = """
<table>
<tr>
<td colspan="3"> <div class="INFO"/> </td>
</tr>
<tr>
    <td style="text-align: right; vertical-align: top;"> 
        <div class="YMAX"/> 
    </td>
    <td rowspan="2"> 
        <div colspan="2" class="IMAGE"/> 
    </td>
</tr>
<tr>
    <td style="text-align: right; vertical-align: bottom;"> 
        <div class="YMIN"/> 
    </td>
</tr>
<tr>
    <td> <div class="blank"/> </td>
    <td style="text-align: left; vertical-align: top;"> 
        <div class="XMIN"/> 
    </td>
    <td style="text-align: right; vertical-align: top;"> 
        <div class="XMAX"/> 
    </td>
</tr>
</table>
"""

class VBars:

    """
    Vertical bars for histogram display.
    """

    background = 200

    def __init__(self, values, width=600, height=200):
        self.values = values
        self.width = width
        self.height = height
        self.selected_column = None
        self.dashboard = self.dash()

    def array(self):
        background = self.background
        values = self.values
        array_height = self.height
        array_width = len(self.values)
        bw_array = np.full((array_height, array_width, 3), background, dtype=np.ubyte)
        height_factor = array_height / max(values)
        for i, value in enumerate(values):
            ylimit = int(value * height_factor)
            bw_array[array_height-ylimit:, i] = 0
        selected = self.selected_column
        if selected is not None:
            bw_array[:, selected, 1] = 255
            selected_value = values[selected]
            ylimit = int(selected_value * height_factor)
            bw_array[:array_height-ylimit, selected, 2] = background // 2
            bw_array[:array_height-ylimit, selected, :2] = 255
        self.height_factor = height_factor
        return bw_array

    def dash(self):
        values = self.values
        self.info_text = h5.Text("%s values" % len(values))
        #self.ymin_text = h5.Text(str(min(values)))
        self.ymax_text = h5.Text(str(max(values)))
        #self.xmin_text = h5.Text("0")
        self.xmax_text = h5.Text(str(len(values)))
        array = self._array = self.array()
        self.image = h5.Image(array=array, width=self.width, height=self.height, pixelated=True)
        self.image.on_pixel(self.click, "mousemove")
        self.dashboard = (h5.Template(VBars_fragment)
                            .put(self.info_text, "INFO")
                            #.put(self.ymin_text, "YMIN")
                            .put(self.ymax_text, "YMAX")
                            #.put(self.xmin_text, "XMIN")
                            .put(self.xmax_text, "XMAX")
                            .put(self.image, "IMAGE")
        )
        return self.dashboard
    
    def column_info(self, column):
        value = self.values[column]
        info = "%s: %s" % (column, value)
        return info

    def click(self, event):
        column = event["pixel_column"]
        #row = event["pixel_row"]
        self.selected_column = column
        value = self.values[column]
        #info = "%s: %s" % (column, value)
        info = self.column_info(column)
        self.info_text.text(info)
        array = self.array()
        self.image.change_array(array)

def test_vbars():
    values = np.random.randint(0, 100, 256)
    vbars = VBars(values)
    async def show():
        await vbars.dashboard.show()
    h5.serve(show())
      
class Histogram(VBars):

    def __init__(self, array, width=600, height=200):
        M = int(array.max() - array.min())
        if (M > 1000):
            bins = 1000
        else:
            bins = M + 1
        values, _ = np.histogram(array, bins=bins)
        super().__init__(values, width, height)

    def change_array(self, array):
        values, _ = np.histogram(array, bins=len(self.values))
        self.values = values
        self._array = self.array()
        self.image.change_array(self._array)

def test_histogram():
    #array = np.random.randint(0, 100, 10000)
    #array = (100 + np.sin(array / 10) * 100).astype(int)
    # Define the mean and standard deviation
    mean = 50   # Center of the distribution
    std_dev = 15  # Spread of the distribution

    # Generate normally distributed floating-point numbers
    data = np.random.normal(loc=mean, scale=std_dev, size=10000)

    # Clip values to be within the range [0, 100]
    data = np.clip(data, 0, 100)

    # Convert to integers
    array = np.round(data).astype(int)
    histogram = Histogram(array)
    async def show():
        await histogram.dashboard.show()
    h5.serve(show())

class ImageOverviewAndDetail:

    clicked = False
    
    def __init__(self, array, 
                 width=600, 
                 histogram_height=200,
                 title="Image Overview and Detail"):
        self.title = title
        # scale the array to 0..255 as np.uint8
        m = array.min()
        M = array.max()
        if M == m:
            array = np.zeros(array.shape, dtype=np.uint8)
        else:
            array = array.astype(np.float64)
            array = ((array - m) * 255 // (array.max() - m)).astype(np.uint8)
        self.array = array
        self.width = width
        self.shape = (I, J) = array.shape[:2]
        self.stride = J // width
        self.focus = (I // 2, J // 2)
        self.height = I // self.stride
        self.histogram_height = histogram_height
        self.dashboard = self.dash()

    def detail_boundaries(self):
        (I, J) = self.shape
        (i, j) = self.focus
        #stride = self.stride
        width = self.width
        height = self.height
        i0 = max(0, i - height // 2)
        i1 = min(I-1, i + height // 2)
        j0 = max(0, j - width // 2)
        j1 = min(J-1, j + width // 2)
        return (i0, i1, j0, j1)
    
    def detail(self):
        (i0, i1, j0, j1) = self.detail_boundaries()
        array = self.array[i0:i1, j0:j1]
        # make edges of array black
        detail = array.copy()
        #array[0, :] = 0
        #array[-1, :] = 0
        #array[:, 0] = 0
        #array[:, -1] = 0
        return (detail, array)
    
    def overview(self):
        array = self.array[::self.stride, ::self.stride]
        if len(array.shape) == 2:
            colored_array = np.zeros(array.shape + (3,), dtype=array.dtype)
            colored_array[:, :, 0] = array
            colored_array[:, :, 1] = array
            colored_array[:, :, 2] = array
        else:
            assert len(array.shape) == 3
            colored_array = array.copy()
        # draw a inverted outline around focus
        bounds = self.detail_boundaries()
        # adjust the bounds to the overview array using numpy with stride
        (i0, i1, j0, j1) = np.array(bounds) // self.stride
        colored_array[i0, j0:j1] = 255 - colored_array[i0, j0:j1]
        colored_array[i1, j0:j1] = 255 - colored_array[i1, j0:j1]
        colored_array[i0:i1, j0] = 255 - colored_array[i0:i1, j0]
        colored_array[i0:i1, j1] = 255 - colored_array[i0:i1, j1]
        # make edges of array black
        #colored_array[0, :] = 0
        #colored_array[-1, :] = 0
        #colored_array[:, 0] = 0
        #colored_array[:, -1] = 0
        return (array, colored_array)

    def dash(self):
        (arr_detail, disp_detail) = self.detail()
        (arr_overview, c_overview) = self.overview()
        title_text = h5.Text(self.title)
        overview_text = h5.Text("Overview")
        detail_text = h5.Text("Detail")
        image_detail = h5.Image(array=disp_detail, width=self.width, pixelated=True, scale=False)
        image_overview = h5.Image(array=c_overview, width=self.width, pixelated=True, scale=False)
        image_overview.on_pixel(self.focus_click, "click")
        image_overview.on_pixel(self.focus_move, "mousemove")
        image_overview.css({"border": "5px solid red"})
        image_detail.css({"border": "5px solid red"})
        detail_histogram = Histogram(arr_detail, self.width, self.histogram_height)
        overview_histogram = Histogram(arr_overview, self.width, self.histogram_height)
        dashboard = h5.Stack([
            title_text,
            [
                [overview_text, image_overview, overview_histogram.dashboard],
                [detail_text, image_detail, detail_histogram.dashboard]
            ]
        ])
        self.image_detail = image_detail
        self.image_overview = image_overview
        self.detail_histogram = detail_histogram
        self.overview_histogram = overview_histogram
        self.detail_text = detail_text
        self.overview_text = overview_text
        return dashboard
    
    def focus_click(self, event):
        self.clicked = not self.clicked
        #print("clicked", self.clicked, event["type"])
    
    def focus_move(self, event):
        #print ("focus_move", self.clicked)
        if not self.clicked:
            return
        pcolumn = event["pixel_column"]
        prow = event["pixel_row"]
        # adjust by stride
        column = pcolumn * self.stride
        row = prow * self.stride
        self.focus = (row, column)
        focus_text = "Focus: %s, %s" % (row, column)
        self.overview_text.text(focus_text)
        bounds = self.detail_boundaries()
        bounds_text = "[%s..%s, %s..%s]" % bounds
        self.detail_text.text(bounds_text)
        (_, colored_overview) = self.overview()
        self.image_overview.change_array(colored_overview, scale=False)
        (arr_detail, disp_detail) = self.detail()
        self.image_detail.change_array(disp_detail, scale=True)
        self.detail_histogram.change_array(arr_detail)

    async def show(self):
        await self.dashboard.show(title=self.title)

    async def link(self):
        await self.dashboard.link(title=self.title)

    
def test_image_overview_and_detail():
    print("creating array")
    # Define the size of the grid
    size = 20000  # Size of the 2D array (size x size)
    cycles = 12  # Number of sine wave cycles

    # Create a coordinate grid
    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    X, Y = np.meshgrid(x, y)

    # Compute the radial distance from the center
    R = np.sqrt(X**2 + Y**2)

    # Normalize the radial distance to range from 0 to 2π * cycles
    R_scaled = R / R.max() * (2 * np.pi * cycles)

    # Compute the sine wave radiating outward
    Z = np.sin(R_scaled)
    array = ((Z + 1) * 128).astype(np.uint8)
    #array = np.random.randint(0, 100, (1000, 1000))
    print("creating ImageOverviewAndDetail")
    iod = ImageOverviewAndDetail(array)
    async def show():
        await iod.dashboard.show()
    h5.serve(show())

if __name__ == "__main__":
    test_image_overview_and_detail()