bg = "#353535"
black = "#000000"
border_color = "#000000"  # Visible gray border


def lighten(hex_color: str, amount: float = 0.25) -> str:
    """Return a lighter version of a hex color. amount=0.0 is unchanged, 1.0 is white."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"