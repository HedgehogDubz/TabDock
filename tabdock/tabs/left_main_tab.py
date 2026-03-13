from tabdock.tab import Tab
from tabdock.dock import Dock
from tabdock.hconnector import HConnector


class LeftMainTab(Tab):
    """
    Left sidebar with a large main area.

    +--------+--------------------+
    |        |                    |
    |  left  |       main         |
    |        |                    |
    +--------+--------------------+

    Args:
        left_panels: panel classes shown in the left sidebar
        main_panels: panel classes shown in the main area
        left_ratio:  fraction of width for the left sidebar (default 0.25)
    """

    def __init__(self, parent, name, index, *,
                 left_panels=None,
                 main_panels=None,
                 left_ratio=0.25,
                 **style_kwargs):
        self._left_panels = left_panels or []
        self._main_panels = main_panels or []
        self._left_ratio  = left_ratio
        super().__init__(parent, name, index, **style_kwargs)

    def initUI(self):
        lr = self._left_ratio

        self.left = Dock(self, self._left_panels, 0,  0, lr,      1)
        self.main = Dock(self, self._main_panels, lr, 0, 1 - lr,  1)

        self.add_dock(self.left)
        self.add_dock(self.main)

        self.add_connector(HConnector(self, lr, [self.left], [self.main]))

        self.left.raise_()
        self.main.raise_()
