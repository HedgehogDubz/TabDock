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

    def _set_cursor(self, cursor_shape):
        """Set cursor only if it's different from current cursor."""

        if self.current_cursor != cursor_shape:
            self.current_cursor = cursor_shape
            self.parent_widget.setCursor(cursor_shape)

    def _unset_cursor(self):
        """Restore default cursor."""

        self._set_cursor(Qt.CursorShape.ArrowCursor)

    def eventFilter(self, obj, event):
        """Filter events on the parent widget to handle connector interactions."""

        # Process mouse events
        event_type = event.type()

        if event_type not in [
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.Leave,
            QEvent.Type.Enter,
        ]:
            return False

        # Create a unique identifier for this event to avoid processing it
        # multiple times as it bubbles up through the widget hierarchy
        if hasattr(event, "pos"):
            event_id = (
                event_type,
                event.pos().x(),
                event.pos().y(),
                event.timestamp() if hasattr(event, "timestamp") else 0,
            )

            if self.last_processed_event == event_id:
                return False

            self.last_processed_event = event_id

        # Convert position to parent widget coordinates 
        if hasattr(event, "pos"):
            if obj == self.parent_widget:
                pos = event.pos()
            else:
                # Map from child widget to parent widget coordinates
                pos = obj.mapTo(self.parent_widget, event.pos())
        else:
            return False

        # Determine which Tab this event originated from (if any) so that
        # we only interact with connectors/docks belonging to that Tab.
        current_tab = None
        widget = obj
        while widget is not None:
            if isinstance(widget, Tab):
                current_tab = widget
                break
            widget = widget.parentWidget()

        # Handle mouse press
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                closest = self._find_closest_connector(pos, current_tab)

                if closest:
                    self.active_connector = closest
                    self.active_connector.start_drag(pos)
                    self._set_cursor(
                        self.active_connector.get_cursor_shape(is_dragging=True)
                    )
                    return True

        # Handle mouse move
        elif event.type() == QEvent.Type.MouseMove:
            active = self.active_connector
            if active:
                active.update_drag(pos)
                self._set_cursor(active.get_cursor_shape(is_dragging=True))
                return True
            else:
                closest = self._find_closest_connector(pos, current_tab)
                if closest:
                    self._set_cursor(closest.get_cursor_shape(is_dragging=False))
                else:
                    self._unset_cursor()

        # Handle mouse leave
        elif event.type() == QEvent.Type.Leave:
            if not self.active_connector:
                self._unset_cursor()

        # Handle mouse release
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton and self.active_connector:
                self.active_connector.end_drag(pos)

                closest = self._find_closest_connector(pos, current_tab)
                if closest:
                    self._set_cursor(closest.get_cursor_shape(is_dragging=False))
                else:
                    self._unset_cursor()

                self.active_connector = None
                return True

        # Let the event pass through
        return False
