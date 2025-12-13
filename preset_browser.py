"""
Preset Palette Browser
사전 정의 팔레트 검색 및 선택 UI
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from preset_generator import PresetPaletteGenerator
import os


class PresetPaletteBrowser:
    """사전 정의 팔레트 브라우저"""
    
    def __init__(self, parent, callback):
        """
        Args:
            parent: Parent window
            callback: Function to call with selected palette colors
        """
        self.callback = callback
        self.all_palettes = []
        self.filtered_palettes = []
        self.current_tag_filter = 'All'
        self.color_search_filter = None
        
        # Load palettes
        self.load_palettes()
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("사전 정의 팔레트")
        self.dialog.geometry("680x600")
        self.dialog.transient(parent)
        
        self.create_widgets()
        self.update_palette_list()
    
    def load_palettes(self):
        """Load palettes from file"""
        try:
            palette_file = os.path.join(os.path.dirname(__file__), 'preset_palettes.dat')
            if os.path.exists(palette_file):
                self.all_palettes = PresetPaletteGenerator.load_palettes(palette_file)
            else:
                messagebox.showerror('오류', '사전 정의 팔레트 파일을 찾을 수 없습니다.')
                self.all_palettes = []
        except Exception as e:
            messagebox.showerror('오류', f'팔레트 로드 실패: {str(e)}')
            self.all_palettes = []
    
    def create_widgets(self):
        """Create UI widgets"""
        # Top toolbar
        toolbar = ttk.Frame(self.dialog)
        toolbar.pack(fill='x', padx=10, pady=10)
        
        # Tag filter
        ttk.Label(toolbar, text="필터:").pack(side='left', padx=5)
        
        self.tag_var = tk.StringVar(value='All')
        tags = self.get_all_tags()
        tag_combo = ttk.Combobox(toolbar, textvariable=self.tag_var, values=tags, width=20, state='readonly')
        tag_combo.pack(side='left', padx=5)
        tag_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_by_tag())
        
        # Search by color button
        btn_color_search = ttk.Button(toolbar, text="색상으로 검색", command=self.search_by_color)
        btn_color_search.pack(side='left', padx=10)
        
        # Clear filter button
        btn_clear = ttk.Button(toolbar, text="필터 초기화", command=self.clear_filters)
        btn_clear.pack(side='left', padx=5)
        
        # Info label
        self.info_label = ttk.Label(toolbar, text=f"총 {len(self.all_palettes)}개 팔레트")
        self.info_label.pack(side='right', padx=5)
        
        # Main content area with scrollbar
        content_frame = ttk.Frame(self.dialog)
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(content_frame, bg='white')
        scrollbar = ttk.Scrollbar(content_frame, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            '<Configure>',
            lambda e: self._update_scroll_region()
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw', width=640)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind mousewheel only to this canvas (not bind_all)
        self.canvas.bind('<Enter>', lambda e: self.canvas.bind_all('<MouseWheel>', self._on_mousewheel))
        self.canvas.bind('<Leave>', lambda e: self.canvas.unbind_all('<MouseWheel>'))
        
        # Button bar
        btn_bar = ttk.Frame(self.dialog)
        btn_bar.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(btn_bar, text="닫기", command=self.dialog.destroy).pack(side='right', padx=5)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _update_scroll_region(self):
        """Update scroll region to match content size"""
        self.canvas.update_idletasks()
        
        # Get actual content height
        self.scrollable_frame.update_idletasks()
        content_height = self.scrollable_frame.winfo_reqheight()
        canvas_height = self.canvas.winfo_height()
        
        # Only set scroll region if content exceeds canvas height
        if content_height > canvas_height:
            # Content is larger than canvas - enable scrolling
            self.canvas.configure(scrollregion=(0, 0, 640, content_height))
        else:
            # Content fits in canvas - disable scrolling
            self.canvas.configure(scrollregion=(0, 0, 640, canvas_height))
    
    def get_all_tags(self):
        """Get all unique tags from palettes"""
        tags = set(['All'])
        for palette in self.all_palettes:
            tags.update(palette.get('tags', []))
        return sorted(list(tags))
    
    def filter_by_tag(self):
        """Filter palettes by selected tag"""
        tag = self.tag_var.get()
        self.current_tag_filter = tag
        self.update_palette_list()
    
    def search_by_color(self):
        """Search palettes by color picker"""
        color = colorchooser.askcolor(title="검색할 색상 선택")
        if color and color[0]:
            self.color_search_filter = color[0]  # RGB tuple
            self.update_palette_list()
    
    def clear_filters(self):
        """Clear all filters"""
        self.tag_var.set('All')
        self.current_tag_filter = 'All'
        self.color_search_filter = None
        self.update_palette_list()
    
    def color_similarity(self, rgb1, rgb2):
        """Calculate color similarity (0-100, higher is more similar)"""
        r1, g1, b1 = rgb1
        r2, g2, b2 = rgb2
        # Euclidean distance in RGB space
        distance = ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5
        max_distance = (255**2 * 3) ** 0.5
        similarity = (1 - distance / max_distance) * 100
        return similarity
    
    def hex_to_rgb(self, hex_color):
        """Convert HEX to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def update_palette_list(self):
        """Update the displayed palette list"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Filter palettes
        self.filtered_palettes = []
        for palette in self.all_palettes:
            # Tag filter
            if self.current_tag_filter != 'All':
                if self.current_tag_filter not in palette.get('tags', []):
                    continue
            
            # Color search filter (±5% similarity)
            if self.color_search_filter:
                found_similar = False
                for hex_color in palette['colors']:
                    rgb = self.hex_to_rgb(hex_color)
                    similarity = self.color_similarity(self.color_search_filter, rgb)
                    if similarity >= 95:  # 5% tolerance
                        found_similar = True
                        break
                if not found_similar:
                    continue
            
            self.filtered_palettes.append(palette)
        
        # Update info label
        filter_info = f"{len(self.filtered_palettes)} / {len(self.all_palettes)} 팔레트"
        if self.current_tag_filter != 'All':
            filter_info += f" (태그: {self.current_tag_filter})"
        if self.color_search_filter:
            filter_info += f" (색상 검색)"
        self.info_label.config(text=filter_info)
        
        # Display palettes
        for palette in self.filtered_palettes[:100]:  # Limit to 100 for performance
            self.create_palette_widget(palette)
    
    def create_palette_widget(self, palette):
        """Create a widget for a single palette"""
        frame = ttk.Frame(self.scrollable_frame, relief='solid', borderwidth=1)
        frame.pack(fill='x', padx=5, pady=3)
        
        # Header
        header = ttk.Frame(frame)
        header.pack(fill='x', padx=5, pady=3)
        
        ttk.Label(header, text=palette['name'], font=('Segoe UI', 9, 'bold')).pack(side='left')
        
        # Tags
        tags_text = ', '.join(palette.get('tags', []))
        ttk.Label(header, text=f"({tags_text})", font=('Arial', 7), foreground='gray').pack(side='left', padx=5)
        
        # Use button
        btn_use = ttk.Button(header, text="사용", command=lambda p=palette: self.use_palette(p))
        btn_use.pack(side='right')
        
        # Color swatches with fixed width
        colors_frame = tk.Frame(frame, height=40)
        colors_frame.pack(fill='x', padx=5, pady=3)
        colors_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        for i, color in enumerate(palette['colors']):
            swatch = tk.Canvas(colors_frame, width=110, height=35, bg=color, highlightthickness=1, highlightbackground='gray')
            swatch.pack(side='left', padx=2)
            
            # Show color on hover
            def show_color(event, c=color):
                event.widget.config(highlightbackground='black', highlightthickness=2)
            
            def hide_color(event):
                event.widget.config(highlightbackground='gray', highlightthickness=1)
            
            swatch.bind('<Enter>', show_color)
            swatch.bind('<Leave>', hide_color)
            
            # Add color text
            swatch.create_text(55, 17, text=color, fill='white' if self.is_dark(color) else 'black', font=('Arial', 8))
    
    def is_dark(self, hex_color):
        """Check if color is dark"""
        rgb = self.hex_to_rgb(hex_color)
        luminance = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
        return luminance < 128
    
    def use_palette(self, palette):
        """Use selected palette"""
        if self.callback:
            self.callback(palette['colors'], palette['name'])
        self.dialog.destroy()
