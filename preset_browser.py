"""Preset palette domain logic (no UI).

UI is handled in main.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from preset_generator import PresetPaletteGenerator


@dataclass(frozen=True)
class PresetFilter:
    tag: str | None = None
    color_rgb: tuple[int, int, int] | None = None
    min_similarity: float = 95.0


class PresetPaletteService:
    """Load and filter preset palettes without any GUI dependencies."""

    def __init__(self, file_handler, data_filename: str = 'preset_palettes.dat'):
        self.file_handler = file_handler
        self.data_filename = data_filename

    def load_palettes(self):
        return PresetPaletteGenerator.load_palettes(self.file_handler, self.data_filename)

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def color_similarity(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
        r1, g1, b1 = rgb1
        r2, g2, b2 = rgb2
        distance = ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
        max_distance = (255 ** 2 * 3) ** 0.5
        return (1 - distance / max_distance) * 100

    @classmethod
    def filter_palettes(cls, palettes: list[dict], preset_filter: PresetFilter) -> list[dict]:
        filtered: list[dict] = []
        for palette in palettes:
            if preset_filter.tag:
                if preset_filter.tag not in palette.get('tags', []):
                    continue

            if preset_filter.color_rgb:
                found_similar = False
                for hex_color in palette.get('colors', []):
                    rgb = cls.hex_to_rgb(hex_color)
                    if cls.color_similarity(preset_filter.color_rgb, rgb) >= preset_filter.min_similarity:
                        found_similar = True
                        break
                if not found_similar:
                    continue

            filtered.append(palette)
        return filtered
