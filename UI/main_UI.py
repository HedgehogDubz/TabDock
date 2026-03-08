import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import Qt
from UI.TabDock import TabDock
from UI.Tabs.test_tab import TestTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HedgehogFund")

        # Enable drops on the main window to handle external dock creation
        self.setAcceptDrops(True)

        self.window_width = 1200
        self.window_height = 800

        self.setGeometry(0,0, self.window_width, self.window_height)
        self.center_on_screen()

        self.TD = TabDock(create_external_docks=True)
        self.setCentralWidget(self.TD)

        tt = TestTab(self.TD, "Test Tab 1", 0)
        self.TD.add_tab(tt)
        tt = TestTab(self.TD, "Test Tab 2", 1)
        self.TD.add_tab(tt)
        
    def center_on_screen(self):
        screen = self.screen() or QGuiApplication.primaryScreen()
        screen_geo = screen.availableGeometry()

        frame_geo = self.frameGeometry()

        frame_geo.moveCenter(screen_geo.center())
        self.move(frame_geo.topLeft())

    def dragEnterEvent(self, event):
        """Accept drag events to prevent return animation"""
        if event.mimeData().hasText() and event.mimeData().text() == "dockable_window":
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Track drag movement"""
        if event.mimeData().hasText() and event.mimeData().text() == "dockable_window":
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle drop - create external dock if dropped on main window"""
        if event.mimeData().hasText() and event.mimeData().text() == "dockable_window":
            # Import here to avoid circular dependency
            from UI.dock import Dock

            # Check if there's an active drag
            if Dock._drag_source_dock is not None and Dock._drag_window_index is not None:
                # Get the source dock and create external dock
                source_dock = Dock._drag_source_dock
                window_index = Dock._drag_window_index

                # Get the window being dragged
                if 0 <= window_index < len(source_dock.dockable_windows):
                    window = source_dock.dockable_windows[window_index]
                    window_name = source_dock.dockable_window_names[window_index]

                    # Create external dock at cursor position
                    from UI.dock import ExternalDock
                    external_dock = ExternalDock(window_name)

                    # Remove from source
                    source_dock.remove_dockable_window(window_index)

                    # Add to external dock
                    external_dock.dock.add_dockable_window(window, window_name, 0)

                    # Position at cursor
                    cursor_pos = event.position().toPoint()
                    global_pos = self.mapToGlobal(cursor_pos)
                    external_dock.move(global_pos.x() - 100, global_pos.y() - 20)

                    # Show the external dock
                    external_dock.show()

                    # Clear drag state
                    Dock._drag_source_dock = None
                    Dock._drag_window_index = None

                    # Accept the drop to prevent return animation
                    event.setDropAction(Qt.DropAction.MoveAction)
                    event.accept()
                    return

            event.ignore()
        else:
            event.ignore()







        





def start_UI():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())