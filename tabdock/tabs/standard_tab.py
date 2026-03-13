from tabdock.tab import Tab
from tabdock.dock import Dock
from tabdock.hconnector import HConnector
from tabdock.vconnector import VConnector


class StandardTab(Tab):
    """
    Classic four-panel layout.

    +--------+-----------+--------+
    |        |           |        |
    |  left  |  center   | right  |
    |        |           |        |
    |        +-----------+        |
    |        |  bottom   |        |
    +--------+-----------+--------+

    Args:
        left_panels:   panel classes shown in the left sidebar
        center_panels: panel classes shown in the top-center dock
        right_panels:  panel classes shown in the right sidebar
        bottom_panels: panel classes shown in the bottom-center dock
        left_ratio:    fraction of width for the left sidebar   (default 0.20)
        right_ratio:   fraction of width for the right sidebar  (default 0.20)
        bottom_ratio:  fraction of height for the bottom dock   (default 0.30)
    """

    def __init__(self, parent, name, index, *,
                 left_panels=None,
                 center_panels=None,
                 right_panels=None,
                 bottom_panels=None,
                 left_ratio=0.20,
                 right_ratio=0.20,
                 bottom_ratio=0.30,
                 **style_kwargs):
        self._left_panels   = left_panels   or []
        self._center_panels = center_panels or []
        self._right_panels  = right_panels  or []
        self._bottom_panels = bottom_panels or []
        self._left_ratio    = left_ratio
        self._right_ratio   = right_ratio
        self._bottom_ratio  = bottom_ratio
        super().__init__(parent, name, index, **style_kwargs)

    def initUI(self):
        lr = self._left_ratio
        rr = self._right_ratio
        br = self._bottom_ratio

        self.left   = Dock(self, self._left_panels,   0,      0,      lr,          1)
        self.right  = Dock(self, self._right_panels,  1 - rr, 0,      rr,          1)
        self.center = Dock(self, self._center_panels, lr,     0,      1 - lr - rr, 1 - br)
        self.bottom = Dock(self, self._bottom_panels, lr,     1 - br, 1 - lr - rr, br)

        for dock in [self.left, self.right, self.center, self.bottom]:
            self.add_dock(dock)

        self.add_connector(HConnector(self, lr,      [self.left],                    [self.center, self.bottom]))
        self.add_connector(HConnector(self, 1 - rr,  [self.center, self.bottom],     [self.right]))
        self.add_connector(VConnector(self, 1 - br,  [self.center],                  [self.bottom]))

        for dock in [self.left, self.right, self.center, self.bottom]:
            dock.raise_()
