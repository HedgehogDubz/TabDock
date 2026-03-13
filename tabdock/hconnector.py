from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt


class HConnector(QWidget):
    def __init__(self, parent, x_ratio, left_docks, right_docks, top_connector=None, bottom_connector=None):
        super().__init__(parent)
        self.tab = parent
        self.x_ratio = x_ratio
        self.left_docks = left_docks
        self.right_docks = right_docks
        self.top_connector = top_connector
        self.bottom_connector = bottom_connector
        self.is_dragging = False
        self.hit_zone_width = 10
        self.min_dock_size = getattr(parent, 'min_dock_size', 100)

        for ld in self.left_docks:
            ld.w_ratio = self.x_ratio - ld.x_ratio
            ld.update_geometry()

        for rd in self.right_docks:
            rd.x_ratio = self.x_ratio
            rd.update_geometry()

    def get_distance_to_connector(self, pos):
        """Calculate distance from pos to the connector line"""
        connector_x = self.x_ratio * self.tab.width()
        mouse_x = pos.x()
        return abs(mouse_x - connector_x)

    def is_near_connector(self, pos):
        """Check if position is within hit zone and valid draggable area"""
        distance = self.get_distance_to_connector(pos)

        if distance > self.hit_zone_width:
            return False

        if self.top_connector and self.bottom_connector:
            top_y = self.top_connector.y_ratio * self.tab.height()
            bottom_y = self.bottom_connector.y_ratio * self.tab.height()
            if not (top_y <= pos.y() <= bottom_y):
                return False



        mouse_y_ratio = pos.y() / self.tab.height()
        left_min_y = min(dock.y_ratio for dock in self.left_docks) if self.left_docks else 0
        left_max_y = max(dock.y_ratio + dock.h_ratio for dock in self.left_docks) if self.left_docks else 0
        right_min_y = min(dock.y_ratio for dock in self.right_docks) if self.right_docks else 0
        right_max_y = max(dock.y_ratio + dock.h_ratio for dock in self.right_docks) if self.right_docks else 0
        overlap_min_y = max(left_min_y, right_min_y)
        overlap_max_y = min(left_max_y, right_max_y)

        return overlap_min_y <= mouse_y_ratio <= overlap_max_y

    def start_drag(self, pos):
        """Called by ConnectorManager when drag starts"""
        self.is_dragging = True
        self.drag_start_position = pos

        mouse_ratio = pos.x() / self.tab.width()
        mouse_ratio = self._clamp_position(mouse_ratio)

        self.drag_start_ratio = mouse_ratio
        self.drag_start_connector_ratio = mouse_ratio
        self.x_ratio = mouse_ratio

        for ld in self.left_docks:
            ld.w_ratio = mouse_ratio - ld.x_ratio
            ld.update_geometry()

        for rd in self.right_docks:
            right_edge = rd.x_ratio + rd.w_ratio
            rd.x_ratio = mouse_ratio
            rd.w_ratio = right_edge - mouse_ratio
            rd.update_geometry()

        self.tab.repaint()

    def update_drag(self, pos):
        """Called by ConnectorManager during drag"""
        if not self.is_dragging:
            return

        current_mouse_ratio = pos.x() / self.tab.width()
        mouse_delta = current_mouse_ratio - self.drag_start_ratio
        new_connector_ratio = self.drag_start_connector_ratio + mouse_delta
        new_connector_ratio = self._clamp_position(new_connector_ratio)

        self.x_ratio = new_connector_ratio

        for ld in self.left_docks:
            ld.w_ratio = new_connector_ratio - ld.x_ratio
            ld.update_geometry()

        for rd in self.right_docks:
            right_edge = rd.x_ratio + rd.w_ratio
            rd.x_ratio = new_connector_ratio
            rd.w_ratio = right_edge - new_connector_ratio
            rd.update_geometry()

        self.tab.repaint()

    def end_drag(self, pos):
        """Called by ConnectorManager when drag ends"""
        self.is_dragging = False

    def _clamp_position(self, new_ratio):
        """Clamp connector position to respect minimum dock sizes"""
        min_width_ratio = self.min_dock_size / self.tab.width()

        max_left = max(ld.x_ratio + min_width_ratio for ld in self.left_docks) if self.left_docks else 0
        min_right = min(rd.x_ratio + rd.w_ratio - min_width_ratio for rd in self.right_docks) if self.right_docks else 1

        return max(max_left, min(new_ratio, min_right))

    def get_cursor_shape(self, is_dragging=False):
        """Return appropriate cursor shape"""
        if is_dragging:
            return Qt.CursorShape.ClosedHandCursor
        return Qt.CursorShape.SplitHCursor

