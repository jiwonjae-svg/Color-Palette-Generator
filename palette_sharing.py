"""
Palette Sharing Module
Simple file-based palette sharing with export/import functionality
"""

import json
import os
import datetime
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk


class PaletteSharingManager:
    """Manage palette export and import for sharing"""
    
    def __init__(self, parent):
        self.parent = parent
    
    def export_palette(self, palette_data):
        """
        Export a palette to a shareable JSON file
        
        Args:
            palette_data: Dictionary with 'name', 'colors', 'timestamp'
        """
        try:
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                title='팔레트 내보내기',
                defaultextension='.palette',
                initialfile=f"{palette_data.get('name', 'palette')}.palette",
                filetypes=[
                    ('팔레트 파일', '*.palette'),
                    ('JSON 파일', '*.json'),
                    ('모든 파일', '*.*')
                ]
            )
            
            if not filename:
                return None
            
            # Prepare export data
            export_data = {
                'format_version': '1.0',
                'palette': {
                    'name': palette_data.get('name', 'Unnamed Palette'),
                    'colors': palette_data['colors'],
                    'timestamp': palette_data.get('timestamp', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'author': os.getlogin(),
                    'color_count': len(palette_data['colors'])
                }
            }
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return filename
        
        except Exception as e:
            messagebox.showerror('내보내기 오류', f'팔레트 내보내기 실패:\n{str(e)}')
            return None
    
    def import_palette(self):
        """
        Import a palette from a shareable file
        
        Returns:
            Dictionary with palette data or None if failed
        """
        try:
            # Ask for file to import
            filename = filedialog.askopenfilename(
                title='팔레트 가져오기',
                filetypes=[
                    ('팔레트 파일', '*.palette'),
                    ('JSON 파일', '*.json'),
                    ('모든 파일', '*.*')
                ]
            )
            
            if not filename:
                return None
            
            # Load file
            with open(filename, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate format
            if 'palette' not in import_data:
                raise ValueError('유효하지 않은 팔레트 파일 형식입니다.')
            
            palette = import_data['palette']
            
            # Validate required fields
            if 'colors' not in palette or not isinstance(palette['colors'], list):
                raise ValueError('팔레트 색상 정보가 없습니다.')
            
            # Return palette data
            result = {
                'name': palette.get('name', 'Imported Palette'),
                'colors': palette['colors'],
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': f"Imported from {os.path.basename(filename)}",
                'original_author': palette.get('author', 'Unknown')
            }
            
            return result
        
        except json.JSONDecodeError:
            messagebox.showerror('가져오기 오류', '파일 형식이 올바르지 않습니다.\nJSON 파일이어야 합니다.')
            return None
        except Exception as e:
            messagebox.showerror('가져오기 오류', f'팔레트 가져오기 실패:\n{str(e)}')
            return None
    
    def export_multiple_palettes(self, palettes_list):
        """
        Export multiple palettes to a single collection file
        
        Args:
            palettes_list: List of palette dictionaries
        """
        try:
            if not palettes_list:
                messagebox.showwarning('경고', '내보낼 팔레트가 없습니다.')
                return None
            
            filename = filedialog.asksaveasfilename(
                title='팔레트 컬렉션 내보내기',
                defaultextension='.palettes',
                initialfile='palette_collection.palettes',
                filetypes=[
                    ('팔레트 컬렉션', '*.palettes'),
                    ('JSON 파일', '*.json'),
                    ('모든 파일', '*.*')
                ]
            )
            
            if not filename:
                return None
            
            # Prepare export data
            export_data = {
                'format_version': '1.0',
                'collection': {
                    'name': 'Palette Collection',
                    'author': os.getlogin(),
                    'export_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'palette_count': len(palettes_list),
                    'palettes': []
                }
            }
            
            for palette in palettes_list:
                export_data['collection']['palettes'].append({
                    'name': palette.get('name', 'Unnamed'),
                    'colors': palette['colors'],
                    'timestamp': palette.get('timestamp', '')
                })
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return filename
        
        except Exception as e:
            messagebox.showerror('내보내기 오류', f'컬렉션 내보내기 실패:\n{str(e)}')
            return None
    
    def import_collection(self):
        """
        Import multiple palettes from a collection file
        
        Returns:
            List of palette dictionaries or None if failed
        """
        try:
            filename = filedialog.askopenfilename(
                title='팔레트 컬렉션 가져오기',
                filetypes=[
                    ('팔레트 컬렉션', '*.palettes'),
                    ('JSON 파일', '*.json'),
                    ('모든 파일', '*.*')
                ]
            )
            
            if not filename:
                return None
            
            # Load file
            with open(filename, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate format
            if 'collection' not in import_data or 'palettes' not in import_data['collection']:
                raise ValueError('유효하지 않은 컬렉션 파일 형식입니다.')
            
            palettes = import_data['collection']['palettes']
            
            # Convert to internal format
            result = []
            for palette in palettes:
                if 'colors' in palette and isinstance(palette['colors'], list):
                    result.append({
                        'name': palette.get('name', 'Imported Palette'),
                        'colors': palette['colors'],
                        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return result
        
        except json.JSONDecodeError:
            messagebox.showerror('가져오기 오류', '파일 형식이 올바르지 않습니다.')
            return None
        except Exception as e:
            messagebox.showerror('가져오기 오류', f'컬렉션 가져오기 실패:\n{str(e)}')
            return None
