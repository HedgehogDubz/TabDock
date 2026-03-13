from tabdock.tab import Tab
from tabdock.dock import Dock
from tabdock.hconnector import HConnector
from tabdock.vconnector import VConnector


class QuadTab(Tab):
    """
    Four equal quadrants arranged in a 2x2 grid.

    +-------------+-------------+
    |             |             |
    |  top_left   |  top_right  |
    |             |             |
    +-------------+-------------+
    |             |             |
    | bottom_left | bottom_right|
    |             |             |
    +-------------+-------------+

    Args:
        top_left_panels:     panel classes for the top-left quadrant
        top_right_panels:    panel classes for the top-right quadrant
        bottom_left_panels:  panel classes for the bottom-left quadrant
        bottom_right_panels: panel classes for the bottom-right quadrant
        h_split:  horizontal split position (default 0.5)
        v_split:  vertical split position   (default 0.5)
    """

    def __init__(self, parent, name, index, *,
                 top_left_panels=None,
                 top_right_panels=None,
                 bottom_left_panels=None,
                 bottom_right_panels=None,
                 h_split=0.5,
                 v_split=0.5,
                 **style_kwargs):
        self._top_left_panels     = top_left_panels     or []
        self._top_right_panels    = top_right_panels    or []
        self._bottom_left_panels  = bottom_left_panels  or []
        self._bottom_right_panels = bottom_right_panels or []
        self._h_split = h_split
        self._v_split = v_split
        super().__init__(parent, name, index, **style_kwargs)

    def initUI(self):
        hs = self._h_split
        vs = self._v_split

        self.top_left     = Dock(self, self._top_left_panels,     0,  0,  hs,      vs)
        self.top_right    = Dock(self, self._top_right_panels,    hs, 0,  1 - hs,  vs)
        self.bottom_left  = Dock(self, self._bottom_left_panels,  0,  vs, hs,      1 - vs)
        self.bottom_right = Dock(self, self._bottom_right_panels, hs, vs, 1 - hs,  1 - vs)

        for dock in [self.top_left, self.top_right, self.bottom_left, self.bottom_right]:
            self.add_dock(dock)

        self.add_connector(HConnector(self, hs, [self.top_left, self.bottom_left],   [self.top_right, self.bottom_right]))
        self.add_connector(VConnector(self, vs, [self.top_left, self.top_right],     [self.bottom_left, self.bottom_right]))

        for dock in [self.top_left, self.top_right, self.bottom_left, self.bottom_right]:
            dock.raise_()
