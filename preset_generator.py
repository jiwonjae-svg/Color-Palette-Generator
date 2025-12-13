"""
Preset Palette Generator
사전 정의 팔레트 생성 및 관리 모듈
"""

import json
import gzip
import base64
from cryptography.fernet import Fernet
import os
import random

# Embedded encryption key (keep this secure - do not share)
EMBEDDED_ENCRYPTION_KEY = b'55EDKL_A1eUzicBsX0mr0u7hIZI44eHiF5KrArRC8YA='


class PresetPaletteGenerator:
    """사전 정의 팔레트 생성기"""
    
    # Color schemes from popular design systems
    MATERIAL_DESIGN_COLORS = {
        'Red': ['#FFEBEE', '#FFCDD2', '#EF9A9A', '#E57373', '#EF5350', '#F44336', '#E53935', '#D32F2F', '#C62828', '#B71C1C'],
        'Pink': ['#FCE4EC', '#F8BBD0', '#F48FB1', '#F06292', '#EC407A', '#E91E63', '#D81B60', '#C2185B', '#AD1457', '#880E4F'],
        'Purple': ['#F3E5F5', '#E1BEE7', '#CE93D8', '#BA68C8', '#AB47BC', '#9C27B0', '#8E24AA', '#7B1FA2', '#6A1B9A', '#4A148C'],
        'Deep Purple': ['#EDE7F6', '#D1C4E9', '#B39DDB', '#9575CD', '#7E57C2', '#673AB7', '#5E35B1', '#512DA8', '#4527A0', '#311B92'],
        'Indigo': ['#E8EAF6', '#C5CAE9', '#9FA8DA', '#7986CB', '#5C6BC0', '#3F51B5', '#3949AB', '#303F9F', '#283593', '#1A237E'],
        'Blue': ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5', '#2196F3', '#1E88E5', '#1976D2', '#1565C0', '#0D47A1'],
        'Light Blue': ['#E1F5FE', '#B3E5FC', '#81D4FA', '#4FC3F7', '#29B6F6', '#03A9F4', '#039BE5', '#0288D1', '#0277BD', '#01579B'],
        'Cyan': ['#E0F7FA', '#B2EBF2', '#80DEEA', '#4DD0E1', '#26C6DA', '#00BCD4', '#00ACC1', '#0097A7', '#00838F', '#006064'],
        'Teal': ['#E0F2F1', '#B2DFDB', '#80CBC4', '#4DB6AC', '#26A69A', '#009688', '#00897B', '#00796B', '#00695C', '#004D40'],
        'Green': ['#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784', '#66BB6A', '#4CAF50', '#43A047', '#388E3C', '#2E7D32', '#1B5E20'],
        'Light Green': ['#F1F8E9', '#DCEDC8', '#C5E1A5', '#AED581', '#9CCC65', '#8BC34A', '#7CB342', '#689F38', '#558B2F', '#33691E'],
        'Lime': ['#F9FBE7', '#F0F4C3', '#E6EE9C', '#DCE775', '#D4E157', '#CDDC39', '#C0CA33', '#AFB42B', '#9E9D24', '#827717'],
        'Yellow': ['#FFFDE7', '#FFF9C4', '#FFF59D', '#FFF176', '#FFEE58', '#FFEB3B', '#FDD835', '#FBC02D', '#F9A825', '#F57F17'],
        'Amber': ['#FFF8E1', '#FFECB3', '#FFE082', '#FFD54F', '#FFCA28', '#FFC107', '#FFB300', '#FFA000', '#FF8F00', '#FF6F00'],
        'Orange': ['#FFF3E0', '#FFE0B2', '#FFCC80', '#FFB74D', '#FFA726', '#FF9800', '#FB8C00', '#F57C00', '#EF6C00', '#E65100'],
        'Deep Orange': ['#FBE9E7', '#FFCCBC', '#FFAB91', '#FF8A65', '#FF7043', '#FF5722', '#F4511E', '#E64A19', '#D84315', '#BF360C'],
        'Brown': ['#EFEBE9', '#D7CCC8', '#BCAAA4', '#A1887F', '#8D6E63', '#795548', '#6D4C41', '#5D4037', '#4E342E', '#3E2723'],
        'Grey': ['#FAFAFA', '#F5F5F5', '#EEEEEE', '#E0E0E0', '#BDBDBD', '#9E9E9E', '#757575', '#616161', '#424242', '#212121'],
        'Blue Grey': ['#ECEFF1', '#CFD8DC', '#B0BEC5', '#90A4AE', '#78909C', '#607D8B', '#546E7A', '#455A64', '#37474F', '#263238']
    }
    
    FLAT_UI_COLORS = {
        'Turquoise': '#1ABC9C',
        'Green Sea': '#16A085',
        'Emerald': '#2ECC71',
        'Nephritis': '#27AE60',
        'Peter River': '#3498DB',
        'Belize Hole': '#2980B9',
        'Amethyst': '#9B59B6',
        'Wisteria': '#8E44AD',
        'Wet Asphalt': '#34495E',
        'Midnight Blue': '#2C3E50',
        'Sun Flower': '#F1C40F',
        'Orange': '#F39C12',
        'Carrot': '#E67E22',
        'Pumpkin': '#D35400',
        'Alizarin': '#E74C3C',
        'Pomegranate': '#C0392B',
        'Clouds': '#ECF0F1',
        'Silver': '#BDC3C7',
        'Concrete': '#95A5A6',
        'Asbestos': '#7F8C8D'
    }
    
    SEASONAL_THEMES = {
        'Spring': ['#FFB6C1', '#98FB98', '#87CEEB', '#FFFFE0', '#FFE4E1'],
        'Summer': ['#FFD700', '#FF6347', '#00CED1', '#FF69B4', '#FFA500'],
        'Autumn': ['#D2691E', '#FF8C00', '#8B4513', '#CD853F', '#DEB887'],
        'Winter': ['#4682B4', '#B0C4DE', '#708090', '#FFFFFF', '#ADD8E6']
    }
    
    PURPOSE_THEMES = {
        'Corporate': ['#003366', '#0066CC', '#6699CC', '#99CCFF', '#CCDDFF'],
        'Tech': ['#00D9FF', '#0099CC', '#003D5C', '#FF6600', '#333333'],
        'Nature': ['#228B22', '#32CD32', '#90EE90', '#8FBC8F', '#556B2F'],
        'Elegant': ['#2C3E50', '#8E44AD', '#C0392B', '#E67E22', '#ECF0F1'],
        'Vibrant': ['#FF1744', '#FF9100', '#FFD600', '#00E676', '#00B0FF'],
        'Pastel': ['#FFB3BA', '#FFDFBA', '#FFFFBA', '#BAFFC9', '#BAE1FF'],
        'Dark': ['#121212', '#1E1E1E', '#2C2C2C', '#383838', '#4A4A4A'],
        'Monochrome': ['#000000', '#404040', '#808080', '#BFBFBF', '#FFFFFF'],
        'Warm': ['#FF6B6B', '#FFA07A', '#FFD93D', '#FF8C42', '#F95959'],
        'Cool': ['#4A90E2', '#50C9CE', '#7B68EE', '#5F9EA0', '#6495ED']
    }
    
    def __init__(self):
        self.palettes = []
    
    def hex_to_rgb(self, hex_color):
        """Convert HEX to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(self, rgb):
        """Convert RGB to HEX"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    def generate_analogous_palette(self, base_hex):
        """Generate analogous color palette"""
        import colorsys
        r, g, b = self.hex_to_rgb(base_hex)
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        colors = []
        for offset in [-60, -30, 0, 30, 60]:
            new_h = (h + offset/360) % 1.0
            new_rgb = colorsys.hsv_to_rgb(new_h, s, v)
            new_rgb = tuple(int(x * 255) for x in new_rgb)
            colors.append(self.rgb_to_hex(new_rgb))
        return colors
    
    def generate_complementary_palette(self, base_hex):
        """Generate complementary palette"""
        import colorsys
        r, g, b = self.hex_to_rgb(base_hex)
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        # Base color and its complement
        comp_h = (h + 0.5) % 1.0
        comp_rgb = colorsys.hsv_to_rgb(comp_h, s, v)
        comp_rgb = tuple(int(x * 255) for x in comp_rgb)
        
        # Add variations
        colors = [base_hex]
        for v_offset in [0.3, 0.15, 0, -0.15]:
            new_v = max(0, min(1, v + v_offset))
            rgb = colorsys.hsv_to_rgb(comp_h, s, new_v)
            rgb = tuple(int(x * 255) for x in rgb)
            colors.append(self.rgb_to_hex(rgb))
        return colors
    
    def generate_triadic_palette(self, base_hex):
        """Generate triadic palette"""
        import colorsys
        r, g, b = self.hex_to_rgb(base_hex)
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        colors = [base_hex]
        for offset in [1/3, 2/3]:
            new_h = (h + offset) % 1.0
            for v_mult in [1.0, 0.7]:
                new_v = v * v_mult
                rgb = colorsys.hsv_to_rgb(new_h, s, new_v)
                rgb = tuple(int(x * 255) for x in rgb)
                colors.append(self.rgb_to_hex(rgb))
        return colors[:5]
    
    def generate_all_palettes(self, count=500):
        """Generate comprehensive palette collection"""
        palettes = []
        palette_id = 1
        
        # 1. Material Design palettes
        for color_name, shades in self.MATERIAL_DESIGN_COLORS.items():
            for i in range(0, len(shades)-4, 2):
                palette = {
                    'id': palette_id,
                    'name': f'Material {color_name} {i+1}',
                    'colors': shades[i:i+5],
                    'tags': ['Material Design', color_name, 'Modern']
                }
                palettes.append(palette)
                palette_id += 1
        
        # 2. Flat UI variations
        flat_colors = list(self.FLAT_UI_COLORS.values())
        for i in range(0, len(flat_colors), 5):
            if i + 5 <= len(flat_colors):
                palette = {
                    'id': palette_id,
                    'name': f'Flat UI {i//5 + 1}',
                    'colors': flat_colors[i:i+5],
                    'tags': ['Flat UI', 'Web', 'Modern']
                }
                palettes.append(palette)
                palette_id += 1
        
        # 3. Generate from flat colors (analogous)
        for color_name, base_color in list(self.FLAT_UI_COLORS.items())[:10]:
            colors = self.generate_analogous_palette(base_color)
            palette = {
                'id': palette_id,
                'name': f'{color_name} Analogous',
                'colors': colors,
                'tags': ['Flat UI', 'Analogous', 'Harmony']
            }
            palettes.append(palette)
            palette_id += 1
        
        # 4. Seasonal themes
        for season, colors in self.SEASONAL_THEMES.items():
            palette = {
                'id': palette_id,
                'name': f'{season} Theme',
                'colors': colors,
                'tags': ['Seasonal', season, 'Theme']
            }
            palettes.append(palette)
            palette_id += 1
        
        # 5. Purpose themes
        for purpose, colors in self.PURPOSE_THEMES.items():
            palette = {
                'id': palette_id,
                'name': f'{purpose} Palette',
                'colors': colors,
                'tags': ['Purpose', purpose, 'Professional']
            }
            palettes.append(palette)
            palette_id += 1
        
        # 6. Generate random combinations
        all_material_colors = []
        for shades in self.MATERIAL_DESIGN_COLORS.values():
            all_material_colors.extend(shades)
        
        themes = ['Gradient', 'Vibrant', 'Soft', 'Bold', 'Muted', 'Bright']
        for i in range(min(count - len(palettes), 300)):
            colors = random.sample(all_material_colors, 5)
            theme = random.choice(themes)
            palette = {
                'id': palette_id,
                'name': f'{theme} Mix {i+1}',
                'colors': colors,
                'tags': ['Generated', theme, 'Random']
            }
            palettes.append(palette)
            palette_id += 1
        
        # 7. Complementary palettes from Material colors
        for color_name, shades in list(self.MATERIAL_DESIGN_COLORS.items())[:8]:
            base = shades[5] if len(shades) > 5 else shades[0]
            colors = self.generate_complementary_palette(base)
            palette = {
                'id': palette_id,
                'name': f'{color_name} Complementary',
                'colors': colors,
                'tags': ['Material Design', 'Complementary', 'Harmony']
            }
            palettes.append(palette)
            palette_id += 1
        
        # 8. Triadic palettes
        for color_name, shades in list(self.MATERIAL_DESIGN_COLORS.items())[:8]:
            base = shades[5] if len(shades) > 5 else shades[0]
            colors = self.generate_triadic_palette(base)
            palette = {
                'id': palette_id,
                'name': f'{color_name} Triadic',
                'colors': colors,
                'tags': ['Material Design', 'Triadic', 'Harmony']
            }
            palettes.append(palette)
            palette_id += 1
        
        # 9. More Material variations (all colors, all harmonies)
        for color_name, shades in self.MATERIAL_DESIGN_COLORS.items():
            for idx in [0, 3, 6, 9]:
                if idx < len(shades):
                    base = shades[idx]
                    # Analogous
                    colors = self.generate_analogous_palette(base)
                    palette = {
                        'id': palette_id,
                        'name': f'{color_name} {idx} Analogous',
                        'colors': colors,
                        'tags': ['Material Design', 'Analogous', color_name]
                    }
                    palettes.append(palette)
                    palette_id += 1
                    
                    # Complementary
                    colors = self.generate_complementary_palette(base)
                    palette = {
                        'id': palette_id,
                        'name': f'{color_name} {idx} Complement',
                        'colors': colors,
                        'tags': ['Material Design', 'Complementary', color_name]
                    }
                    palettes.append(palette)
                    palette_id += 1
        
        # 10. Flat UI + Material Design mixes
        flat_list = list(self.FLAT_UI_COLORS.values())
        for i in range(30):
            material_colors = random.sample(all_material_colors, 3)
            flat_colors = random.sample(flat_list, 2)
            colors = material_colors + flat_colors
            random.shuffle(colors)
            palette = {
                'id': palette_id,
                'name': f'Material+Flat Mix {i+1}',
                'colors': colors,
                'tags': ['Mixed', 'Material Design', 'Flat UI']
            }
            palettes.append(palette)
            palette_id += 1
        
        # 11. More theme variations
        theme_mixes = [
            ('Warm Sunset', ['#FF6B6B', '#FFA07A', '#FFD93D', '#FF8C42', '#F95959']),
            ('Cool Ocean', ['#4A90E2', '#50C9CE', '#6FEDD6', '#5DADE2', '#3498DB']),
            ('Forest Green', ['#2ECC71', '#27AE60', '#1E8449', '#0B5345', '#229954']),
            ('Royal Purple', ['#9B59B6', '#8E44AD', '#6C3483', '#512E5F', '#7D3C98']),
            ('Warm Earth', ['#A0522D', '#8B4513', '#D2691E', '#CD853F', '#DEB887']),
            ('Neon Night', ['#FF00FF', '#00FFFF', '#FFFF00', '#FF1493', '#00FF00']),
            ('Pastel Dream', ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#E0BBE4']),
            ('Corporate Blue', ['#003366', '#004D99', '#0066CC', '#0080FF', '#3399FF']),
            ('Vintage Rose', ['#C88B8B', '#D4A5A5', '#E8C4C4', '#F5E1E1', '#FFEEE6']),
            ('Cyber Tech', ['#00FF9F', '#00FFFF', '#BF00FF', '#FF00BF', '#FFBF00']),
            ('Desert Sand', ['#EDC9AF', '#E0AC69', '#C19A6B', '#D2B48C', '#F5DEB3']),
            ('Arctic Ice', ['#E0F2F7', '#B3E5FC', '#81D4FA', '#4FC3F7', '#29B6F6']),
            ('Cherry Blossom', ['#FFB7C5', '#FFC0CB', '#FFD1DC', '#FFE4E1', '#FFF0F5']),
            ('Mint Fresh', ['#98FF98', '#90EE90', '#8FBC8F', '#3CB371', '#2E8B57']),
            ('Autumn Leaves', ['#FF6347', '#FF7F50', '#FF8C00', '#FFA500', '#FFB347']),
        ]
        
        for theme_name, colors in theme_mixes:
            palette = {
                'id': palette_id,
                'name': theme_name,
                'colors': colors,
                'tags': ['Theme', 'Curated', theme_name.split()[0]]
            }
            palettes.append(palette)
            palette_id += 1
        
        # 12. Monochromatic variations
        base_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF',
                       '#FF8800', '#8800FF', '#00FF88', '#FF0088', '#88FF00', '#0088FF']
        for base_hex in base_colors:
            import colorsys
            r, g, b = self.hex_to_rgb(base_hex)
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            colors = []
            for v_val in [0.3, 0.5, 0.7, 0.85, 1.0]:
                rgb = colorsys.hsv_to_rgb(h, s, v_val)
                rgb = tuple(int(x * 255) for x in rgb)
                colors.append(self.rgb_to_hex(rgb))
            palette = {
                'id': palette_id,
                'name': f'Mono {base_hex[1:4]}',
                'colors': colors,
                'tags': ['Monochromatic', 'Gradient', 'Simple']
            }
            palettes.append(palette)
            palette_id += 1
        
        # 13. Extended Material Design combinations
        material_keys = list(self.MATERIAL_DESIGN_COLORS.keys())
        for i in range(50):
            color1, color2 = random.sample(material_keys, 2)
            shades1 = self.MATERIAL_DESIGN_COLORS[color1]
            shades2 = self.MATERIAL_DESIGN_COLORS[color2]
            colors = [
                random.choice(shades1),
                random.choice(shades1),
                random.choice(shades2),
                random.choice(shades2),
                random.choice(shades1)
            ]
            palette = {
                'id': palette_id,
                'name': f'{color1}+{color2} Blend',
                'colors': colors,
                'tags': ['Material Design', 'Blend', color1, color2]
            }
            palettes.append(palette)
            palette_id += 1
        
        # 14. Saturation variations
        for color_name, shades in list(self.MATERIAL_DESIGN_COLORS.items())[:10]:
            base = shades[5] if len(shades) > 5 else shades[0]
            r, g, b = self.hex_to_rgb(base)
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            colors = []
            for s_val in [0.2, 0.4, 0.6, 0.8, 1.0]:
                rgb = colorsys.hsv_to_rgb(h, s_val, v)
                rgb = tuple(int(x * 255) for x in rgb)
                colors.append(self.rgb_to_hex(rgb))
            palette = {
                'id': palette_id,
                'name': f'{color_name} Saturation',
                'colors': colors,
                'tags': ['Material Design', 'Saturation', color_name]
            }
            palettes.append(palette)
            palette_id += 1
        
        # 15. Temperature-based palettes
        warm_hues = [0, 15, 30, 45]  # Red to yellow range
        cool_hues = [180, 195, 210, 225, 240]  # Cyan to blue range
        
        for i in range(20):
            colors = []
            for hue in random.sample(warm_hues, 3) + random.sample([20, 35], 2):
                h = hue / 360
                s = random.uniform(0.6, 0.9)
                v = random.uniform(0.7, 1.0)
                rgb = colorsys.hsv_to_rgb(h, s, v)
                rgb = tuple(int(x * 255) for x in rgb)
                colors.append(self.rgb_to_hex(rgb))
            palette = {
                'id': palette_id,
                'name': f'Warm Palette {i+1}',
                'colors': colors,
                'tags': ['Temperature', 'Warm', 'Generated']
            }
            palettes.append(palette)
            palette_id += 1
        
        for i in range(20):
            colors = []
            for hue in random.sample(cool_hues, 5):
                h = hue / 360
                s = random.uniform(0.6, 0.9)
                v = random.uniform(0.7, 1.0)
                rgb = colorsys.hsv_to_rgb(h, s, v)
                rgb = tuple(int(x * 255) for x in rgb)
                colors.append(self.rgb_to_hex(rgb))
            palette = {
                'id': palette_id,
                'name': f'Cool Palette {i+1}',
                'colors': colors,
                'tags': ['Temperature', 'Cool', 'Generated']
            }
            palettes.append(palette)
            palette_id += 1
        
        # 16. Brand-inspired palettes
        brand_palettes = [
            ('Tech Blue', ['#0078D7', '#106EBE', '#005A9E', '#00428A', '#003E82']),
            ('Social Media', ['#1DA1F2', '#FF0000', '#0077B5', '#833AB4', '#25D366']),
            ('Nature Green', ['#52B788', '#40916C', '#2D6A4F', '#1B4332', '#081C15']),
            ('Sunset Orange', ['#FF6B35', '#F7931E', '#FDC500', '#F78F1E', '#F95738']),
            ('Deep Purple', ['#5D3FD3', '#6A5ACD', '#7B68EE', '#9370DB', '#8A2BE2']),
            ('Coral Pink', ['#FF6F61', '#FF7F7F', '#FF91A4', '#FFA6C1', '#FFB6C1']),
            ('Emerald', ['#50C878', '#3EB489', '#2D9D7A', '#1B866B', '#0A6F5C']),
            ('Amber', ['#FFBF00', '#FFB700', '#FFAA00', '#FF9500', '#FF8800']),
            ('Teal', ['#008080', '#00A9A5', '#00B4A6', '#00C4AD', '#00D4B4']),
            ('Crimson', ['#DC143C', '#C91A3A', '#B21838', '#9B1436', '#841134']),
            ('Navy', ['#000080', '#001A66', '#003080', '#004799', '#005EB3']),
            ('Gold', ['#FFD700', '#FFC700', '#FFB700', '#FFA700', '#FF9700']),
            ('Silver', ['#C0C0C0', '#A9A9A9', '#999999', '#808080', '#696969']),
            ('Olive', ['#808000', '#999900', '#AAAA00', '#BBBB00', '#CCCC00']),
            ('Maroon', ['#800000', '#990000', '#AA0000', '#BB0000', '#CC0000']),
            ('Lime', ['#00FF00', '#33FF33', '#66FF66', '#99FF99', '#CCFFCC']),
            ('Aqua', ['#00FFFF', '#33FFFF', '#66FFFF', '#99FFFF', '#CCFFFF']),
            ('Fuchsia', ['#FF00FF', '#FF33FF', '#FF66FF', '#FF99FF', '#FFCCFF']),
            ('Indigo', ['#4B0082', '#5D1A99', '#6F33B3', '#814DCC', '#9366E6']),
            ('Turquoise', ['#40E0D0', '#4DE6D7', '#5AECDE', '#66F2E5', '#73F8EC']),
        ]
        
        for name, colors in brand_palettes:
            palette = {
                'id': palette_id,
                'name': name,
                'colors': colors,
                'tags': ['Brand', 'Curated', name.split()[0]]
            }
            palettes.append(palette)
            palette_id += 1
        
        # 17. Split complementary palettes
        for color_name, shades in list(self.MATERIAL_DESIGN_COLORS.items())[:15]:
            base = shades[5] if len(shades) > 5 else shades[0]
            r, g, b = self.hex_to_rgb(base)
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            
            colors = [base]
            # Split complementary (150° and 210° from base)
            for angle in [150, 210]:
                new_h = (h + angle/360) % 1.0
                for v_mult in [1.0, 0.7]:
                    new_v = v * v_mult
                    rgb = colorsys.hsv_to_rgb(new_h, s, new_v)
                    rgb = tuple(int(x * 255) for x in rgb)
                    colors.append(self.rgb_to_hex(rgb))
            
            palette = {
                'id': palette_id,
                'name': f'{color_name} Split Comp',
                'colors': colors[:5],
                'tags': ['Material Design', 'Split Complementary', color_name]
            }
            palettes.append(palette)
            palette_id += 1
        
        # 18. Square (tetradic) palettes
        for color_name, shades in list(self.MATERIAL_DESIGN_COLORS.items())[:15]:
            base = shades[5] if len(shades) > 5 else shades[0]
            r, g, b = self.hex_to_rgb(base)
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            
            colors = [base]
            # Square: 90°, 180°, 270° from base
            for angle in [90, 180, 270]:
                new_h = (h + angle/360) % 1.0
                rgb = colorsys.hsv_to_rgb(new_h, s, v)
                rgb = tuple(int(x * 255) for x in rgb)
                colors.append(self.rgb_to_hex(rgb))
            
            palette = {
                'id': palette_id,
                'name': f'{color_name} Square',
                'colors': colors[:5],
                'tags': ['Material Design', 'Square', 'Tetradic']
            }
            palettes.append(palette)
            palette_id += 1
        
        # 19. More curated theme palettes
        extra_themes = [
            ('Midnight Blue', ['#191970', '#000080', '#00008B', '#0000CD', '#0000FF']),
            ('Peachy Keen', ['#FFDAB9', '#FFDEAD', '#FFE4B5', '#FFEFD5', '#FFF8DC']),
            ('Lavender Fields', ['#E6E6FA', '#D8BFD8', '#DDA0DD', '#EE82EE', '#DA70D6']),
            ('Cinnamon Spice', ['#D2691E', '#CD853F', '#DEB887', '#F5DEB3', '#FFEFD5']),
            ('Seafoam', ['#9FE2BF', '#87CEEB', '#7FFFD4', '#40E0D0', '#48D1CC']),
            ('Burgundy Wine', ['#800020', '#8B0000', '#A52A2A', '#B22222', '#CD5C5C']),
            ('Mustard Yellow', ['#FFDB58', '#FFD700', '#FFDF00', '#FFE135', '#FFEC8B']),
            ('Plum Purple', ['#8E4585', '#9932CC', '#8B008B', '#9400D3', '#9370DB']),
            ('Sage Green', ['#BCB88A', '#C9CC3F', '#B2AC88', '#A7A77D', '#9C9C72']),
            ('Rust', ['#B7410E', '#C85A17', '#D97220', '#EA8A29', '#FBA232']),
            ('Charcoal', ['#36454F', '#464646', '#555555', '#696969', '#808080']),
            ('Cream', ['#FFFDD0', '#FAFAD2', '#FFF8DC', '#FFEFD5', '#FFE4B5']),
            ('Slate', ['#708090', '#778899', '#87CEEB', '#B0C4DE', '#DCDCDC']),
            ('Tangerine', ['#FF9F00', '#FFA500', '#FFB347', '#FFC87C', '#FFDAB9']),
            ('Raspberry', ['#E30B5C', '#E6004C', '#E6007E', '#E600AC', '#E63E97']),
            ('Pine', ['#01796F', '#0B7B70', '#147D71', '#1E7F72', '#288173']),
            ('Champagne', ['#F7E7CE', '#F8E8D0', '#F9E9D2', '#FAEAD4', '#FBEBD6']),
            ('Mahogany', ['#C04000', '#C85A3C', '#D07456', '#D88E70', '#E0A88A']),
            ('Periwinkle', ['#CCCCFF', '#C5CBE1', '#BFC9E3', '#B9C8E5', '#B3C6E7']),
            ('Butterscotch', ['#E1A95F', '#E5B56C', '#E9C179', '#EDCD86', '#F1D993']),
        ]
        
        for name, colors in extra_themes:
            palette = {
                'id': palette_id,
                'name': name,
                'colors': colors,
                'tags': ['Theme', 'Curated', name.split()[0]]
            }
            palettes.append(palette)
            palette_id += 1
        
        # 20. Final random high-quality mixes
        for i in range(100):
            colors = random.sample(all_material_colors, 5)
            palette = {
                'id': palette_id,
                'name': f'Curated Mix {i+1}',
                'colors': colors,
                'tags': ['Generated', 'Mixed', 'Quality']
            }
            palettes.append(palette)
            palette_id += 1
        
        self.palettes = palettes
        return palettes
    
    def save_palettes(self, filename='preset_palettes.dat'):
        """Save palettes to encrypted compressed file"""
        try:
            # Convert to JSON
            data = json.dumps(self.palettes, ensure_ascii=False)
            
            # Compress
            compressed = gzip.compress(data.encode('utf-8'))
            
            # Encrypt using embedded key
            fernet = Fernet(EMBEDDED_ENCRYPTION_KEY)
            encrypted = fernet.encrypt(compressed)
            
            # Save encrypted data
            with open(filename, 'wb') as f:
                f.write(encrypted)
            
            print(f"✓ Saved {len(self.palettes)} palettes to {filename}")
            print(f"✓ Using embedded encryption key (secure)")
            return True
        except Exception as e:
            print(f"Error saving palettes: {e}")
            return False
    
    @staticmethod
    def load_palettes(filename='preset_palettes.dat'):
        """Load palettes from encrypted file"""
        try:
            # Load encrypted data
            with open(filename, 'rb') as f:
                encrypted = f.read()
            
            # Decrypt using embedded key
            fernet = Fernet(EMBEDDED_ENCRYPTION_KEY)
            compressed = fernet.decrypt(encrypted)
            
            # Decompress
            data = gzip.decompress(compressed).decode('utf-8')
            
            # Parse JSON
            palettes = json.loads(data)
            print(f"✓ Loaded {len(palettes)} palettes from {filename}")
            return palettes
        except Exception as e:
            print(f"Error loading palettes: {e}")
            return []


# Generate palettes if run directly
if __name__ == "__main__":
    generator = PresetPaletteGenerator()
    palettes = generator.generate_all_palettes(count=1200)
    print(f"Generated {len(palettes)} palettes")
    
    # Save to file
    generator.save_palettes('preset_palettes.dat')
    
    # Test loading
    loaded = PresetPaletteGenerator.load_palettes('preset_palettes.dat')
    print(f"Verification: Loaded {len(loaded)} palettes")
