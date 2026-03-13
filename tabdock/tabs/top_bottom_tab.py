from tabdock.tab import Tab
from tabdock.dock import Dock
from tabdock.vconnector import VConnector


class TopBottomTab(Tab):
    """
    Horizontal toolbar strip on top with a large main area below.

    +----------------------------+
    |           top              |
    +----------------------------+
    |           main             |
    +----------------------------+

    Args:
        top_panels:  panel classes shown in the top strip
        main_panels: panel classes shown in the main area
        top_ratio:   fraction of height for the top strip (default 0.25)
    """

    def __init__(self, parent, name, index, *,
                 top_panels=None,
                 main_panels=None,
                 top_ratio=0.25,
                 **style_kwargs):
        self._top_panels  = top_panels  or []
        self._main_panels = main_panels or []
        self._top_ratio   = top_ratio
        super().__init__(parent, name, index, **style_kwargs)

    def initUI(self):
        tr = self._top_ratio

        self.top  = Dock(self, self._top_panels,  0, 0,  1, tr)
        self.main = Dock(self, self._main_panels, 0, tr, 1, 1 - tr)

        self.add_dock(self.top)
        self.add_dock(self.main)

        self.add_connector(VConnector(self, tr, [self.top], [self.main]))

        self.top.raise_()
        self.main.raise_()
