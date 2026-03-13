from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout,
                              QLabel, QPushButton, QComboBox, QLineEdit,
                              QCheckBox, QSlider, QListWidget, QAbstractItemView)
from PyQt6.QtCore import Qt
from tabdock._style_guide import bg, black
from tabdock.panel_state import PanelStateManager


class Panel(QFrame):
    def __init__(self, parent, docked, x, y, w, h, *, panel_bg=None):
        super().__init__(parent)

        self.panel_bg     = panel_bg if panel_bg is not None else getattr(parent, 'panel_bg',       bg)
        self.text_color   = getattr(parent, 'tab_text_color',  'white')
        self.widget_bg    = getattr(parent, 'tab_bar_bg',      black)
        self.active_color = getattr(parent, 'active_tab_color', '#5080c0')
        self.accent_color = getattr(parent, 'accent_color',    '#5080c0')

        self.setStyleSheet(f"background-color: {self.panel_bg}; border: none; margin: 0px; padding: 0px;")
        self.setGeometry(x, y, w, h)
        self.setContentsMargins(0, 0, 0, 0)
        self.docked = docked

        # Subscriptions this instance has registered — cleaned up on destroy
        self._subscriptions: list[tuple[str, callable]] = []
        self.destroyed.connect(self._cleanup_subscriptions)

        # Root vertical layout — rows stack top to bottom
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(8, 8, 8, 8)
        self._root_layout.setSpacing(6)
        self._root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._current_row = self._make_row()

    # ------------------------------------------------------------------ #
    #  Shared state
    # ------------------------------------------------------------------ #

    @property
    def state(self) -> PanelStateManager:
        """Shared state manager for this panel's class (all instances share it)."""
        return PanelStateManager.for_class(type(self))

    def _init_key(self, key: str, default):
        """Set default value in state only if the key has never been set."""
        if not self.state.has(key):
            self.state.set(key, default)

    def _subscribe(self, key: str, callback, init: bool = True):
        """Subscribe to a state key and track it for cleanup."""
        self.state.subscribe(key, callback, init=init)
        self._subscriptions.append((key, callback))

    def _cleanup_subscriptions(self):
        for key, cb in self._subscriptions:
            self.state.unsubscribe(key, cb)
        self._subscriptions.clear()

    # ------------------------------------------------------------------ #
    #  Layout helpers
    # ------------------------------------------------------------------ #

    def _make_row(self):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._root_layout.addLayout(row)
        return row

    def next_row(self):
        """Start placing subsequent widgets on a new row."""
        self._current_row = self._make_row()

    def add_spacer(self, height: int = 8):
        """Add vertical blank space between rows."""
        self._root_layout.addSpacing(height)

    # ------------------------------------------------------------------ #
    #  Widget factories
    # ------------------------------------------------------------------ #

    def add_label(self, text: str, state_key: str = None,
                  state_format=None, default=None) -> QLabel:
        """Plain text label. Subscribes to any state key and displays its value.

        Args:
            state_key:    Key to subscribe to (any type — use state_format to convert).
            state_format: Callable(value) -> str. Defaults to str().
            default:      Initial value written to state if the key is new.
        """
        w = QLabel(text, self)
        w.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color};
                background: transparent;
                padding: 2px 0px;
                font-size: 12px;
            }}
        """)
        if state_key is not None:
            if default is not None:
                self._init_key(state_key, default)
            fmt = state_format or str
            self._subscribe(state_key, lambda v: w.setText(fmt(v)))
        self._current_row.addWidget(w)
        return w

    def add_section_label(self, text: str) -> QLabel:
        """Bold section-header label."""
        w = QLabel(text, self)
        w.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color};
                background: transparent;
                padding: 2px 0px;
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        self._current_row.addWidget(w)
        return w

    def add_button(self, text: str, callback=None,
                   bool_key: str = None, default: bool = False,
                   on_text: str = None, off_text: str = None) -> QPushButton:
        """Styled push button.

        Args:
            bool_key: Clicking toggles a bool in shared state under this key.
                      on_text / off_text optionally relabel the button on each state.
            default:  Initial bool value if the key is new (default False).
            callback: Called on click, or with the new bool when bool_key is set.
        """
        w = QPushButton(text, self)
        w.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.widget_bg};
                color: {self.text_color};
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 5px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border: 1px solid {self.accent_color};
            }}
            QPushButton:pressed {{
                background-color: {self.panel_bg};
                border: 1px solid {self.accent_color};
            }}
        """)
        if bool_key is not None:
            self._init_key(bool_key, default)

            def _on_click():
                new_val = not self.state.get(bool_key, default)
                self.state.set(bool_key, new_val)
                if callback:
                    callback(new_val)
            w.clicked.connect(_on_click)

            if on_text is not None or off_text is not None:
                _on  = on_text  or text
                _off = off_text or text
                self._subscribe(bool_key, lambda v: w.setText(_on if v else _off))
        else:
            if callback:
                w.clicked.connect(callback)
        self._current_row.addWidget(w)
        return w

    def add_dropdown(self, options: list, callback=None,
                     string_key: str = None, default: str = None) -> QComboBox:
        """Styled combo box / dropdown.

        Args:
            string_key: Syncs the selected text with shared state.
            default:    Initial selected text if the key is new.
                        Falls back to the first option if not given.
        """
        w = QComboBox(self)
        w.addItems([str(o) for o in options])
        w.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.widget_bg};
                color: {self.text_color};
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 18px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.widget_bg};
                color: {self.text_color};
                selection-background-color: {self.active_color};
                border: none;
                outline: none;
            }}
        """)
        if string_key is not None:
            init_val = default if default is not None else (options[0] if options else "")
            self._init_key(string_key, str(init_val))
            _syncing = [False]

            def _on_user_change():
                if not _syncing[0]:
                    self.state.set(string_key, w.currentText())
                    if callback:
                        callback(w.currentText())
            w.currentTextChanged.connect(_on_user_change)

            def _sync(val):
                _syncing[0] = True
                idx = w.findText(str(val))
                if idx >= 0:
                    w.setCurrentIndex(idx)
                _syncing[0] = False
            self._subscribe(string_key, _sync)
        else:
            if callback:
                w.currentIndexChanged.connect(callback)
        self._current_row.addWidget(w)
        return w

    def add_text_input(self, placeholder: str = "", callback=None,
                       string_key: str = None, default: str = "") -> QLineEdit:
        """Styled single-line text input.

        Args:
            string_key: Syncs the text content with shared state.
            default:    Initial text if the key is new.
        """
        w = QLineEdit(self)
        w.setPlaceholderText(placeholder)
        w.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.widget_bg};
                color: {self.text_color};
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {self.accent_color};
            }}
        """)
        if string_key is not None:
            self._init_key(string_key, default)
            _syncing = [False]

            def _on_user_change(text):
                if not _syncing[0]:
                    self.state.set(string_key, text)
                    if callback:
                        callback(text)
            w.textChanged.connect(_on_user_change)

            def _sync(val):
                _syncing[0] = True
                w.setText(str(val))
                _syncing[0] = False
            self._subscribe(string_key, _sync)
        else:
            if callback:
                w.textChanged.connect(callback)
        self._current_row.addWidget(w)
        return w

    def add_checkbox(self, text: str, callback=None,
                     bool_key: str = None, default: bool = False) -> QCheckBox:
        """Styled checkbox.

        Args:
            bool_key: Syncs the checked state with shared state.
            default:  Initial checked value if the key is new.
        """
        w = QCheckBox(text, self)
        w.setStyleSheet(f"""
            QCheckBox {{
                color: {self.text_color};
                background: transparent;
                font-size: 12px;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                background-color: {self.widget_bg};
                border: none;
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.accent_color};
            }}
        """)
        if bool_key is not None:
            self._init_key(bool_key, default)
            _syncing = [False]

            def _on_user_change(state):
                if not _syncing[0]:
                    val = bool(state)
                    self.state.set(bool_key, val)
                    if callback:
                        callback(val)
            w.stateChanged.connect(_on_user_change)

            def _sync(val):
                _syncing[0] = True
                w.setChecked(bool(val))
                _syncing[0] = False
            self._subscribe(bool_key, _sync)
        else:
            if callback:
                w.stateChanged.connect(callback)
        self._current_row.addWidget(w)
        return w

    def add_slider(self, minimum: int = 0, maximum: int = 100,
                   value: int = None, callback=None,
                   int_key: str = None, default: int = None) -> QSlider:
        """Horizontal slider.

        Args:
            int_key: Syncs the slider value with shared state.
            default: Initial value in state if the key is new.
                     Falls back to `value`, then to `minimum`.
        """
        w = QSlider(Qt.Orientation.Horizontal, self)
        w.setMinimum(minimum)
        w.setMaximum(maximum)
        w.setMinimumWidth(100)
        if value is not None:
            w.setValue(value)
        w.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 4px;
                background: {self.widget_bg};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                width: 14px;
                height: 14px;
                margin: -5px 0;
                background: {self.text_color};
                border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self.accent_color};
                border-radius: 2px;
            }}
        """)
        if int_key is not None:
            init_val = default if default is not None else (value if value is not None else minimum)
            self._init_key(int_key, init_val)
            _syncing = [False]

            def _on_user_change(v):
                if not _syncing[0]:
                    self.state.set(int_key, v)
                    if callback:
                        callback(v)
            w.valueChanged.connect(_on_user_change)

            def _sync(v):
                _syncing[0] = True
                w.setValue(int(v))
                _syncing[0] = False
            self._subscribe(int_key, _sync)
        else:
            if callback:
                w.valueChanged.connect(callback)
        self._current_row.addWidget(w)
        return w

    def add_list(self, items: list, multi_select: bool = False,
                 list_key: str = None, default: list = None,
                 callback=None) -> QListWidget:
        """Scrollable list widget (full width, expands vertically).

        Args:
            items:        Strings to display.
            multi_select: Allow selecting multiple items (default False).
            list_key:     Syncs the selection across all instances via shared state.
            default:      Initial selection list if the key is new (default []).
            callback:     Called with list of selected strings on selection change.
        """
        w = QListWidget(self)
        w.addItems([str(i) for i in items])
        w.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
            if multi_select else
            QAbstractItemView.SelectionMode.SingleSelection
        )
        w.setStyleSheet(f"""
            QListWidget {{
                background-color: {self.widget_bg};
                color: {self.text_color};
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 2px;
                font-size: 12px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 4px 8px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {self.accent_color};
                color: {self.panel_bg};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {self.panel_bg};
            }}
            QScrollBar:vertical {{
                background: {self.panel_bg};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.widget_bg};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        if list_key is not None:
            self._init_key(list_key, default if default is not None else [])
            _syncing = [False]

            def _on_user_select():
                if _syncing[0]:
                    return
                selected = [w.item(i).text() for i in range(w.count())
                            if w.item(i).isSelected()]
                self.state.set(list_key, selected)
                if callback:
                    callback(selected)

            def _sync(selected):
                _syncing[0] = True
                w.clearSelection()
                for i in range(w.count()):
                    if w.item(i).text() in selected:
                        w.item(i).setSelected(True)
                _syncing[0] = False

            w.itemSelectionChanged.connect(_on_user_select)
            self._subscribe(list_key, _sync)
        else:
            if callback:
                w.itemSelectionChanged.connect(
                    lambda: callback([w.item(i).text() for i in range(w.count())
                                      if w.item(i).isSelected()])
                )
        self._root_layout.addWidget(w)
        self._current_row = self._make_row()
        return w

    def add_separator(self) -> QFrame:
        """Full-width horizontal divider line (always on its own row)."""
        line = QFrame(self)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {self.widget_bg}; border: none;")
        self._root_layout.addWidget(line)
        self._current_row = self._make_row()
        return line
