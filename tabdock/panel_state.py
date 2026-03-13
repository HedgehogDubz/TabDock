class PanelStateManager:
    """
    Per-panel-class shared observable state.

    One instance exists per Panel subclass (keyed by class name).
    State is a plain dict; subscribers are called whenever a key changes.

    Usage inside a Panel subclass:
        self.state.get("my_key", default)
        self.state.set("my_key", value)
        self.state.subscribe("my_key", callback)   # fires immediately if key exists
    """

    _registry: dict[str, "PanelStateManager"] = {}

    @classmethod
    def for_class(cls, panel_class) -> "PanelStateManager":
        key = panel_class.__name__
        if key not in cls._registry:
            cls._registry[key] = cls()
        return cls._registry[key]

    def __init__(self):
        self._state: dict = {}
        self._listeners: dict[str, list] = {}

    def has(self, key) -> bool:
        return key in self._state

    def get(self, key, default=None):
        return self._state.get(key, default)

    def set(self, key, value):
        self._state[key] = value
        for cb in list(self._listeners.get(key, [])):
            cb(value)

    def subscribe(self, key, callback, init: bool = True):
        """Register a callback for key. If init=True and key already has a value, fires now."""
        self._listeners.setdefault(key, []).append(callback)
        if init and key in self._state:
            callback(self._state[key])

    def unsubscribe(self, key, callback):
        if key in self._listeners:
            try:
                self._listeners[key].remove(callback)
            except ValueError:
                pass
