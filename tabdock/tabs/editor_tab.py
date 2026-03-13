from tabdock.tab import Tab
from tabdock.dock import Dock
from tabdock.hconnector import HConnector
from tabdock.vconnector import VConnector


class EditorTab(Tab):
    """
    IDE-style layout: narrow left panel, large editor, bottom console.
    The left panel spans the full height; the right side is split top/bottom.

    +--------+--------------------+
    |        |       main         |
    |  left  |                    |
    |        +--------------------+
    |        |      bottom        |
    +--------+--------------------+

    Args:
        left_panels:   panel classes for the left panel (e.g. file tree)
        main_panels:   panel classes for the main/editor area
        bottom_panels: panel classes for the bottom strip (e.g. console, logs)
        left_ratio:    fraction of width for the left panel   (default 0.20)
        bottom_ratio:  fraction of height for the bottom strip (default 0.25)
    """

    def __init__(self, parent, name, index, *,
                 left_panels=None,
                 main_panels=None,
                 bottom_panels=None,
                 left_ratio=0.20,
                 bottom_ratio=0.25,
                 **style_kwargs):
        self._left_panels   = left_panels   or []
        self._main_panels   = main_panels   or []
        self._bottom_panels = bottom_panels or []
        self._left_ratio    = left_ratio
        self._bottom_ratio  = bottom_ratio
        super().__init__(parent, name, index, **style_kwargs)

    def initUI(self):
        lr = self._left_ratio
        br = self._bottom_ratio

        self.left   = Dock(self, self._left_panels,   0,      0,      lr,      1)
        self.main   = Dock(self, self._main_panels,   lr,     0,      1 - lr,  1 - br)
        self.bottom = Dock(self, self._bottom_panels, lr,     1 - br, 1 - lr,  br)

        for dock in [self.left, self.main, self.bottom]:
            self.add_dock(dock)

        self.add_connector(HConnector(self, lr,     [self.left], [self.main, self.bottom]))
        self.add_connector(VConnector(self, 1 - br, [self.main], [self.bottom]))

        for dock in [self.left, self.main, self.bottom]:
            dock.raise_()
