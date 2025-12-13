"""
색상 조정 도구 모듈
밝기, 채도, 색조, 온도, 대비 조절 UI 제공
"""

import tkinter as tk
from tkinter import ttk

class ColorAdjusterDialog:
    def __init__(self, parent, generator, palette_colors, callback):
        """
        Color adjuster dialog
        
        Args:
            parent: Parent window
            generator: ColorPaletteGenerator instance
            palette_colors: List of RGB tuples to adjust
            callback: Function to call with adjusted colors
        """
        self.generator = generator
        self.original_colors = palette_colors.copy()
        self.current_colors = palette_colors.copy()
        self.callback = callback
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("색상 조정")
        self.dialog.geometry("450x420")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Preview frame
        preview_frame = ttk.LabelFrame(self.dialog, text="미리보기", padding=10)
        preview_frame.pack(fill='x', padx=10, pady=10)
        
        self.preview_canvas = tk.Canvas(preview_frame, height=60, bg='white')
        self.preview_canvas.pack(fill='x')
        
        # Control frame
        control_frame = ttk.Frame(self.dialog, padding=10)
        control_frame.pack(fill='both', expand=True, padx=10)
        
        # Brightness slider
        ttk.Label(control_frame, text="밝기:").grid(row=0, column=0, sticky='w', pady=5)
        self.brightness_var = tk.DoubleVar(value=0)
        brightness_slider = ttk.Scale(control_frame, from_=-0.5, to=0.5, 
                                     variable=self.brightness_var, 
                                     orient='horizontal',
                                     command=lambda v: self.update_preview())
        brightness_slider.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Saturation slider
        ttk.Label(control_frame, text="채도:").grid(row=1, column=0, sticky='w', pady=5)
        self.saturation_var = tk.DoubleVar(value=0)
        saturation_slider = ttk.Scale(control_frame, from_=-0.5, to=0.5,
                                     variable=self.saturation_var,
                                     orient='horizontal',
                                     command=lambda v: self.update_preview())
        saturation_slider.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Hue slider
        ttk.Label(control_frame, text="색조:").grid(row=2, column=0, sticky='w', pady=5)
        self.hue_var = tk.DoubleVar(value=0)
        hue_slider = ttk.Scale(control_frame, from_=-180, to=180,
                              variable=self.hue_var,
                              orient='horizontal',
                              command=lambda v: self.update_preview())
        hue_slider.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        # Warmth/Temperature slider
        ttk.Label(control_frame, text="색온도:").grid(row=3, column=0, sticky='w', pady=5)
        self.warmth_var = tk.DoubleVar(value=0)
        warmth_slider = ttk.Scale(control_frame, from_=-30, to=30,
                                 variable=self.warmth_var,
                                 orient='horizontal',
                                 command=lambda v: self.update_preview())
        warmth_slider.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        ttk.Label(control_frame, text="(Cool ← → Warm)", font=('Arial', 8)).grid(row=3, column=2, sticky='w')
        
        # Contrast slider (brightness range adjustment)
        ttk.Label(control_frame, text="대비:").grid(row=4, column=0, sticky='w', pady=5)
        self.contrast_var = tk.DoubleVar(value=0)
        contrast_slider = ttk.Scale(control_frame, from_=-0.3, to=0.3,
                                   variable=self.contrast_var,
                                   orient='horizontal',
                                   command=lambda v: self.update_preview())
        contrast_slider.grid(row=4, column=1, sticky='ew', padx=5, pady=5)
        
        control_frame.columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="초기화", command=self.reset).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="적용", command=self.apply).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="취소", command=self.dialog.destroy).pack(side='left', padx=5)
        
        # Initial preview
        self.update_preview()
    
    def update_preview(self):
        """Update color preview with current adjustments."""
        brightness = self.brightness_var.get()
        saturation = self.saturation_var.get()
        hue = self.hue_var.get()
        warmth = self.warmth_var.get()
        contrast = self.contrast_var.get()
        
        # Apply adjustments
        self.current_colors = []
        for rgb in self.original_colors:
            # Apply hue
            adjusted = self.generator.adjust_hue(rgb, hue)
            # Apply warmth (shift towards red/orange or blue)
            if warmth != 0:
                adjusted = self.apply_warmth(adjusted, warmth)
            # Apply saturation
            adjusted = self.generator.adjust_saturation(adjusted, saturation)
            # Apply brightness
            adjusted = self.generator.adjust_brightness(adjusted, brightness)
            # Apply contrast
            if contrast != 0:
                adjusted = self.apply_contrast(adjusted, contrast)
            self.current_colors.append(adjusted)
        
        # Draw preview
        self.preview_canvas.delete('all')
        width = self.preview_canvas.winfo_width()
        if width < 10:
            width = 380
        
        if self.current_colors:
            box_width = width / len(self.current_colors)
            for i, rgb in enumerate(self.current_colors):
                x0 = i * box_width
                x1 = (i + 1) * box_width
                hex_color = self.generator.rgb_to_hex(rgb)
                self.preview_canvas.create_rectangle(x0, 0, x1, 60, fill=hex_color, outline='')
    
    def apply_warmth(self, rgb, warmth):
        """Apply warmth/coolness to color."""
        r, g, b = rgb
        # Positive warmth: increase red/yellow, negative: increase blue
        if warmth > 0:
            # Warm: shift towards red/orange
            r = min(255, int(r + warmth * 2))
            g = min(255, int(g + warmth * 0.5))
            b = max(0, int(b - warmth * 0.5))
        else:
            # Cool: shift towards blue
            r = max(0, int(r + warmth * 0.5))
            g = max(0, int(g + warmth * 0.5))
            b = min(255, int(b - warmth * 2))
        return (r, g, b)
    
    def apply_contrast(self, rgb, contrast):
        """Apply contrast adjustment."""
        # Contrast: expand or compress distance from mid-gray (128)
        r, g, b = rgb
        r = int(128 + (r - 128) * (1 + contrast))
        g = int(128 + (g - 128) * (1 + contrast))
        b = int(128 + (b - 128) * (1 + contrast))
        # Clamp values
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        return (r, g, b)
    
    def reset(self):
        """Reset all adjustments."""
        self.brightness_var.set(0)
        self.saturation_var.set(0)
        self.hue_var.set(0)
        self.warmth_var.set(0)
        self.contrast_var.set(0)
        self.update_preview()
    
    def apply(self):
        """Apply adjustments and close dialog."""
        self.callback(self.current_colors)
        self.dialog.destroy()
