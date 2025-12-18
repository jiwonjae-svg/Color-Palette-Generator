"""
Palette Sharing Module
Simple file-based palette sharing with export/import functionality
"""

import json
import os
import datetime
from typing import Any


class PaletteSharingManager:
    """Manage palette export and import for sharing"""

    def export_palette(self, palette_data: dict[str, Any], filename: str) -> str:
        """
        Export a palette to a shareable JSON file.
        
        Args:
            palette_data: Dictionary with 'name', 'colors', 'timestamp'
            filename: Path to write.
        """
        if not filename:
            raise ValueError('filename is required')

        if 'colors' not in palette_data or not isinstance(palette_data['colors'], list):
            raise ValueError('palette_data.colors must be a list')

        export_data = {
            'format_version': '1.0',
            'palette': {
                'name': palette_data.get('name', 'Unnamed Palette'),
                'colors': palette_data['colors'],
                'timestamp': palette_data.get('timestamp', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'author': os.getlogin(),
                'color_count': len(palette_data['colors']),
            },
        }

        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return filename
    
    def import_palette(self, filename: str) -> dict[str, Any]:
        """
        Import a palette from a shareable file.
        
        Returns:
            Dictionary with palette data or None if failed
        """
        if not filename:
            raise ValueError('filename is required')

        with open(filename, 'r', encoding='utf-8') as f:
            import_data = json.load(f)

        if 'palette' not in import_data:
            raise ValueError('Invalid palette file format')

        palette = import_data['palette']
        if 'colors' not in palette or not isinstance(palette['colors'], list):
            raise ValueError('Palette has no valid colors list')

        return {
            'name': palette.get('name', 'Imported Palette'),
            'colors': palette['colors'],
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': f"Imported from {os.path.basename(filename)}",
            'original_author': palette.get('author', 'Unknown'),
        }
    
    def export_multiple_palettes(self, palettes_list: list[dict[str, Any]], filename: str) -> str:
        """
        Export multiple palettes to a single collection file
        
        Args:
            palettes_list: List of palette dictionaries
        """
        if not palettes_list:
            raise ValueError('palettes_list is empty')
        if not filename:
            raise ValueError('filename is required')

        export_data = {
            'format_version': '1.0',
            'collection': {
                'name': 'Palette Collection',
                'author': os.getlogin(),
                'export_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'palette_count': len(palettes_list),
                'palettes': [],
            },
        }

        for palette in palettes_list:
            export_data['collection']['palettes'].append({
                'name': palette.get('name', 'Unnamed'),
                'colors': palette['colors'],
                'timestamp': palette.get('timestamp', ''),
            })

        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return filename
    
    def import_collection(self, filename: str) -> list[dict[str, Any]]:
        """
        Import multiple palettes from a collection file
        
        Returns:
            List of palette dictionaries or None if failed
        """
        if not filename:
            raise ValueError('filename is required')

        with open(filename, 'r', encoding='utf-8') as f:
            import_data = json.load(f)

        if 'collection' not in import_data or 'palettes' not in import_data['collection']:
            raise ValueError('Invalid collection file format')

        palettes = import_data['collection']['palettes']

        result: list[dict[str, Any]] = []
        for palette in palettes:
            if 'colors' in palette and isinstance(palette['colors'], list):
                result.append({
                    'name': palette.get('name', 'Imported Palette'),
                    'colors': palette['colors'],
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                })

        return result
