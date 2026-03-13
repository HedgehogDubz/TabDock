from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt


class VConnector(QWidget):
    def __init__(self, parent, y_ratio, top_docks, bottom_docks, left_connector=None, right_connector=None):
        super().__init__(parent)
        self.tab = parent
        self.y_ratio = y_ratio
        self.top_docks = top_docks
        self.bottom_docks = bottom_docks
        self.left_connector = left_connector
        self.right_connector = right_connector
        self.is_dragging = False
        self.hit_zone_height = 10
        self.min_dock_size = getattr(parent, 'min_dock_size', 100)

        for td in self.top_docks:
            td.h_ratio = self.y_ratio - td.y_ratio
            td.update_geometry()

        for bd in self.bottom_docks:
            bd.y_ratio = self.y_ratio
            bd.update_geometry()

    def get_distance_to_connector(self, pos):
        """Calculate distance from pos to the connector line"""
        connector_y = self.y_ratio * self.tab.height()
        mouse_y = pos.y()
        return abs(mouse_y - connector_y)

    def is_near_connector(self, pos):
        """Check if position is within hit zone and valid draggable area"""
        if self.get_distance_to_connector(pos) > self.hit_zone_height:
            return False

        if self.left_connector and self.right_connector:
            left_x = self.left_connector.x_ratio * self.tab.width()
            right_x = self.right_connector.x_ratio * self.tab.width()
            if not (left_x <= pos.x() <= right_x):
                return False
        

        mouse_x_ratio = pos.x() / self.tab.width()
        top_min_x = min(dock.x_ratio for dock in self.top_docks) if self.top_docks else 0
        top_max_x = max(dock.x_ratio + dock.w_ratio for dock in self.top_docks) if self.top_docks else 0
        bottom_min_x = min(dock.x_ratio for dock in self.bottom_docks) if self.bottom_docks else 0
        bottom_max_x = max(dock.x_ratio + dock.w_ratio for dock in self.bottom_docks) if self.bottom_docks else 0
        overlap_min_x = max(top_min_x, bottom_min_x)
        overlap_max_x = min(top_max_x, bottom_max_x)
        return overlap_min_x <= mouse_x_ratio <= overlap_max_x

    def start_drag(self, pos):
        """Called by ConnectorManager when drag starts"""
        self.is_dragging = True
        self.drag_start_position = pos

        mouse_ratio = pos.y() / self.tab.height()
        mouse_ratio = self._clamp_position(mouse_ratio)

        self.drag_start_ratio = mouse_ratio
        self.drag_start_connector_ratio = mouse_ratio
        self.y_ratio = mouse_ratio

        for td in self.top_docks:
            td.h_ratio = mouse_ratio - td.y_ratio
            td.update_geometry()

        for bd in self.bottom_docks:
            bottom_edge = bd.y_ratio + bd.h_ratio
            bd.y_ratio = mouse_ratio
            bd.h_ratio = bottom_edge - mouse_ratio
            bd.update_geometry()

        self.tab.repaint()

    def update_drag(self, pos):
        """Called by ConnectorManager during drag"""
        if not self.is_dragging:
            return

        current_mouse_ratio = pos.y() / self.tab.height()
        mouse_delta = current_mouse_ratio - self.drag_start_ratio
        new_connector_ratio = self.drag_start_connector_ratio + mouse_delta
        new_connector_ratio = self._clamp_position(new_connector_ratio)

        self.y_ratio = new_connector_ratio

        for td in self.top_docks:
            td.h_ratio = new_connector_ratio - td.y_ratio
            td.update_geometry()

        for bd in self.bottom_docks:
            bottom_edge = bd.y_ratio + bd.h_ratio
            bd.y_ratio = new_connector_ratio
            bd.h_ratio = bottom_edge - new_connector_ratio
            bd.update_geometry()

        self.tab.repaint()

    def end_drag(self, pos):
        """Called by ConnectorManager when drag ends"""
        self.is_dragging = False

    def _clamp_position(self, new_ratio):
        """Clamp connector position to respect minimum dock sizes"""
        min_height_ratio = self.min_dock_size / self.tab.height()

        max_top = max(td.y_ratio + min_height_ratio for td in self.top_docks) if self.top_docks else 0
        min_bottom = min(bd.y_ratio + bd.h_ratio - min_height_ratio for bd in self.bottom_docks) if self.bottom_docks else 1

        return max(max_top, min(new_ratio, min_bottom))

    def get_cursor_shape(self, is_dragging=False):
        """Return appropriate cursor shape"""
        if is_dragging:
            return Qt.CursorShape.ClosedHandCursor
        return Qt.CursorShape.SplitVCursor

