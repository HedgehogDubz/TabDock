from PyQt6.QtWidgets import QWidget
from UI.dock import Dock

class Tab(QWidget):
    def __init__(self, parent, name, index):
        super().__init__(parent)
        self.parent = parent

        self.name = name
        self.index = index
        self.docks = []
        self.connectors = []
        self.min_dock_size = getattr(parent, 'min_dock_size', 100)

        self.initUI()

    def initUI(self):
        pass

    def add_dock(self, dock):
        self.docks.append(dock)
        self.parent.add_dock(dock)
        return dock

    def remove_dock(self, dock):
        if dock in self.docks:
            self.docks.remove(dock)
            self.parent.remove_dock(dock)

    def centralWidget(self):
        return self.tab_content_widget if hasattr(self, 'tab_content_widget') else self

    def width(self):
        return self.tab_content_widget.width() if hasattr(self, 'tab_content_widget') else super().width()

    def height(self):
        return self.tab_content_widget.height() if hasattr(self, 'tab_content_widget') else super().height()
    
    def add_connector(self, connector):
        self.connectors.append(connector)
        self.parent.add_connector(connector)

    def remove_connector(self, connector):
        if connector in self.connectors:
            self.connectors.remove(connector)
            self.parent.remove_connector(connector)

            if hasattr(self, 'connector_manager') and self.connector_manager:
                self.connector_manager.remove_connector(connector)

    def delete_dock(self, dock):
        """Delete a dock and redistribute its space to neighbors using connector information"""
        if dock not in self.docks:
            return

        from UI.hconnector import HConnector
        from UI.vconnector import VConnector

        # Find neighbors using connectors (more reliable than edge detection)
        left_neighbors = []
        right_neighbors = []
        top_neighbors = []
        bottom_neighbors = []

        h_connectors_with_dock = []
        v_connectors_with_dock = []

        for connector in self.connectors:
            if isinstance(connector, HConnector):
                if dock in connector.left_docks:
                    # Dock is on the left, so right_docks are right neighbors
                    right_neighbors.extend(connector.right_docks)
                    h_connectors_with_dock.append(connector)
                elif dock in connector.right_docks:
                    # Dock is on the right, so left_docks are left neighbors
                    left_neighbors.extend(connector.left_docks)
                    h_connectors_with_dock.append(connector)
            elif isinstance(connector, VConnector):
                if dock in connector.top_docks:
                    # Dock is on top, so bottom_docks are bottom neighbors
                    bottom_neighbors.extend(connector.bottom_docks)
                    v_connectors_with_dock.append(connector)
                elif dock in connector.bottom_docks:
                    # Dock is on bottom, so top_docks are top neighbors
                    top_neighbors.extend(connector.top_docks)
                    v_connectors_with_dock.append(connector)

        # Remove duplicates
        left_neighbors = list(set(left_neighbors))
        right_neighbors = list(set(right_neighbors))
        top_neighbors = list(set(top_neighbors))
        bottom_neighbors = list(set(bottom_neighbors))

        # Determine expansion direction (prioritize horizontal)
        expanding_neighbors = None
        expansion_direction = None
        connectors_to_remove = []
        connectors_to_update = []

        if left_neighbors:
            expanding_neighbors = left_neighbors
            expansion_direction = 'left'
            connectors_to_remove = h_connectors_with_dock
            connectors_to_update = v_connectors_with_dock
        elif right_neighbors:
            expanding_neighbors = right_neighbors
            expansion_direction = 'right'
            connectors_to_remove = h_connectors_with_dock
            connectors_to_update = v_connectors_with_dock
        elif top_neighbors:
            expanding_neighbors = top_neighbors
            expansion_direction = 'top'
            connectors_to_remove = v_connectors_with_dock
            connectors_to_update = h_connectors_with_dock
        elif bottom_neighbors:
            expanding_neighbors = bottom_neighbors
            expansion_direction = 'bottom'
            connectors_to_remove = v_connectors_with_dock
            connectors_to_update = h_connectors_with_dock

        # Expand neighbors
        if expanding_neighbors and expansion_direction:
            if expansion_direction == 'left':
                # Left neighbors expand right
                for neighbor in expanding_neighbors:
                    neighbor.w_ratio += dock.w_ratio
                    neighbor.update_geometry()
            elif expansion_direction == 'right':
                # Right neighbors expand left
                for neighbor in expanding_neighbors:
                    neighbor.x_ratio = dock.x_ratio
                    neighbor.w_ratio += dock.w_ratio
                    neighbor.update_geometry()
            elif expansion_direction == 'top':
                # Top neighbors expand down
                for neighbor in expanding_neighbors:
                    neighbor.h_ratio += dock.h_ratio
                    neighbor.update_geometry()
            elif expansion_direction == 'bottom':
                # Bottom neighbors expand up
                for neighbor in expanding_neighbors:
                    neighbor.y_ratio = dock.y_ratio
                    neighbor.h_ratio += dock.h_ratio
                    neighbor.update_geometry()

            # Update connectors to replace dock with expanding neighbors
            # Only update connectors that span the same dimension as the deleted dock
            for connector in connectors_to_update:
                if isinstance(connector, HConnector):
                    # For HConnectors (vertical lines), check if connector spans the full width of the deleted dock
                    # The connector should be at a position within the dock's horizontal range
                    connector_in_dock_range = (dock.x_ratio <= connector.x_ratio <= (dock.x_ratio + dock.w_ratio))

                    if connector_in_dock_range:
                        # Only add neighbors that will span the same width as the deleted dock at this connector
                        matching_neighbors = [n for n in expanding_neighbors
                                             if (n.x_ratio <= connector.x_ratio <= (n.x_ratio + n.w_ratio))]

                        if dock in connector.left_docks:
                            connector.left_docks.remove(dock)
                            connector.left_docks.extend(matching_neighbors)
                        elif dock in connector.right_docks:
                            connector.right_docks.remove(dock)
                            connector.right_docks.extend(matching_neighbors)
                elif isinstance(connector, VConnector):
                    # For VConnectors (horizontal lines), check if connector spans the full height of the deleted dock
                    # The connector should be at a position within the dock's vertical range
                    connector_in_dock_range = (dock.y_ratio <= connector.y_ratio <= (dock.y_ratio + dock.h_ratio))

                    if connector_in_dock_range:
                        # Only add neighbors that will span the same height as the deleted dock at this connector
                        matching_neighbors = [n for n in expanding_neighbors
                                             if (n.y_ratio <= connector.y_ratio <= (n.y_ratio + n.h_ratio))]

                        if dock in connector.top_docks:
                            connector.top_docks.remove(dock)
                            connector.top_docks.extend(matching_neighbors)
                        elif dock in connector.bottom_docks:
                            connector.bottom_docks.remove(dock)
                            connector.bottom_docks.extend(matching_neighbors)

        # Remove connectors on the expansion edge
        for connector in connectors_to_remove:
            connector.hide()
            connector.deleteLater()
            self.remove_connector(connector)

        # Remove the dock
        dock.hide()
        dock.deleteLater()
        self.remove_dock(dock)

        # Update geometry of all remaining docks
        for remaining_dock in self.docks:
            remaining_dock.update_geometry()