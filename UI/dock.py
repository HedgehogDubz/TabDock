from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton
from PyQt6.QtGui import QPainter, QColor, QPen, QDrag, QCursor, QPixmap
from PyQt6.QtCore import Qt, QMimeData, QPoint
from UI._style_guide import bg, black, border_color
import math

class DraggableTabButton(QPushButton):
    def __init__(self, text, dock, index):
        super().__init__(text)
        self.dock = dock
        self.index = index
        self.drag_start_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self.drag_start_position is None:
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return

        Dock._drag_source_dock = self.dock
        Dock._drag_window_index = self.index

        # Hide the original tab button while dragging
        self.hide()

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText("dockable_window")
        drag.setMimeData(mime_data)

        # Create a pixmap that looks like the tab button for visual feedback
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)

        # Render the button onto the pixmap
        painter = QPainter(pixmap)
        painter.setOpacity(0.7)  # Make it semi-transparent

        # Draw the button background
        painter.fillRect(pixmap.rect(), QColor(bg))

        # Draw the button text
        painter.setPen(QColor("white"))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))

        # Start drag - this will block until drop or cancel
        result = drag.exec(Qt.DropAction.MoveAction)

        # Handle the result of the drag operation
        if result != Qt.DropAction.MoveAction:
            # Check if drag state was already cleared (drop was handled by a Dock)
            if Dock._drag_source_dock is None:
                # Drop was handled, nothing to do
                return

            # Drag was not accepted by any widget - check if we should create external dock
            tab_dock = self._get_tab_dock()
            if tab_dock and hasattr(tab_dock, 'create_external_docks') and tab_dock.create_external_docks:
                # Create external dock at cursor position (user dragged outside app window)
                self._create_external_dock()
                return

            # Drag was truly cancelled, show the button again
            try:
                self.show()
            except RuntimeError:
                # Button was already deleted, ignore
                pass

            Dock._drag_source_dock = None
            Dock._drag_window_index = None

    def _get_tab_dock(self):
        """Get the TabDock instance from the parent chain, or ExternalDock if applicable"""
        try:
            # Dock has a parent attribute (Tab instance or ExternalDock)
            dock_parent = self.dock.parent
            if dock_parent is None:
                return None

            # Check if parent is an ExternalDock (which supports creating more external docks)
            if isinstance(dock_parent, ExternalDock):
                return dock_parent

            # Tab has a parent attribute (TabDock instance)
            # We need to access the attribute, not call the parent() method
            # Use __dict__ to get the actual attribute
            if hasattr(dock_parent, '__dict__') and 'parent' in dock_parent.__dict__:
                tab_dock = dock_parent.__dict__['parent']
                # Verify it's actually a TabDock with create_external_docks attribute
                if hasattr(tab_dock, 'create_external_docks'):
                    return tab_dock
        except Exception:
            pass

        return None

    def _create_external_dock(self):
        """Create an external floating dock with the dragged window"""
        if Dock._drag_source_dock is None or Dock._drag_window_index is None:
            return

        source_dock = Dock._drag_source_dock
        window_index = Dock._drag_window_index

        # Get the dockable window
        dockable_window = source_dock.dockable_windows[window_index]
        window_name = dockable_window.__class__.__name__

        # Create the external dock window
        external_dock = ExternalDock(window_name)

        # Remove from source dock
        source_dock.remove_dockable_window(window_index)

        # Add to external dock
        external_dock.dock.add_dockable_window(dockable_window, window_name, 0, is_external=True)

        # Position at cursor and show
        cursor_pos = QCursor.pos()
        external_dock.move(cursor_pos.x() - 100, cursor_pos.y() - 20)
        external_dock.show()

