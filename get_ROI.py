__author__ = 'sg24'

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# noinspection PyPep8Naming,PyArgumentList
def get_ROI(frame, debug_verbose_en):

    # Get user's ROI selection:
    Rect_pre1 = Annotate(frame)
    #plt.show()
    plt.pause(10)

    # Convert Rect into the required format (x,y,w,h):
    Rect_pre2 = [Rect_pre1.rect.get_x(),
                 Rect_pre1.rect.get_y(),
                 abs(Rect_pre1.rect.get_width()),
                 abs(Rect_pre1.rect.get_height())]

    # Round:
    Rect = [int(round(n, 0)) for n in Rect_pre2]

    if debug_verbose_en:
        print ("Rect = %s" % str(Rect))

    return Rect

# ------------------------------------------------------------------------------


class Annotate(object):
    def __init__(self, frame):
        self.ax = plt.gca()
        self.rect = Rectangle((0, 0), 1, 1)
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.ax.add_patch(self.rect)
        self.ax = plt.imshow(frame)
        self.ax.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.ax.figure.canvas.mpl_connect('button_release_event', self.on_release)

    def on_press(self, event):
        self.x0 = event.xdata
        self.y0 = event.ydata

    def on_release(self, event):
        self.x1 = event.xdata
        self.y1 = event.ydata
        self.rect.set_width(self.x1 - self.x0)
        self.rect.set_height(self.y1 - self.y0)
        self.rect.set_xy((self.x0, self.y0))
        self.ax.figure.canvas.draw()