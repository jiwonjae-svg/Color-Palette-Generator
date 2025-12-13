"""
Image Recoloring Module
Applies palette colors to images based on brightness values
"""

from PIL import Image, ImageTk
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
    
    def apply_palette_to_image(self, image_path, palette_hex_colors):
        """
        Apply palette colors to image based on brightness zones
        
        Args:
            image_path: Path to the image file
            palette_hex_colors: List of hex color strings (e.g., ['#FF0000', '#00FF00', ...])
        
        Returns:
            PIL Image with palette applied
        """
        # Load image
        img = Image.open(image_path)
        img = img.convert('RGB')
        img_array = np.array(img)
        
        # Convert to grayscale (value/brightness)
        gray = np.array(img.convert('L'))
        
        # Sort palette by brightness
        sorted_palette = self.sort_palette_by_brightness(palette_hex_colors)
        num_colors = len(sorted_palette)
        
        # Calculate brightness thresholds
        min_val = gray.min()
        max_val = gray.max()
        
        # Create zones based on number of palette colors
        thresholds = np.linspace(min_val, max_val, num_colors + 1)
        
        # Create result image
        result = np.zeros_like(img_array)
        
        # Apply palette colors to each brightness zone
        for i in range(num_colors):
            # Create mask for current brightness zone
            if i == num_colors - 1:
                # Last zone includes max value
                mask = (gray >= thresholds[i]) & (gray <= thresholds[i + 1])
            else:
                mask = (gray >= thresholds[i]) & (gray < thresholds[i + 1])
            
            # Get corresponding palette color (brightest to darkest)
            palette_rgb = self.hex_to_rgb(sorted_palette[i])
            
            # Apply color to masked region
            result[mask] = palette_rgb
        
        # Convert back to PIL Image
        result_img = Image.fromarray(result.astype('uint8'), 'RGB')
        return result_img
    
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
        recolored = self.apply_palette_to_image(image_path, palette_hex_colors)
        
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
