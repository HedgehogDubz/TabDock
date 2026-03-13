from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton
from tabdock._style_guide import bg, black, border_color
from tabdock.connector_manager import ConnectorManager

class TabDock(QWidget):
    def __init__(self, parent=None, create_external_docks=False, min_dock_size=100, *,
                 tab_height=50,
                 tab_bar_bg=None,
                 content_bg=None,
                 tab_text_color="white",
                 active_tab_color=None,
                 tab_button_padding="0px 15px",
                 tab_spacing=3,
                 tab_radius=5,
                 dock_bg=None,
                 dock_border_color=None,
                 border_width=2,
                 dock_tab_height=25,
                 dock_tab_padding="5px 10px",
                 dock_tab_spacing=0,
                 dock_padding=2,
                 panel_bg=None,
                 available_panels=None,
                 accent_color=None):
        super().__init__(parent)

        self.available_panels = available_panels or []
        self.accent_color = accent_color if accent_color is not None else '#5080c0'

        # Own visual params
        self.tab_height = tab_height
        self.tab_bar_bg = tab_bar_bg if tab_bar_bg is not None else black
        self.content_bg = content_bg if content_bg is not None else bg
        self.tab_text_color = tab_text_color
        self.active_tab_color = active_tab_color if active_tab_color is not None else bg
        self.tab_button_padding = tab_button_padding
        self.tab_spacing = tab_spacing
        self.tab_radius = tab_radius

        # Cascade-only params (passed down to Tab → Dock → Panel)
        self.dock_bg = dock_bg if dock_bg is not None else black
        self.dock_border_color = dock_border_color if dock_border_color is not None else border_color
        self.border_width = border_width
        self.dock_tab_height = dock_tab_height
        self.dock_tab_radius = tab_radius
        self.dock_tab_padding = dock_tab_padding
        self.dock_tab_spacing = dock_tab_spacing
        self.dock_padding = dock_padding
        self.panel_bg = panel_bg if panel_bg is not None else bg

        self.tabIndex = 0
        self.tabs = []
        self.docks = []
        self.connectors = []
        self.min_dock_size = min_dock_size

        self.tab_buttons = []

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.tab_chooser_widget = QWidget()
        self.tab_chooser_widget.setStyleSheet(f"background-color: {self.tab_bar_bg};")
        self.tab_chooser_widget.setFixedHeight(self.tab_height)

        self.tab_chooser_layout = QHBoxLayout(self.tab_chooser_widget)
        self.tab_chooser_layout.setContentsMargins(0, 0, 5, 8)
        self.tab_chooser_layout.setSpacing(self.tab_spacing)
        self.tab_chooser_layout.addStretch()

        self.tab_content_widget = QWidget()
        self.tab_content_widget.setStyleSheet(f"background-color: {self.content_bg};")
        self.tab_content_widget.setAcceptDrops(True)

        self.main_layout.addWidget(self.tab_chooser_widget)
        self.main_layout.addWidget(self.tab_content_widget, 1)

        self.create_external_docks = create_external_docks

        self.connector_manager = ConnectorManager(self.tab_content_widget)

    def add_tab(self, tab):
        index = len(self.tabs)
        self.tabs.append(tab)
        tab.setParent(self.tab_content_widget)
        tab.tab_content_widget = self.tab_content_widget

        tab_button = QPushButton(tab.name)
        tab_button.setFixedHeight(self.tab_height - 10)
        tab_button.setStyleSheet(f"background-color: {self.tab_bar_bg}; color: {self.tab_text_color}; border: none; padding: {self.tab_button_padding}; border-bottom-left-radius: {self.tab_radius}px; border-bottom-right-radius: {self.tab_radius}px;")
        tab_button.clicked.connect(lambda _, idx=index: self.switch_tab(idx))
        self.tab_buttons.append(tab_button)

        self.tab_chooser_layout.insertWidget(index, tab_button)

        if len(self.tabs) == 1:
            self.switch_tab(0)
        else:
            tab.hide()

    def add_dock(self, dock):
        self.docks.append(dock)

    def remove_dock(self, dock):
        if dock in self.docks:
            self.docks.remove(dock)

    def add_connector(self, connector):
        self.connectors.append(connector)
        self.connector_manager.add_connector(connector)

    def remove_connector(self, connector):
        if connector in self.connectors:
            self.connectors.remove(connector)
            self.connector_manager.remove_connector(connector)

    def switch_tab(self, index):
        if 0 <= index < len(self.tabs):
            if 0 <= self.tabIndex < len(self.tabs):
                self.tabs[self.tabIndex].hide()

            self.tabIndex = index
            current_tab = self.tabs[self.tabIndex]
            current_tab.setGeometry(0, 0, self.tab_content_widget.width(), self.tab_content_widget.height())
            current_tab.show()
            current_tab.raise_()

            for i, button in enumerate(self.tab_buttons):
                if i == index:
                    button.setStyleSheet(f"background-color: {self.active_tab_color}; color: {self.tab_text_color}; border: none; padding: {self.tab_button_padding}; border-bottom-left-radius: {self.tab_radius}px; border-bottom-right-radius: {self.tab_radius}px;")
                else:
                    button.setStyleSheet(f"background-color: {self.tab_bar_bg}; color: {self.tab_text_color}; border: none; padding: {self.tab_button_padding}; border-bottom-left-radius: {self.tab_radius}px; border-bottom-right-radius: {self.tab_radius}px;")

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if 0 <= self.tabIndex < len(self.tabs):
            self.tabs[self.tabIndex].setGeometry(0, 0, self.tab_content_widget.width(), self.tab_content_widget.height())

        for dock in self.docks:
            dock.update_geometry()

