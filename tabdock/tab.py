from PyQt6.QtWidgets import QWidget
from tabdock.dock import Dock
from tabdock._style_guide import bg, black, border_color

class Tab(QWidget):
    def __init__(self, parent, name, index, *,
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
        super().__init__(parent)
        self.parent = parent

        self.name = name
        self.index = index
        self.docks = []
        self.connectors = []
        self.min_dock_size = getattr(parent, 'min_dock_size', 100)

        # Inherit from parent (TabDock) if not explicitly overridden
        self.dock_bg           = dock_bg           if dock_bg           is not None else getattr(parent, 'dock_bg',           black)
        self.tab_bar_bg        = tab_bar_bg        if tab_bar_bg        is not None else getattr(parent, 'tab_bar_bg',        black)
        self.content_bg        = content_bg        if content_bg        is not None else getattr(parent, 'content_bg',        bg)
        self.dock_border_color = dock_border_color if dock_border_color is not None else getattr(parent, 'dock_border_color', border_color)
        self.border_width      = border_width      if border_width      is not None else getattr(parent, 'border_width',      2)
        self.tab_text_color    = tab_text_color    if tab_text_color    is not None else getattr(parent, 'tab_text_color',    'white')
        self.active_tab_color  = active_tab_color  if active_tab_color  is not None else getattr(parent, 'active_tab_color',  bg)
        self.tab_height        = tab_height        if tab_height        is not None else getattr(parent, 'dock_tab_height',   25)
        self.tab_radius        = tab_radius        if tab_radius        is not None else getattr(parent, 'dock_tab_radius',   5)
        self.tab_padding       = tab_padding       if tab_padding       is not None else getattr(parent, 'dock_tab_padding',  '5px 10px')
        self.tab_spacing       = tab_spacing       if tab_spacing       is not None else getattr(parent, 'dock_tab_spacing',  0)
        self.dock_padding      = dock_padding      if dock_padding      is not None else getattr(parent, 'dock_padding',      2)
        self.panel_bg          = panel_bg          if panel_bg          is not None else getattr(parent, 'panel_bg',          bg)
        self.available_panels  = available_panels  if available_panels  is not None else getattr(parent, 'available_panels',  [])
        self.accent_color      = accent_color      if accent_color      is not None else getattr(parent, 'accent_color',      '#5080c0')

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

        from tabdock.hconnector import HConnector
        from tabdock.vconnector import VConnector

        EPS = 1e-6

        # Find neighbors and connectors referencing this dock
        left_neighbors, right_neighbors, top_neighbors, bottom_neighbors = [], [], [], []
        h_connectors_with_dock, v_connectors_with_dock = [], []

        for connector in self.connectors:
            if isinstance(connector, HConnector):
                if dock in connector.left_docks:
                    right_neighbors.extend(connector.right_docks)
                    h_connectors_with_dock.append(connector)
                elif dock in connector.right_docks:
                    left_neighbors.extend(connector.left_docks)
                    h_connectors_with_dock.append(connector)
            elif isinstance(connector, VConnector):
                if dock in connector.top_docks:
                    bottom_neighbors.extend(connector.bottom_docks)
                    v_connectors_with_dock.append(connector)
                elif dock in connector.bottom_docks:
                    top_neighbors.extend(connector.top_docks)
                    v_connectors_with_dock.append(connector)

        left_neighbors  = list(set(left_neighbors))
        right_neighbors = list(set(right_neighbors))
        top_neighbors   = list(set(top_neighbors))
        bottom_neighbors = list(set(bottom_neighbors))

        def find_valid(direction, candidates, relevant_connectors):
            """Return (neighbors, shared_connectors) where the neighbors are adjacent to
            dock at the correct edge AND collectively span dock's full perpendicular
            dimension (height for left/right; width for top/bottom).
            Handles both single-neighbor and multi-neighbor (split sub-dock) cases."""

            # Filter: neighbor must be at the correct adjacent edge and have a shared connector
            filtered, shared_map = [], {}
            for neighbor in candidates:
                if direction == 'left':
                    shared = next((c for c in relevant_connectors
                                   if dock in c.right_docks and neighbor in c.left_docks), None)
                    at_edge = abs((neighbor.x_ratio + neighbor.w_ratio) - dock.x_ratio) < EPS
                elif direction == 'right':
                    shared = next((c for c in relevant_connectors
                                   if dock in c.left_docks and neighbor in c.right_docks), None)
                    at_edge = abs(neighbor.x_ratio - (dock.x_ratio + dock.w_ratio)) < EPS
                elif direction == 'top':
                    shared = next((c for c in relevant_connectors
                                   if dock in c.bottom_docks and neighbor in c.top_docks), None)
                    at_edge = abs((neighbor.y_ratio + neighbor.h_ratio) - dock.y_ratio) < EPS
                elif direction == 'bottom':
                    shared = next((c for c in relevant_connectors
                                   if dock in c.top_docks and neighbor in c.bottom_docks), None)
                    at_edge = abs(neighbor.y_ratio - (dock.y_ratio + dock.h_ratio)) < EPS
                else:
                    continue
                if shared is not None and at_edge:
                    filtered.append(neighbor)
                    shared_map[id(neighbor)] = shared

            if not filtered:
                return [], []

            # Sort and check full span coverage with no gaps
            if direction in ('left', 'right'):
                ordered = sorted(filtered, key=lambda n: n.y_ratio)
                dock_s, dock_e = dock.y_ratio, dock.y_ratio + dock.h_ratio
                spans = [(n.y_ratio, n.y_ratio + n.h_ratio) for n in ordered]
            else:
                ordered = sorted(filtered, key=lambda n: n.x_ratio)
                dock_s, dock_e = dock.x_ratio, dock.x_ratio + dock.w_ratio
                spans = [(n.x_ratio, n.x_ratio + n.w_ratio) for n in ordered]

            if abs(spans[0][0] - dock_s) > EPS:
                return [], []
            if abs(spans[-1][1] - dock_e) > EPS:
                return [], []
            for i in range(len(spans) - 1):
                if abs(spans[i][1] - spans[i + 1][0]) > EPS:
                    return [], []

            return ordered, [shared_map[id(n)] for n in ordered]

        expansion_direction = None
        actual_expanding = []
        shared_connectors = []  # one shared connector per entry in actual_expanding

        for direction, candidates, relevant in [
            ('left',   left_neighbors,   h_connectors_with_dock),
            ('right',  right_neighbors,  h_connectors_with_dock),
            ('top',    top_neighbors,    v_connectors_with_dock),
            ('bottom', bottom_neighbors, v_connectors_with_dock),
        ]:
            valid, shared_list = find_valid(direction, candidates, relevant)
            if valid:
                expansion_direction = direction
                actual_expanding = valid
                shared_connectors = shared_list
                break

        # Apply geometry expansion to valid neighbors
        for neighbor in actual_expanding:
            if expansion_direction == 'left':
                neighbor.w_ratio += dock.w_ratio
            elif expansion_direction == 'right':
                neighbor.x_ratio = dock.x_ratio
                neighbor.w_ratio += dock.w_ratio
            elif expansion_direction == 'top':
                neighbor.h_ratio += dock.h_ratio
            elif expansion_direction == 'bottom':
                neighbor.y_ratio = dock.y_ratio
                neighbor.h_ratio += dock.h_ratio
            neighbor.update_geometry()

        # --- Shared connector handling ---
        # Each shared connector sits exactly between dock and its expanding neighbor.
        # After expansion the neighbor spans across the connector's position, so:
        #   • Remove dock from its side of the connector.
        #   • If other docks remain on dock's side, the connector still serves them —
        #     also remove the expanding neighbor from the opposite side (it now spans
        #     past the connector).
        #   • If either side becomes empty → queue the connector for removal.
        final_remove = set()
        processed_shared = set()

        for shared, neighbor in zip(shared_connectors, actual_expanding):
            if shared in processed_shared:
                continue
            processed_shared.add(shared)

            if isinstance(shared, HConnector):
                if dock in shared.right_docks:          # direction 'left'
                    shared.right_docks.remove(dock)
                    if shared.right_docks and neighbor in shared.left_docks:
                        shared.left_docks.remove(neighbor)
                elif dock in shared.left_docks:         # direction 'right'
                    shared.left_docks.remove(dock)
                    if shared.left_docks and neighbor in shared.right_docks:
                        shared.right_docks.remove(neighbor)
                if not shared.left_docks or not shared.right_docks:
                    final_remove.add(shared)

            elif isinstance(shared, VConnector):
                if dock in shared.bottom_docks:         # direction 'top'
                    shared.bottom_docks.remove(dock)
                    if shared.bottom_docks and neighbor in shared.top_docks:
                        shared.top_docks.remove(neighbor)
                elif dock in shared.top_docks:          # direction 'bottom'
                    shared.top_docks.remove(dock)
                    if shared.top_docks and neighbor in shared.bottom_docks:
                        shared.bottom_docks.remove(neighbor)
                if not shared.top_docks or not shared.bottom_docks:
                    final_remove.add(shared)

        # --- All other connectors ---
        # Remove dock from every remaining connector; substitute expanding neighbors.
        # Queue any connector whose side goes empty.
        for connector in self.connectors:
            if connector in processed_shared:
                continue
            if isinstance(connector, HConnector):
                if dock in connector.left_docks:
                    connector.left_docks.remove(dock)
                    for n in actual_expanding:
                        if n not in connector.left_docks:
                            connector.left_docks.append(n)
                if dock in connector.right_docks:
                    connector.right_docks.remove(dock)
                    for n in actual_expanding:
                        if n not in connector.right_docks:
                            connector.right_docks.append(n)
                if not connector.left_docks or not connector.right_docks:
                    final_remove.add(connector)
            elif isinstance(connector, VConnector):
                if dock in connector.top_docks:
                    connector.top_docks.remove(dock)
                    for n in actual_expanding:
                        if n not in connector.top_docks:
                            connector.top_docks.append(n)
                if dock in connector.bottom_docks:
                    connector.bottom_docks.remove(dock)
                    for n in actual_expanding:
                        if n not in connector.bottom_docks:
                            connector.bottom_docks.append(n)
                if not connector.top_docks or not connector.bottom_docks:
                    final_remove.add(connector)

        # Remove all empty-sided connectors
        for connector in final_remove:
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