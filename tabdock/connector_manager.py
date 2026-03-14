from PyQt6.QtCore import Qt, QObject, QEvent
from tabdock.tab import Tab


class ConnectorManager(QObject):
    """Manages all HConnector and VConnector instances and handles mouse events via event filter."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_widget = parent
        self.connectors: list = []
        self.active_connector = None
        self.current_cursor = Qt.CursorShape.ArrowCursor
        self._cursor_widgets: set = set()  # widgets we've set a cursor on
        # Track last event to avoid duplicate processing as events bubble
        self.last_processed_event = None

        # Enable mouse tracking so we get mouse move events even without buttons pressed
        parent.setMouseTracking(True)

        # Install event filter on parent widget
        parent.installEventFilter(self)

    def add_connector(self, connector):
        """Register a connector (HConnector or VConnector) with the manager."""
        self.connectors.append(connector)

        # Enable mouse tracking on all child widgets (in case new ones were added)
        self._enable_tracking_on_children()

    def remove_connector(self, connector):
        """Unregister a connector."""
        if connector in self.connectors:
            self.connectors.remove(connector)

    def _enable_tracking_on_children(self):
        """Enable mouse tracking on all child widgets AND install event filter on them."""
        from PyQt6.QtWidgets import QWidget

        children = self.parent_widget.findChildren(QWidget)
        for child in children:
            if not child.hasMouseTracking():
                child.setMouseTracking(True)
            # Install event filter on children so we can intercept events before they're consumed
            child.installEventFilter(self)

    def _find_closest_connector(self, pos, current_tab=None):
        """Find the connector closest to the given position.

        If ``current_tab`` is provided, only consider connectors that belong to
        that :class:`Tab`. This avoids accidentally dragging connectors for a
        hidden tab, which would update invisible docks and appear to "do
        nothing" to the user.
        """

        closest_connector = None
        min_distance = float("inf")

        for connector in self.connectors:
            # If we know which Tab this event came from, restrict candidates
            # to connectors that belong to that Tab.
            if current_tab is not None:
                connector_tab = getattr(connector, "tab", None)
                if connector_tab is not None and connector_tab is not current_tab:
                    continue

            if connector.is_near_connector(pos):
                distance = connector.get_distance_to_connector(pos)
                if distance < min_distance:
                    min_distance = distance
                    closest_connector = connector

        return closest_connector

    def _set_cursor(self, cursor_shape, source_widget=None):
        """Set cursor on the source widget and the parent widget."""
        self.current_cursor = cursor_shape
        self.parent_widget.setCursor(cursor_shape)
        if source_widget is not None and source_widget is not self.parent_widget:
            source_widget.setCursor(cursor_shape)
            self._cursor_widgets.add(source_widget)

    def _unset_cursor(self):
        """Restore default cursor on parent and all modified child widgets."""
        self.current_cursor = Qt.CursorShape.ArrowCursor
        self.parent_widget.unsetCursor()
        for w in self._cursor_widgets:
            try:
                w.unsetCursor()
            except RuntimeError:
                pass  # widget was deleted
        self._cursor_widgets.clear()

    def _get_pos(self, obj, event):
        """Extract position in parent_widget coordinates from a mouse event."""
        if not hasattr(event, "pos"):
            return None
        if obj == self.parent_widget:
            return event.pos()
        return obj.mapTo(self.parent_widget, event.pos())

    def _get_current_tab(self, obj):
        """Walk up from obj to find the Tab ancestor, if any."""
        widget = obj
        while widget is not None:
            if isinstance(widget, Tab):
                return widget
            widget = widget.parentWidget()
        return None

    def eventFilter(self, obj, event):
        """Filter events on the parent widget to handle connector interactions."""

        event_type = event.type()

        # Handle Leave early — it has no position data
        if event_type == QEvent.Type.Leave:
            if not self.active_connector:
                self._unset_cursor()
            return False

        if event_type not in (
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
        ):
            return False

        pos = self._get_pos(obj, event)
        if pos is None:
            return False

        current_tab = self._get_current_tab(obj)

        # Handle mouse press
        if event_type == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                closest = self._find_closest_connector(pos, current_tab)
                if closest:
                    self.active_connector = closest
                    self.active_connector.start_drag(pos)
                    self._set_cursor(
                        self.active_connector.get_cursor_shape(is_dragging=True), obj
                    )
                    return True

        # Handle mouse move
        elif event_type == QEvent.Type.MouseMove:
            active = self.active_connector
            if active:
                active.update_drag(pos)
                self._set_cursor(active.get_cursor_shape(is_dragging=True), obj)
                return True
            else:
                closest = self._find_closest_connector(pos, current_tab)
                if closest:
                    self._set_cursor(closest.get_cursor_shape(is_dragging=False), obj)
                else:
                    self._unset_cursor()

        # Handle mouse release
        elif event_type == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton and self.active_connector:
                self.active_connector.end_drag(pos)

                closest = self._find_closest_connector(pos, current_tab)
                if closest:
                    self._set_cursor(closest.get_cursor_shape(is_dragging=False), obj)
                else:
                    self._unset_cursor()

                self.active_connector = None
                return True

        return False
