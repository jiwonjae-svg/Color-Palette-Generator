"""Color adjustment utilities (no UI).

All Tkinter UI for color adjustment dialogs lives in main.py.
"""

from __future__ import annotations

RGB = tuple[int, int, int]


def apply_warmth(rgb: RGB, warmth: float) -> RGB:
    """Apply warmth/coolness to a color.

    warmth > 0 shifts toward red/yellow, warmth < 0 shifts toward blue.
    """
    r, g, b = rgb
    if warmth > 0:
        r = min(255, int(r + warmth * 2))
        g = min(255, int(g + warmth * 0.5))
        b = max(0, int(b - warmth * 0.5))
    else:
        r = max(0, int(r + warmth * 0.5))
        g = max(0, int(g + warmth * 0.5))
        b = min(255, int(b - warmth * 2))
    return (r, g, b)


def apply_contrast(rgb: RGB, contrast: float) -> RGB:
    """Apply contrast adjustment around mid-gray (128)."""
    r, g, b = rgb
    r = int(128 + (r - 128) * (1 + contrast))
    g = int(128 + (g - 128) * (1 + contrast))
    b = int(128 + (b - 128) * (1 + contrast))
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return (r, g, b)
