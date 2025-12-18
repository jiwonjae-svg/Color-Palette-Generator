"""
Image Recoloring Module
Applies palette colors to images based on brightness values
"""

from PIL import Image, ImageTk, ImageFilter
import numpy as np


class ImageRecolorer:
    """Apply palette colors to images based on brightness zones"""
    
    def __init__(self):
        pass
    
    def hex_to_rgb(self, hex_color):
        """Convert HEX to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(self, rgb):
        """Convert RGB tuple to HEX"""
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
    
    def get_brightness(self, rgb):
        """Calculate brightness value (0-255) from RGB"""
        # Using perceived brightness formula
        r, g, b = rgb
        return 0.299 * r + 0.587 * g + 0.114 * b
    
    def sort_palette_by_brightness(self, palette_hex_colors):
        """Sort palette colors from brightest to darkest"""
        color_brightness = []
        for hex_color in palette_hex_colors:
            rgb = self.hex_to_rgb(hex_color)
            brightness = self.get_brightness(rgb)
            color_brightness.append((hex_color, brightness))
        
        # Sort by brightness (descending - brightest first)
        color_brightness.sort(key=lambda x: x[1], reverse=True)
        return [color for color, _ in color_brightness]
    
    def apply_palette_to_pil_image(self, img: Image.Image, palette_hex_colors, blur_radius: float = 0.6) -> Image.Image:
        """Apply palette colors to an in-memory PIL image.

        This is used for fast previews (apply to a downscaled image) and for full-size processing.
        """
        alpha = None
        if img.mode in ('RGBA', 'LA'):
            alpha = img.getchannel('A')
        rgb_img = img.convert('RGB')

        gray = np.array(rgb_img.convert('L'))

        sorted_palette = self.sort_palette_by_brightness(palette_hex_colors)
        num_colors = len(sorted_palette)
        if num_colors <= 0:
            return img.copy()

        min_val = gray.min()
        max_val = gray.max()

        denom = float(max_val - min_val) if max_val != min_val else 1.0
        zone_idx = np.floor(((gray.astype(np.float32) - float(min_val)) / denom) * num_colors).astype(np.int32)
        zone_idx = np.clip(zone_idx, 0, num_colors - 1)

        zone_palette = [self.hex_to_rgb(sorted_palette[num_colors - 1 - i]) for i in range(num_colors)]
        zone_palette = np.array(zone_palette, dtype=np.uint8)

        result = zone_palette[zone_idx]
        result_img = Image.fromarray(result.astype('uint8'), 'RGB')

        try:
            if blur_radius and float(blur_radius) > 0:
                result_img = result_img.filter(ImageFilter.GaussianBlur(radius=float(blur_radius)))
        except Exception:
            pass

        if alpha is not None:
            try:
                result_img.putalpha(alpha)
            except Exception:
                pass
        return result_img

    def apply_palette_to_image(self, image_path, palette_hex_colors, blur_radius: float = 0.6):
        """
        Apply palette colors to image based on brightness zones
        
        Args:
            image_path: Path to the image file
            palette_hex_colors: List of hex color strings (e.g., ['#FF0000', '#00FF00', ...])
        
        Returns:
            PIL Image with palette applied
        """
        img = Image.open(image_path)
        return self.apply_palette_to_pil_image(img, palette_hex_colors, blur_radius=blur_radius)
    
    def preview_recolored_image(self, image_path, palette_hex_colors, max_size=(800, 600)):
        """
        Create a preview of recolored image
        
        Args:
            image_path: Path to the image file
            palette_hex_colors: List of hex colors
            max_size: Maximum preview size (width, height)
        
        Returns:
            PhotoImage for Tkinter display
        """
        img = Image.open(image_path)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        recolored = self.apply_palette_to_pil_image(img, palette_hex_colors)
        
        # Resize for preview if needed
        recolored.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        return ImageTk.PhotoImage(recolored)
    
    def save_recolored_image(self, image_path, palette_hex_colors, output_path):
        """
        Save recolored image to file
        
        Args:
            image_path: Path to input image
            palette_hex_colors: List of hex colors
            output_path: Path to save output image
        """
        recolored = self.apply_palette_to_image(image_path, palette_hex_colors)
        recolored.save(output_path)
        return output_path