class ExternalDock(QWidget):
    """A floating window that contains a single Dock"""
    def __init__(self, window_name, width=400, height=300):
        super().__init__()
        self.setWindowTitle(f"External Dock - {window_name}")
        self.setWindowFlags(Qt.WindowType.Window)
        self.resize(width, height)

        # Store that external docks are enabled (since this IS an external dock)
        self.create_external_docks = True

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create a dock that fills this window
        # The dock needs a parent with centralWidget(), width(), height() methods
        self.dock = Dock(self, [], 0, 0, 1, 1)
        layout.addWidget(self.dock)

    def centralWidget(self):
        """Return self as the central widget for Dock compatibility"""
        return self

    def width(self):
        """Override to provide width for Dock"""
        return super().width()

    def height(self):
        """Override to provide height for Dock"""
        return super().height()

class Dock(QFrame):
    _drag_source_dock = None
    _drag_window_index = None

    def __init__(self, parent, dockable_windows, x_ratio, y_ratio, w_ratio, h_ratio):
        self.parent = parent
        super().__init__(parent.centralWidget())

        self.setStyleSheet(f"background-color: {black}; margin: 0px;")
        self.setAcceptDrops(True)
        self.preview_button = None
        self.drop_insert_index = -1
        self.preview_active = False

        self.x_ratio = x_ratio
        self.y_ratio = y_ratio
        self.w_ratio = w_ratio
        self.h_ratio = h_ratio

        dock_x = int(x_ratio * parent.width())
        dock_y = int(y_ratio * parent.height())
        x_end = int((x_ratio + w_ratio) * parent.width())
        y_end = int((y_ratio + h_ratio) * parent.height())
        dock_w = x_end - dock_x
        dock_h = y_end - dock_y

        self.setGeometry(dock_x, dock_y, dock_w, dock_h)

        self.dockIndex = 0
        self.dockable_windows_classes = dockable_windows
        self.dockable_windows = []
        self.tab_buttons = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(0)

        self.tab_bar_widget = QWidget()
        self.tab_bar_widget.setStyleSheet("margin: 0px; padding: 0px; border: none;")
        self.tab_bar_widget.setContentsMargins(0, 0, 0, 0)
        self.tab_bar_widget.setAcceptDrops(False)
        self.tab_bar_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        self.tab_bar = QHBoxLayout(self.tab_bar_widget)
        self.tab_bar.setContentsMargins(0, 0, 0, 0)
        self.tab_bar.setSpacing(0)
        self.tab_bar.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.tab_bar.addStretch()

        for i, dw_class in enumerate(dockable_windows):
            tab_button = DraggableTabButton(dw_class.__name__, self, i)
            tab_button.setFlat(True)
            tab_button.setStyleSheet(f"background-color: {black}; color: white; border: none; padding: 5px 10px; margin: 0px;")
            tab_button.setContentsMargins(0, 0, 0, 0)
            tab_button.setAcceptDrops(False)
            tab_button.clicked.connect(lambda _, index=i: self.switch_tab(index))
            self.tab_buttons.append(tab_button)
            self.tab_bar.insertWidget(i, tab_button)

            dw_instance = dw_class(self, True, 0, 0, int(math.ceil(self.w_ratio * parent.width())), int(math.ceil(self.h_ratio * parent.height())))
            dw_instance.hide()
            self.dockable_windows.append(dw_instance)

        self.layout.addWidget(self.tab_bar_widget, 0)

        for dw in self.dockable_windows:
            self.layout.addWidget(dw, 1)

        if self.dockable_windows:
            self.switch_tab(0)

    def update_geometry(self):
        parent_width = self.parent.width()
        parent_height = self.parent.height()

        dock_x = int(self.x_ratio * parent_width)
        dock_y = int(self.y_ratio * parent_height)
        x_end = int((self.x_ratio + self.w_ratio) * parent_width)
        y_end = int((self.y_ratio + self.h_ratio) * parent_height)
        dock_w = x_end - dock_x
        dock_h = y_end - dock_y

        self.setGeometry(dock_x, dock_y, dock_w, dock_h)
        self.repaint()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        pen = QPen(QColor(border_color))
        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)

    def switch_tab(self, index):
        if 0 <= index < len(self.dockable_windows):
            if 0 <= self.dockIndex < len(self.dockable_windows):
                self.dockable_windows[self.dockIndex].hide()

            self.dockIndex = index
            self.dockable_windows[self.dockIndex].show()

            for i, button in enumerate(self.tab_buttons):
                if i == index:
                    button.setStyleSheet(f"background-color: {bg}; color: white; border: none; padding: 5px 10px; margin: 0px; border-top-left-radius: 5px; border-top-right-radius: 5px;")
                else:
                    button.setStyleSheet(f"background-color: {black}; color: white; border: none; padding: 5px 10px; margin: 0px; border-top-left-radius: 5px; border-top-right-radius: 5px;")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() == "dockable_window":
            if Dock._drag_source_dock is not None:
                # Accept the drag enter event regardless of position
                # We'll check the actual position in dragMoveEvent
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
                return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() == "dockable_window":
            if Dock._drag_source_dock is not None:
                pos = event.position().toPoint() if hasattr(event.position(), 'toPoint') else event.pos()
                if self._is_over_tab_bar(pos):
                    self._update_drop_preview(pos)
                else:
                    self._hide_drop_preview()
                # Accept the drag move event regardless of position
                # This ensures dropEvent will be called even when not over tab bar
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
                return
        event.ignore()

    def dragLeaveEvent(self, _):
        self._hide_drop_preview()

    def dropEvent(self, event):
        if Dock._drag_source_dock is not None and Dock._drag_window_index is not None:
            source_dock = Dock._drag_source_dock
            window_index = Dock._drag_window_index

            pos = event.position().toPoint() if hasattr(event.position(), 'toPoint') else event.pos()

            if self._is_over_tab_bar(pos):
                dockable_window = source_dock.dockable_windows[window_index]
                window_name = dockable_window.__class__.__name__

                insert_index = self.drop_insert_index if self.drop_insert_index >= 0 else self._calculate_insert_index(pos)

                if source_dock == self:
                    if insert_index > window_index:
                        insert_index -= 1
                    if insert_index != window_index:
                        source_dock.remove_dockable_window(window_index)
                        self._hide_drop_preview()
                        self.add_dockable_window(dockable_window, window_name, insert_index)
                    else:
                        self._hide_drop_preview()
                else:
                    source_dock.remove_dockable_window(window_index)
                    self._hide_drop_preview()
                    self.add_dockable_window(dockable_window, window_name, insert_index)
                    if self.parent is None and self.dockable_windows:
                        self.hide()

                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
                Dock._drag_source_dock = None
                Dock._drag_window_index = None
                return
            else:
                # Not over tab bar - create external dock here since event won't bubble up
                self._hide_drop_preview()

                # Create external dock at cursor position
                window = source_dock.dockable_windows[window_index]
                window_name = window.__class__.__name__

                from UI.dock import ExternalDock
                external_dock = ExternalDock(window_name)

                # Remove from source
                source_dock.remove_dockable_window(window_index)

                # Add to external dock
                external_dock.dock.add_dockable_window(window, window_name, 0)

                # Position at cursor
                cursor_pos = QCursor.pos()
                external_dock.move(cursor_pos.x() - 100, cursor_pos.y() - 20)

                # Show the external dock
                external_dock.show()

                # Clear drag state
                Dock._drag_source_dock = None
                Dock._drag_window_index = None

                # Accept the drop to prevent return animation
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
                return

        # Only clear drag state if no drag was active
        event.ignore()

    def _is_over_tab_bar(self, pos):
        tab_bar_rect = self.tab_bar_widget.geometry()
        result = tab_bar_rect.contains(pos)

        # Fallback: accept drops if Y is within the tab bar's height OR within top 50px
        # This handles edge cases where geometry() doesn't perfectly align
        # or when dragging from external docks
        if not result:
            # Check if Y position is within the tab bar's height (regardless of where it is)
            # OR if it's in the top 50 pixels of the dock
            tab_bar_height = tab_bar_rect.height()
            if pos.y() <= tab_bar_height + 5 or pos.y() <= 50:
                # Also check if X is roughly within the dock's width
                if 0 <= pos.x() <= self.width():
                    return True

        return result

    def _calculate_insert_index(self, pos):
        mouse_x = pos.x()

        if not self.tab_buttons:
            return 0

        for i, button in enumerate(self.tab_buttons):
            button_global_pos = button.mapToGlobal(button.rect().topLeft())
            button_parent_pos = self.mapFromGlobal(button_global_pos)
            button_left = button_parent_pos.x()
            button_right = button_left + button.width()
            button_center = button_left + button.width() / 2

            if button_left <= mouse_x <= button_right:
                if mouse_x < button_center:
                    return i
                else:
                    return i + 1
            elif mouse_x < button_left:
                return i

        return len(self.tab_buttons)

    def _update_drop_preview(self, pos):
        if Dock._drag_source_dock is None or Dock._drag_window_index is None:
            return

        insert_index = self._calculate_insert_index(pos)

        if self.preview_active and self.drop_insert_index == insert_index:
            return

        self._hide_drop_preview()

        source_dock = Dock._drag_source_dock
        window_index = Dock._drag_window_index
        dockable_window = source_dock.dockable_windows[window_index]
        window_name = dockable_window.__class__.__name__

        self.preview_button = QPushButton(window_name)
        self.preview_button.setFlat(True)
        self.preview_button.setStyleSheet(f"background-color: {bg}; color: white; border: none; padding: 5px 10px; margin: 0px; opacity: 0.5;")
        self.preview_button.setContentsMargins(0, 0, 0, 0)
        self.preview_button.setEnabled(False)

        self.tab_bar.insertWidget(insert_index, self.preview_button)

        self.drop_insert_index = insert_index
        self.preview_active = True

    def _hide_drop_preview(self):
        if not self.preview_active:
            return

        if self.preview_button is not None:
            self.tab_bar.removeWidget(self.preview_button)
            self.preview_button.deleteLater()
            self.preview_button = None

        self.drop_insert_index = -1
        self.preview_active = False

    def remove_dockable_window(self, index):
        if 0 <= index < len(self.dockable_windows):
            dw = self.dockable_windows.pop(index)
            button = self.tab_buttons.pop(index)

            dw.hide()
            self.layout.removeWidget(dw)
            dw.setParent(None)

            self.tab_bar.removeWidget(button)
            button.deleteLater()

            for i, btn in enumerate(self.tab_buttons):
                btn.index = i
                btn.clicked.disconnect()
                btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))

            if self.dockable_windows:
                self.dockIndex = min(self.dockIndex, len(self.dockable_windows) - 1)
                self.switch_tab(self.dockIndex)
            else:
                self.dockIndex = 0
                # If this is an external dock and it's now empty, close it
                if isinstance(self.parent, ExternalDock):
                    self.parent.close()

    def add_dockable_window(self, dockable_window, window_name, insert_index=None, is_external=False):
        if insert_index is None:
            insert_index = len(self.dockable_windows)

        insert_index = max(0, min(insert_index, len(self.dockable_windows)))

        tab_button = DraggableTabButton(window_name, self, insert_index)
        tab_button.setFlat(True)
        tab_button.setStyleSheet(f"background-color: {black}; color: white; border: none; padding: 5px 10px; margin: 0px;")
        tab_button.setContentsMargins(0, 0, 0, 0)
        tab_button.clicked.connect(lambda _, idx=insert_index: self.switch_tab(idx))
        self.tab_buttons.insert(insert_index, tab_button)
        self.tab_bar.insertWidget(insert_index, tab_button)

        dockable_window.setParent(self)
        dockable_window.hide()
        self.dockable_windows.insert(insert_index, dockable_window)
        self.layout.addWidget(dockable_window, 1)

        for i, btn in enumerate(self.tab_buttons):
            btn.index = i
            btn.clicked.disconnect()
            btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))

        self.switch_tab(insert_index)

