from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QApplication, QMenu, QScrollArea
from PyQt6.QtGui import QPainter, QColor, QCursor, QAction
from PyQt6.QtCore import Qt, QPoint
from tabdock._style_guide import bg, black, border_color, lighten
import math

class DragPreviewWidget(QWidget):
    """Floating widget that shows a preview of the tab being dragged"""
    def __init__(self, text, size, bg_color, text_color):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.setFixedSize(size)

        self.button_text = text
        self.bg_color = bg_color
        self.text_color = text_color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setOpacity(1.0)
        painter.fillRect(self.rect(), QColor(self.bg_color))

        painter.setOpacity(1.0)
        painter.setPen(QColor(self.text_color))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.button_text)

class DraggableTabButton(QPushButton):
    def __init__(self, text, dock, index):
        super().__init__(text)
        self.dock = dock
        self.index = index
        self.drag_start_position = None
        self.drag_preview = None
        self.is_dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self.drag_start_position is None:
            return

        if not self.is_dragging:
            if (event.pos() - self.drag_start_position).manhattanLength() < 10:
                return

            self.is_dragging = True
            Dock._drag_source_dock = self.dock
            Dock._drag_window_index = self.index

            self.hide()

            self.dock._hide_dragged_tab(self.index)

            self.drag_preview = DragPreviewWidget(self.text(), self.size(),
                                                   self.dock.active_tab_color,
                                                   self.dock.tab_text_color)
            self.drag_preview.show()

            self.grabMouse()

        if self.drag_preview:
            cursor_pos = QCursor.pos()
            self.drag_preview.move(
                cursor_pos.x() - self.drag_preview.width() // 2,
                cursor_pos.y() - self.drag_preview.height() // 2
            )

            self._update_drop_targets(cursor_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.releaseMouse()

            if self.drag_preview:
                self.drag_preview.close()
                self.drag_preview.deleteLater()
                self.drag_preview = None

            # Handle the drop
            self._handle_drop(QCursor.pos())

            # Clean up all preview buttons in all docks
            app = QApplication.instance()
            for widget in app.allWidgets():
                if isinstance(widget, Dock):
                    widget._hide_drop_preview()

            if Dock._drag_source_dock and Dock._drag_window_index is not None:
                if Dock._drag_window_index < len(Dock._drag_source_dock.tab_buttons):
                    Dock._drag_source_dock._show_dragged_tab(Dock._drag_window_index)

            self.is_dragging = False
            self.drag_start_position = None
        else:
            super().mouseReleaseEvent(event)

    def _update_drop_targets(self, global_pos):
        app = QApplication.instance()

        if self.drag_preview:
            self.drag_preview.hide()

        widget_at_cursor = app.widgetAt(global_pos)

        target_dock = None
        current = widget_at_cursor
        while current:
            if isinstance(current, Dock):
                target_dock = current
                break
            current = current.parentWidget()

        all_docks = [widget for widget in app.allWidgets() if isinstance(widget, Dock)]

        if target_dock:
            local_pos = target_dock.mapFromGlobal(global_pos)
            if target_dock._is_over_tab_bar(local_pos):
                target_dock._update_drop_preview(local_pos)
                for dock in all_docks:
                    if dock != target_dock:
                        dock._hide_drop_preview()
            else:
                for dock in all_docks:
                    dock._hide_drop_preview()
                if self.drag_preview:
                    self.drag_preview.show()
        else:
            for dock in all_docks:
                dock._hide_drop_preview()
            if self.drag_preview:
                self.drag_preview.show()

    def _handle_drop(self, global_pos):
        """Handle the drop at the given global position"""
        app = QApplication.instance()
        widget_at_cursor = app.widgetAt(global_pos)

        # Find the Dock widget if cursor is over one
        target_dock = None
        current = widget_at_cursor
        while current:
            if isinstance(current, Dock):
                target_dock = current
                break
            current = current.parentWidget()

        if target_dock:
            #internal dock
            local_pos = target_dock.mapFromGlobal(global_pos)

            if target_dock._is_over_tab_bar(local_pos):
                self._handle_tab_move(target_dock, local_pos)
            else:
                self._create_external_dock()
        else:
            # external dock
            tab_dock = self._get_tab_dock()
            if tab_dock and hasattr(tab_dock, 'create_external_docks') and tab_dock.create_external_docks:
                self._create_external_dock()
            else:
                self.show()

        # Clear drag state
        Dock._drag_source_dock = None
        Dock._drag_window_index = None

    def _handle_tab_move(self, target_dock, local_pos):
        """Move tab to target dock at the drop position"""
        source_dock = Dock._drag_source_dock
        window_index = Dock._drag_window_index

        if source_dock is None or window_index is None:
            return

        panel = source_dock.panels[window_index]
        window_name = panel.__class__.__name__

        insert_index = target_dock._calculate_insert_index(local_pos)

        if source_dock == target_dock:
            # Reordering within same dock
            if insert_index > window_index:
                insert_index -= 1
            if insert_index != window_index:
                # IMPORTANT: Hide preview BEFORE removing panel to avoid layout corruption
                target_dock._hide_drop_preview()
                source_dock.remove_panel(window_index)
                target_dock.add_panel(panel, window_name, insert_index)
            else:
                # Dropped back in same position - just switch to that tab
                target_dock._hide_drop_preview()
                self.show()
                source_dock.switch_tab(window_index)
        else:
            # Moving between docks
            # IMPORTANT: Hide preview BEFORE removing panel to avoid layout corruption
            target_dock._hide_drop_preview()
            source_dock.remove_panel(window_index)
            target_dock.add_panel(panel, window_name, insert_index)

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

            if hasattr(dock_parent, '__dict__') and 'parent' in dock_parent.__dict__:
                tab_dock = dock_parent.__dict__['parent']
                if hasattr(tab_dock, 'create_external_docks'):
                    return tab_dock
        except Exception:
            pass

        return None

    def _create_external_dock(self):
        """Create an external floating dock with the dragged panel"""
        if Dock._drag_source_dock is None or Dock._drag_window_index is None:
            return

        source_dock = Dock._drag_source_dock
        window_index = Dock._drag_window_index

        # Get the panel
        panel = source_dock.panels[window_index]
        panel_name = panel.__class__.__name__

        external_dock = ExternalDock(panel_name)
        source_dock.remove_panel(window_index)

        external_dock.dock.add_panel(panel, panel_name, 0, is_external=True)

        cursor_pos = QCursor.pos()
        external_dock.show()
        external_dock.move(cursor_pos.x() - 40, cursor_pos.y() - 43)

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
    _preview_dock = None

    def __init__(self, parent, panels, x_ratio, y_ratio, w_ratio, h_ratio, *,
                 dock_bg=None,
                 tab_bar_bg=None,
                 content_bg=None,
                 dock_border_color=None,
                 border_width=None,
                 tab_text_color=None,
                 active_tab_color=None,
                 tab_height=None,
                 tab_radius=None,
                 tab_padding=None,
                 tab_spacing=None,
                 dock_padding=None,
                 panel_bg=None,
                 available_panels=None,
                 accent_color=None):
        self.parent = parent
        super().__init__(parent.centralWidget())

        # Inherit from parent (Tab/TabDock) if not explicitly set
        self.dock_bg           = dock_bg           if dock_bg           is not None else getattr(parent, 'dock_bg',           black)
        self.tab_bar_bg        = tab_bar_bg        if tab_bar_bg        is not None else getattr(parent, 'tab_bar_bg',        black)
        self.content_bg        = content_bg        if content_bg        is not None else getattr(parent, 'content_bg',        bg)
        self.dock_border_color = dock_border_color if dock_border_color is not None else getattr(parent, 'dock_border_color', border_color)
        self.border_width      = border_width      if border_width      is not None else getattr(parent, 'border_width',      2)
        self.tab_text_color    = tab_text_color    if tab_text_color    is not None else getattr(parent, 'tab_text_color',    'white')
        self.active_tab_color  = active_tab_color  if active_tab_color  is not None else getattr(parent, 'active_tab_color',  bg)
        self.tab_height        = tab_height        if tab_height        is not None else getattr(parent, 'tab_height',        25)
        self.tab_radius        = tab_radius        if tab_radius        is not None else getattr(parent, 'tab_radius',        5)
        self.tab_padding       = tab_padding       if tab_padding       is not None else getattr(parent, 'tab_padding',       '5px 10px')
        self.tab_spacing       = tab_spacing       if tab_spacing       is not None else getattr(parent, 'tab_spacing',       0)
        self.dock_padding      = dock_padding      if dock_padding      is not None else getattr(parent, 'dock_padding',      2)
        self.panel_bg          = panel_bg          if panel_bg          is not None else getattr(parent, 'panel_bg',          bg)
        self.available_panels  = available_panels  if available_panels  is not None else getattr(parent, 'available_panels',  [])
        self.accent_color      = accent_color      if accent_color      is not None else getattr(parent, 'accent_color',      '#5080c0')

        self.setStyleSheet(f"background-color: {self.dock_bg}; margin: 0px;")
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
        self.panel_classes = panels
        self.panels = []
        self.tab_buttons = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(self.dock_padding, self.dock_padding, self.dock_padding, self.dock_padding)
        self.layout.setSpacing(0)

        self.tab_bar_widget = QWidget()
        self.tab_bar_widget.setStyleSheet(f"background-color: {self.tab_bar_bg}; margin: 0px; padding: 0px; border: none;")
        self.tab_bar_widget.setContentsMargins(0, 0, 0, 0)
        self.tab_bar_widget.setAcceptDrops(False)
        self.tab_bar_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.tab_bar_widget.setFixedHeight(self.tab_height)

        self.tab_bar = QHBoxLayout(self.tab_bar_widget)
        self.tab_bar.setContentsMargins(0, 0, 0, 0)
        self.tab_bar.setSpacing(self.tab_spacing)
        self.tab_bar.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Create scrollable content area that always exists (even when no panels)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        _scroll_handle = lighten(self.content_bg, 0.25)
        _scroll_arrow = lighten(self.content_bg, 0.35)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.content_bg};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {self.content_bg};
                width: 10px;
                border-radius: 5px;
                margin: 12px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {_scroll_handle};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {_scroll_arrow};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 10px;
                subcontrol-origin: margin;
                background: {_scroll_handle};
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical:hover, QScrollBar::sub-line:vertical:hover {{
                background: {_scroll_arrow};
            }}
            QScrollBar::sub-line:vertical {{
                subcontrol-position: top;
            }}
            QScrollBar::add-line:vertical {{
                subcontrol-position: bottom;
            }}
            QScrollBar::up-arrow:vertical {{
                width: 6px;
                height: 6px;
                background: none;
                border-left: 2px solid {self.content_bg};
                border-top: 2px solid {self.content_bg};
                transform: rotate(45deg);
            }}
            QScrollBar::down-arrow:vertical {{
                width: 6px;
                height: 6px;
                background: none;
                border-left: 2px solid {self.content_bg};
                border-top: 2px solid {self.content_bg};
                transform: rotate(45deg);
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background-color: {self.content_bg}; margin: 0px; padding: 0px; border: none;")
        self.content_widget.setContentsMargins(0, 0, 0, 0)

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.scroll_area.setWidget(self.content_widget)

        for i, panel_class in enumerate(panels):
            tab_button = DraggableTabButton(panel_class.__name__, self, i)
            tab_button.setFlat(True)
            tab_button.setStyleSheet(f"background-color: {self.tab_bar_bg}; color: {self.tab_text_color}; border: none; padding: {self.tab_padding}; margin: 0px;")
            tab_button.setContentsMargins(0, 0, 0, 0)
            tab_button.setAcceptDrops(False)
            tab_button.clicked.connect(lambda _, index=i: self.switch_tab(index))
            self.tab_buttons.append(tab_button)
            self.tab_bar.addWidget(tab_button)

            panel_instance = panel_class(self, True, 0, 0, int(math.ceil(self.w_ratio * parent.width())), int(math.ceil(self.h_ratio * parent.height())))
            panel_instance.hide()
            self.panels.append(panel_instance)

        self.tab_bar.addStretch()

        self.layout.addWidget(self.tab_bar_widget, 0)
        self.layout.addWidget(self.scroll_area, 1)  # Scroll area always added with stretch

        for panel in self.panels:
            self.content_layout.addWidget(panel)

        if self.panels:
            self.switch_tab(0)

        # Ensure the dock is above connectors in z-order
        self.raise_()

    def update_geometry(self):
        parent_width = self.parent.width()
        parent_height = self.parent.height()

        dock_x = int(self.x_ratio * parent_width)
        dock_y = int(self.y_ratio * parent_height)
        x_end = int((self.x_ratio + self.w_ratio) * parent_width)
        y_end = int((self.y_ratio + self.h_ratio) * parent_height)
        dock_w = x_end - dock_x
        dock_h = y_end - dock_y

        old_geometry = self.geometry()
        self.setGeometry(dock_x, dock_y, dock_w, dock_h)

        if old_geometry != self.geometry():
            self.repaint()

    def paintEvent(self, event):
        super().paintEvent(event)

    def contextMenuEvent(self, event):
        """Show context menu on right-click"""
        menu = QMenu(self)

        # Style the menu using theme colors
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.dock_bg};
                color: {self.tab_text_color};
                border: 1px solid {self.dock_border_color};
            }}
            QMenu::item {{
                padding: 5px 20px;
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: {self.tab_bar_bg};
            }}
            QMenu::item:disabled {{
                color: {self.dock_border_color};
            }}
        """)

        # Split dock submenu
        split_menu = menu.addMenu("Split Dock")

        min_size = getattr(self.parent, 'min_dock_size', 100)
        can_split_h = self.width()  >= min_size * 2
        can_split_v = self.height() >= min_size * 2

        split_right_action = QAction("Split Right", self)
        split_right_action.triggered.connect(lambda: self.split_dock('right'))
        split_right_action.setEnabled(can_split_h)
        split_menu.addAction(split_right_action)

        split_bottom_action = QAction("Split Bottom", self)
        split_bottom_action.triggered.connect(lambda: self.split_dock('bottom'))
        split_bottom_action.setEnabled(can_split_v)
        split_menu.addAction(split_bottom_action)

        split_left_action = QAction("Split Left", self)
        split_left_action.triggered.connect(lambda: self.split_dock('left'))
        split_left_action.setEnabled(can_split_h)
        split_menu.addAction(split_left_action)

        split_top_action = QAction("Split Top", self)
        split_top_action.triggered.connect(lambda: self.split_dock('top'))
        split_top_action.setEnabled(can_split_v)
        split_menu.addAction(split_top_action)

        # Add panel submenu
        add_panel_menu = menu.addMenu("Add Panel")

        available_panels = self.available_panels
        for panel_class in available_panels:
            panel_action = QAction(panel_class.__name__, self)
            panel_action.triggered.connect(lambda checked, pc=panel_class: self.add_panel_from_class(pc))
            add_panel_menu.addAction(panel_action)

        menu.addSeparator()

        # Delete dock action
        delete_action = QAction("Delete Dock", self)
        delete_action.triggered.connect(self.delete_dock)
        menu.addAction(delete_action)

        menu.exec(event.globalPos())

    def add_panel_from_class(self, panel_class):
        """Add a new panel instance to this dock"""
        import math

        # Create a new panel instance
        panel_instance = panel_class(
            self,
            True,
            0,
            0,
            int(math.ceil(self.w_ratio * self.parent.width())),
            int(math.ceil(self.h_ratio * self.parent.height()))
        )

        # Add the panel to this dock
        self.add_panel(panel_instance, panel_class.__name__)

        # Switch to the newly added panel
        self.switch_tab(len(self.panels) - 1)

    def _visual_kwargs(self):
        """Return visual style kwargs to propagate to child docks created by splitting."""
        return dict(
            dock_bg=self.dock_bg,
            tab_bar_bg=self.tab_bar_bg,
            content_bg=self.content_bg,
            dock_border_color=self.dock_border_color,
            border_width=self.border_width,
            tab_text_color=self.tab_text_color,
            active_tab_color=self.active_tab_color,
            tab_height=self.tab_height,
            tab_radius=self.tab_radius,
            tab_padding=self.tab_padding,
            tab_spacing=self.tab_spacing,
            dock_padding=self.dock_padding,
            panel_bg=self.panel_bg,
            available_panels=self.available_panels,
            accent_color=self.accent_color,
        )

    def split_dock(self, direction):
        """Split this dock in the specified direction (left, right, top, bottom)"""
        if not hasattr(self.parent, 'add_dock') or not hasattr(self.parent, 'add_connector'):
            return

        from tabdock.hconnector import HConnector
        from tabdock.vconnector import VConnector
        vkw = self._visual_kwargs()

        match direction:
            case 'left':
                split_ratio = 0.5
                new_w_ratio = self.w_ratio * split_ratio

                # Remove self from HConnectors at its left edge (self moves right)
                old_left_x = self.x_ratio
                for conn in self.parent.connectors:
                    if isinstance(conn, HConnector) and abs(conn.x_ratio - old_left_x) < 0.01:
                        if self in conn.right_docks:
                            conn.right_docks.remove(self)

                # Create new dock on the left
                new_dock = Dock(self.parent, [], self.x_ratio, self.y_ratio, new_w_ratio, self.h_ratio, **vkw)
                self.parent.add_dock(new_dock)
                new_dock.show()

                # Adjust self (moves right)
                self.x_ratio = self.x_ratio + new_w_ratio
                self.w_ratio = self.w_ratio - new_w_ratio
                self.update_geometry()

                # Create independent connector: new_dock (left) | self (right)
                top_connector = None
                bottom_connector = None
                for conn in self.parent.connectors:
                    if isinstance(conn, VConnector):
                        if abs(conn.y_ratio - new_dock.y_ratio) < 0.01:
                            top_connector = conn
                        elif abs(conn.y_ratio - (new_dock.y_ratio + new_dock.h_ratio)) < 0.01:
                            bottom_connector = conn

                connector = HConnector(self.parent, self.x_ratio, [new_dock], [self], top_connector, bottom_connector)
                self.parent.add_connector(connector)

                # Add new_dock to any existing connector at its left edge
                for conn in self.parent.connectors:
                    if isinstance(conn, HConnector) and conn is not connector and abs(conn.x_ratio - new_dock.x_ratio) < 0.01:
                        if new_dock not in conn.right_docks:
                            conn.right_docks.append(new_dock)

                # Update VConnectors to include new_dock wherever self appears
                for conn in self.parent.connectors:
                    if isinstance(conn, VConnector):
                        if self in conn.top_docks and new_dock not in conn.top_docks:
                            conn.top_docks.append(new_dock)
                        if self in conn.bottom_docks and new_dock not in conn.bottom_docks:
                            conn.bottom_docks.append(new_dock)

                new_dock.raise_()
                self.raise_()

            case 'right':
                split_ratio = 0.5
                new_w_ratio = self.w_ratio * split_ratio

                # Remove self from HConnectors at its right edge (new_dock will be there)
                old_right_x = self.x_ratio + self.w_ratio
                for conn in self.parent.connectors:
                    if isinstance(conn, HConnector) and abs(conn.x_ratio - old_right_x) < 0.01:
                        if self in conn.left_docks:
                            conn.left_docks.remove(self)

                # Shrink self
                self.w_ratio = new_w_ratio
                self.update_geometry()

                # Create new dock on the right
                new_dock = Dock(self.parent, [], self.x_ratio + self.w_ratio, self.y_ratio, new_w_ratio, self.h_ratio, **vkw)
                self.parent.add_dock(new_dock)
                new_dock.show()

                # Create independent connector: self (left) | new_dock (right)
                top_connector = None
                bottom_connector = None
                for conn in self.parent.connectors:
                    if isinstance(conn, VConnector):
                        if abs(conn.y_ratio - self.y_ratio) < 0.01:
                            top_connector = conn
                        elif abs(conn.y_ratio - (self.y_ratio + self.h_ratio)) < 0.01:
                            bottom_connector = conn

                connector = HConnector(self.parent, new_dock.x_ratio, [self], [new_dock], top_connector, bottom_connector)
                self.parent.add_connector(connector)

                # Add new_dock to any existing connector at its right edge
                for conn in self.parent.connectors:
                    if isinstance(conn, HConnector) and conn is not connector and abs(conn.x_ratio - (new_dock.x_ratio + new_dock.w_ratio)) < 0.01:
                        if new_dock not in conn.left_docks:
                            conn.left_docks.append(new_dock)

                # Update VConnectors to include new_dock wherever self appears
                for conn in self.parent.connectors:
                    if isinstance(conn, VConnector):
                        if self in conn.top_docks and new_dock not in conn.top_docks:
                            conn.top_docks.append(new_dock)
                        if self in conn.bottom_docks and new_dock not in conn.bottom_docks:
                            conn.bottom_docks.append(new_dock)

                new_dock.raise_()
                self.raise_()

            case 'top':
                split_ratio = 0.5
                new_h_ratio = self.h_ratio * split_ratio

                # Remove self from VConnectors at its top edge (self moves down)
                old_top_y = self.y_ratio
                for conn in self.parent.connectors:
                    if isinstance(conn, VConnector) and abs(conn.y_ratio - old_top_y) < 0.01:
                        if self in conn.bottom_docks:
                            conn.bottom_docks.remove(self)

                # Create new dock on top
                new_dock = Dock(self.parent, [], self.x_ratio, self.y_ratio, self.w_ratio, new_h_ratio, **vkw)
                self.parent.add_dock(new_dock)
                new_dock.show()

                # Adjust self (moves down)
                self.y_ratio = self.y_ratio + new_h_ratio
                self.h_ratio = self.h_ratio - new_h_ratio
                self.update_geometry()

                # Create independent connector: new_dock (top) | self (bottom)
                left_connector = None
                right_connector = None
                for conn in self.parent.connectors:
                    if isinstance(conn, HConnector):
                        if abs(conn.x_ratio - new_dock.x_ratio) < 0.01:
                            left_connector = conn
                        elif abs(conn.x_ratio - (new_dock.x_ratio + new_dock.w_ratio)) < 0.01:
                            right_connector = conn

                connector = VConnector(self.parent, self.y_ratio, [new_dock], [self], left_connector, right_connector)
                self.parent.add_connector(connector)

                # Add new_dock to any existing connector at its top edge
                for conn in self.parent.connectors:
                    if isinstance(conn, VConnector) and conn is not connector and abs(conn.y_ratio - new_dock.y_ratio) < 0.01:
                        if new_dock not in conn.bottom_docks:
                            conn.bottom_docks.append(new_dock)

                # Update HConnectors to include new_dock wherever self appears
                for conn in self.parent.connectors:
                    if isinstance(conn, HConnector):
                        if self in conn.left_docks and new_dock not in conn.left_docks:
                            conn.left_docks.append(new_dock)
                        if self in conn.right_docks and new_dock not in conn.right_docks:
                            conn.right_docks.append(new_dock)

                new_dock.raise_()
                self.raise_()

            case 'bottom':
                split_ratio = 0.5
                new_h_ratio = self.h_ratio * split_ratio

                # Remove self from VConnectors at its bottom edge (new_dock will be there)
                old_bottom_y = self.y_ratio + self.h_ratio
                for conn in self.parent.connectors:
                    if isinstance(conn, VConnector) and abs(conn.y_ratio - old_bottom_y) < 0.01:
                        if self in conn.top_docks:
                            conn.top_docks.remove(self)

                # Shrink self
                self.h_ratio = new_h_ratio
                self.update_geometry()

                # Create new dock on the bottom
                new_dock = Dock(self.parent, [], self.x_ratio, self.y_ratio + self.h_ratio, self.w_ratio, new_h_ratio, **vkw)
                self.parent.add_dock(new_dock)
                new_dock.show()

                # Create independent connector: self (top) | new_dock (bottom)
                left_connector = None
                right_connector = None
                for conn in self.parent.connectors:
                    if isinstance(conn, HConnector):
                        if abs(conn.x_ratio - self.x_ratio) < 0.01:
                            left_connector = conn
                        elif abs(conn.x_ratio - (self.x_ratio + self.w_ratio)) < 0.01:
                            right_connector = conn

                connector = VConnector(self.parent, new_dock.y_ratio, [self], [new_dock], left_connector, right_connector)
                self.parent.add_connector(connector)

                # Add new_dock to any existing connector at its bottom edge
                for conn in self.parent.connectors:
                    if isinstance(conn, VConnector) and conn is not connector and abs(conn.y_ratio - (new_dock.y_ratio + new_dock.h_ratio)) < 0.01:
                        if new_dock not in conn.top_docks:
                            conn.top_docks.append(new_dock)

                # Update HConnectors to include new_dock wherever self appears
                for conn in self.parent.connectors:
                    if isinstance(conn, HConnector):
                        if self in conn.left_docks and new_dock not in conn.left_docks:
                            conn.left_docks.append(new_dock)
                        if self in conn.right_docks and new_dock not in conn.right_docks:
                            conn.right_docks.append(new_dock)

                new_dock.raise_()
                self.raise_()
                


    def delete_dock(self):
        """Delete this dock and redistribute its space to neighbors"""
        if hasattr(self.parent, 'delete_dock'):
            self.parent.delete_dock(self)

    def switch_tab(self, index):
        if 0 <= index < len(self.panels):
            if 0 <= self.dockIndex < len(self.panels):
                self.panels[self.dockIndex].hide()

            self.dockIndex = index
            self.panels[self.dockIndex].show()

            for i, button in enumerate(self.tab_buttons):
                if i == index:
                    button.setStyleSheet(f"background-color: {self.active_tab_color}; color: {self.tab_text_color}; border: none; padding: {self.tab_padding}; margin: 0px; border-top-left-radius: {self.tab_radius}px; border-top-right-radius: {self.tab_radius}px;")
                else:
                    button.setStyleSheet(f"background-color: {self.tab_bar_bg}; color: {self.tab_text_color}; border: none; padding: {self.tab_padding}; margin: 0px; border-top-left-radius: {self.tab_radius}px; border-top-right-radius: {self.tab_radius}px;")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() == "panel":
            if Dock._drag_source_dock is not None:
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
                return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() == "panel":
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
                panel = source_dock.panels[window_index]
                window_name = panel.__class__.__name__

                insert_index = self.drop_insert_index if self.drop_insert_index >= 0 else self._calculate_insert_index(pos)

                if source_dock == self:
                    if insert_index > window_index:
                        insert_index -= 1
                    if insert_index != window_index:
                        source_dock.remove_panel(window_index)
                        self._hide_drop_preview()
                        self.add_panel(panel, window_name, insert_index)
                    else:
                        self._hide_drop_preview()
                else:
                    source_dock.remove_panel(window_index)
                    self._hide_drop_preview()
                    self.add_panel(panel, window_name, insert_index)
                    if self.parent is None and self.panels:
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
                window = source_dock.panels[window_index]
                window_name = window.__class__.__name__

                from tabdock.dock import ExternalDock
                external_dock = ExternalDock(window_name)

                # Remove from source
                source_dock.remove_panel(window_index)

                # create dock
                external_dock.dock.add_panel(window, window_name, 0)
                cursor_pos = QCursor.pos()
                external_dock.move(cursor_pos.x() - 100, cursor_pos.y() - 20)
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

        if not result:
            tab_bar_height = tab_bar_rect.height()
            if pos.y() <= tab_bar_height + 5 or pos.y() <= 50:
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

    def _hide_dragged_tab(self, index):
        if 0 <= index < len(self.tab_buttons):
            self.tab_buttons[index].hide()
            if self.dockIndex == index:
                if len(self.panels) > 1:
                    for i in range(len(self.panels)):
                        if i != index:
                            self.switch_tab(i)
                            break
                else:
                    if 0 <= index < len(self.panels):
                        self.panels[index].hide()

    def _show_dragged_tab(self, index):
        if 0 <= index < len(self.tab_buttons):
            self.tab_buttons[index].show()

    def _update_drop_preview(self, pos):
        if Dock._drag_source_dock is None or Dock._drag_window_index is None:
            return

        insert_index = self._calculate_insert_index(pos)

        if self.preview_active and self.drop_insert_index == insert_index:
            return

        if Dock._preview_dock and Dock._preview_dock != self:
            Dock._preview_dock._hide_drop_preview()

        source_dock = Dock._drag_source_dock
        window_index = Dock._drag_window_index
        panel = source_dock.panels[window_index]
        window_name = panel.__class__.__name__

        is_same_dock = (Dock._preview_dock == self)

        if not is_same_dock:
            self._hide_drop_preview()

            for dw in self.panels:
                dw.hide()

            if source_dock != self:
                already_in_layout = False
                for i in range(self.content_layout.count()):
                    item = self.content_layout.itemAt(i)
                    if item and item.widget() == panel:
                        already_in_layout = True
                        break

                if not already_in_layout:
                    source_dock.content_layout.removeWidget(panel)
                    panel.setParent(self)
                    self.content_layout.addWidget(panel)

            panel.show()
            panel.raise_()
        else:
            if self.preview_button is not None:
                self.tab_bar.removeWidget(self.preview_button)
                self.preview_button.deleteLater()

        self.preview_button = QPushButton(window_name)
        self.preview_button.setFlat(True)
        self.preview_button.setStyleSheet(f"background-color: {self.active_tab_color}; color: {self.tab_text_color}; border: none; padding: {self.tab_padding}; margin: 0px; border-top-left-radius: {self.tab_radius}px; border-top-right-radius: {self.tab_radius}px; opacity: 0.7;")
        self.preview_button.setContentsMargins(0, 0, 0, 0)
        self.preview_button.setEnabled(False)

        self.tab_bar.insertWidget(insert_index, self.preview_button)
        self.preview_button.show()

        self.drop_insert_index = insert_index
        self.preview_active = True
        Dock._preview_dock = self

    def _hide_drop_preview(self):
        if self.preview_button is not None:
            self.preview_button.hide()
            self.tab_bar.removeWidget(self.preview_button)
            self.preview_button.setParent(None)
            self.preview_button.deleteLater()
            self.preview_button = None

        if not self.preview_active:
            return

        if Dock._drag_source_dock and Dock._drag_window_index is not None:
            source_dock = Dock._drag_source_dock
            window_index = Dock._drag_window_index
            if 0 <= window_index < len(source_dock.panels):
                panel = source_dock.panels[window_index]

                if source_dock != self:
                    panel.hide()

                    for i in range(self.content_layout.count()):
                        item = self.content_layout.itemAt(i)
                        if item and item.widget() == panel:
                            self.content_layout.removeWidget(panel)
                            break

                    panel.setParent(source_dock)

                    already_in_layout = False
                    for i in range(source_dock.content_layout.count()):
                        item = source_dock.content_layout.itemAt(i)
                        if item and item.widget() == panel:
                            already_in_layout = True
                            break

                    if not already_in_layout:
                        source_dock.content_layout.addWidget(panel)

                    if 0 <= source_dock.dockIndex < len(source_dock.panels):
                        if Dock._drag_window_index == source_dock.dockIndex:
                            pass
                        else:
                            source_dock.panels[source_dock.dockIndex].show()
                else:
                    panel.hide()

        for dw in self.panels:
            dw.hide()

        if len(self.panels) > 0 and 0 <= self.dockIndex < len(self.panels):
            if Dock._drag_source_dock == self and Dock._drag_window_index == self.dockIndex:
                pass
            else:
                self.panels[self.dockIndex].show()

        self.drop_insert_index = -1
        self.preview_active = False

        if Dock._preview_dock == self:
            Dock._preview_dock = None

    def remove_panel(self, index):
        if 0 <= index < len(self.panels):
            panel = self.panels.pop(index)
            button = self.tab_buttons.pop(index)

            panel.hide()
            self.content_layout.removeWidget(panel)
            panel.setParent(None)

            self.tab_bar.removeWidget(button)
            button.deleteLater()

            for i, btn in enumerate(self.tab_buttons):
                btn.index = i
                btn.clicked.disconnect()
                btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))

            if self.panels:
                # If we removed a panel before the active one, adjust the index
                if index < self.dockIndex:
                    self.dockIndex -= 1
                # Make sure dockIndex is still valid
                self.dockIndex = min(self.dockIndex, len(self.panels) - 1)
                self.switch_tab(self.dockIndex)
            else:
                self.dockIndex = 0
                # If this is an external dock and it's now empty, close it
                if isinstance(self.parent, ExternalDock):
                    self.parent.close()

    def add_panel(self, panel, panel_name, insert_index=None, is_external=False):
        if insert_index is None:
            insert_index = len(self.panels)

        insert_index = max(0, min(insert_index, len(self.panels)))

        tab_button = DraggableTabButton(panel_name, self, insert_index)
        tab_button.setFlat(True)
        tab_button.setStyleSheet(f"background-color: {self.tab_bar_bg}; color: {self.tab_text_color}; border: none; padding: {self.tab_padding}; margin: 0px;")
        tab_button.setContentsMargins(0, 0, 0, 0)
        tab_button.clicked.connect(lambda _, idx=insert_index: self.switch_tab(idx))
        self.tab_buttons.insert(insert_index, tab_button)
        self.tab_bar.insertWidget(insert_index, tab_button)

        panel.setParent(self)
        panel.hide()
        self.panels.insert(insert_index, panel)
        self.content_layout.addWidget(panel)

        for i, btn in enumerate(self.tab_buttons):
            btn.index = i
            btn.clicked.disconnect()
            btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))

        # Hide all panels before switching to ensure only one is visible
        for p in self.panels:
            p.hide()

        self.switch_tab(insert_index)

