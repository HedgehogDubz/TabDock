from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton
from UI._style_guide import bg, black

class TabDock(QWidget):
    def __init__(self, parent=None, create_external_docks=False):
        super().__init__(parent)

        self.tabIndex = 0
        self.tabs = []
        self.docks = []
        
        self.tab_buttons = []

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.tab_chooser_widget = QWidget()
        self.tab_chooser_widget.setStyleSheet(f"background-color: {black};")
        self.tab_chooser_widget.setFixedHeight(50)

        self.tab_chooser_layout = QHBoxLayout(self.tab_chooser_widget)
        self.tab_chooser_layout.setContentsMargins(5, 5, 5, 5)
        self.tab_chooser_layout.setSpacing(5)
        self.tab_chooser_layout.addStretch()

        self.tab_content_widget = QWidget()
        self.tab_content_widget.setStyleSheet(f"background-color: {bg};")
        self.tab_content_widget.setAcceptDrops(True)

        self.main_layout.addWidget(self.tab_chooser_widget)
        self.main_layout.addWidget(self.tab_content_widget, 1)

        self.create_external_docks = create_external_docks

    def add_tab(self, tab):
        index = len(self.tabs)
        self.tabs.append(tab)
        tab.setParent(self.tab_content_widget)
        tab.tab_content_widget = self.tab_content_widget

        tab_button = QPushButton(tab.name)
        tab_button.setFixedHeight(40)
        tab_button.setStyleSheet(f"background-color: {black}; color: white; border: 0px solid {black}; padding: 8px 15px; border-radius: 5px;")
        tab_button.clicked.connect(lambda _, idx=index: self.switch_tab(idx))
        self.tab_buttons.append(tab_button)

        self.tab_chooser_layout.insertWidget(index, tab_button)

        if len(self.tabs) == 1:
            self.switch_tab(0)
        else:
            tab.hide()

    def add_dock(self, dock):
        self.docks.append(dock)

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
                    button.setStyleSheet(f"background-color: {bg}; color: white; padding: 8px 15px; border-radius: 5px;")
                else:
                    button.setStyleSheet(f"background-color: {black}; color: white; padding: 8px 15px; border-radius: 5px;")

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if 0 <= self.tabIndex < len(self.tabs):
            self.tabs[self.tabIndex].setGeometry(0, 0, self.tab_content_widget.width(), self.tab_content_widget.height())

        for dock in self.docks:
            dock.update_geometry()

