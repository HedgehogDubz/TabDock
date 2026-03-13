"""
qt-themes compatibility helper.

Usage:
    import qt_themes
    from tabdock.qt_themes_compat import apply_theme

    app = QApplication(sys.argv)
    kwargs = apply_theme('nord')          # sets QPalette + returns TabDock color kwargs
    TD = TabDock(..., **kwargs)

    # Or apply later (before TabDock is created):
    kwargs = apply_theme('catppuccin_mocha')
    TD = TabDock(..., **kwargs)
"""


def apply_theme(theme_name: str) -> dict:
    """
    Apply a qt-themes theme to the QApplication (via QPalette) and return
    a dict of color keyword arguments suitable for passing to TabDock.

    Raises ImportError if qt-themes is not installed.
    Raises ValueError if the theme name is not recognised.
    """
    try:
        import os
        os.environ.setdefault("QT_API", "pyqt6")
        import qt_themes
    except ImportError:
        print(f"[qt_themes_compat] qt-themes not found — running without theme.")
        return {}

    qt_themes.set_theme(theme_name)
    theme = qt_themes.get_theme(theme_name)

    if theme is None:
        raise ValueError(
            f"Unknown theme '{theme_name}'. "
            f"Available: {list(qt_themes.get_themes().keys())}"
        )

    def hex(color) -> str:
        return color.name()          # QColor.name() → '#rrggbb'

    return dict(
        # TabDock chooser bar
        tab_bar_bg        = hex(theme.crust),      # darkest strip at the very top
        content_bg        = hex(theme.base),        # content area behind docks
        tab_text_color    = hex(theme.text),
        active_tab_color  = hex(theme.base),
        accent_color      = hex(theme.primary),

        # Dock internals (cascade: TabDock → Tab → Dock → Panel)
        dock_bg           = hex(theme.crust),       # matches chrome so no visible border
        dock_border_color = hex(theme.crust),       # invisible — blends with background
        panel_bg          = hex(theme.base),        # panel content background
    )


def get_available_themes() -> list:
    """Return a sorted list of available theme name strings."""
    try:
        import qt_themes
        return sorted(qt_themes.get_themes().keys())
    except ImportError:
        return []
