"""
Color Palette Generator Module
Handles color palette generation and harmony calculations
"""

from PIL import Image
import colorsys
from collections import Counter
import random
import logging


class ColorPaletteGenerator:
    """Color palette generator class"""
    
    def __init__(self):
        pass
    
    def extract_main_colors(self, image_path, num_colors=5, filter_background=True):
        """Extract main colors from image using improved K-means clustering"""
        img = Image.open(image_path)
        img = img.convert('RGB')
        img = img.resize((150, 150))

        pixels = list(img.getdata())
        
        if filter_background:
            filtered_pixels = []
            for p in pixels:
                r, g, b = p
                lum = 0.299 * r + 0.587 * g + 0.114 * b
                max_c = max(r, g, b)
                min_c = min(r, g, b)
                sat = 0 if max_c == 0 else (max_c - min_c) / max_c
                
                if not (lum > 240 or lum < 15 or sat < 0.15):
                    filtered_pixels.append(p)
            
            pixels = filtered_pixels if len(filtered_pixels) > 100 else pixels
        
        unique_colors = set(pixels)
        unique_count = len(unique_colors)

        if unique_count <= num_colors:
            pixel_count = Counter(pixels)
            main_colors = [c for c, _ in pixel_count.most_common(num_colors)]
            return main_colors[:num_colors]

        # Prepare data for k-means: sample if too many pixels
        data = pixels
        max_samples = 2000
        if len(data) > max_samples:
            data = random.sample(data, max_samples)

        # initialize centroids by sampling distinct points
        centroids = []
        # ensure we don't sample duplicate initial centroids
        tries = 0
        while len(centroids) < num_colors and tries < num_colors * 10:
            c = tuple(random.choice(data))
            if c not in centroids:
                centroids.append([float(c[0]), float(c[1]), float(c[2])])
            tries += 1

        # fallback if not enough distinct points
        while len(centroids) < num_colors:
            centroids.append([random.randint(0,255), random.randint(0,255), random.randint(0,255)])

        # K-means iterations (Euclidean in RGB)
        max_iter = 12
        for _ in range(max_iter):
            clusters = [[] for _ in range(len(centroids))]
            for p in data:
                # find nearest centroid
                best_i = 0
                best_d = None
                for i, c in enumerate(centroids):
                    dx = c[0] - p[0]
                    dy = c[1] - p[1]
                    dz = c[2] - p[2]
                    d = dx*dx + dy*dy + dz*dz
                    if best_d is None or d < best_d:
                        best_d = d
                        best_i = i
                clusters[best_i].append(p)

            moved = False
            # recompute centroids
            for i, pts in enumerate(clusters):
                if not pts:
                    # reinitialize empty centroid
                    centroids[i] = [float(x) for x in random.choice(data)]
                    moved = True
                    continue
                sx = sum(p[0] for p in pts) / len(pts)
                sy = sum(p[1] for p in pts) / len(pts)
                sz = sum(p[2] for p in pts) / len(pts)
                if (abs(centroids[i][0] - sx) > 0.5 or
                        abs(centroids[i][1] - sy) > 0.5 or
                        abs(centroids[i][2] - sz) > 0.5):
                    moved = True
                centroids[i][0] = sx
                centroids[i][1] = sy
                centroids[i][2] = sz

            if not moved:
                break

        # After convergence, count assignment over full pixel set to get dominant clusters
        full_clusters = [[] for _ in range(len(centroids))]
        for p in pixels:
            best_i = 0
            best_d = None
            for i, c in enumerate(centroids):
                dx = c[0] - p[0]
                dy = c[1] - p[1]
                dz = c[2] - p[2]
                d = dx*dx + dy*dy + dz*dz
                if best_d is None or d < best_d:
                    best_d = d
                    best_i = i
            full_clusters[best_i].append(p)

        # compute final centroids as integer RGB and sort by cluster size
        results = []
        for pts in full_clusters:
            if pts:
                sx = int(sum(p[0] for p in pts) / len(pts))
                sy = int(sum(p[1] for p in pts) / len(pts))
                sz = int(sum(p[2] for p in pts) / len(pts))
                results.append(((sx, sy, sz), len(pts)))

        if not results:
            # fallback
            pixel_count = Counter(pixels)
            return [c for c, _ in pixel_count.most_common(num_colors)][:num_colors]

        # sort by size desc and return top num_colors
        results.sort(key=lambda x: x[1], reverse=True)
        colors = [c for c, _ in results][:num_colors]
        return colors

    def approximate_color_count(self, image_path, sample_size=None):
        """이미지의 대략적인 색상 수를 계산합니다."""
        img = Image.open(image_path)
        img = img.convert('RGB')
        img = img.resize((100, 100))
        pixels = list(img.getdata())
        if sample_size and len(pixels) > sample_size:
            pixels = random.sample(pixels, sample_size)
        return len(set(pixels))

    def hex_to_rgb(self, hex_code):
        """HEX를 RGB로 변환"""
        hex_code = hex_code.lstrip('#')
        if len(hex_code) == 3:
            hex_code = ''.join([c*2 for c in hex_code])
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(self, rgb):
        """RGB를 HEX로 변환"""
        if isinstance(rgb, tuple) or isinstance(rgb, list):
            return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        return '#000000'
    
    def rgb_to_hsv(self, r, g, b):
        """RGB를 HSV로 변환 (with error handling)"""
        try:
            r = max(0, min(255, int(r)))
            g = max(0, min(255, int(g)))
            b = max(0, min(255, int(b)))
            return colorsys.rgb_to_hsv(r/255, g/255, b/255)
        except (ValueError, TypeError) as e:
            logging.warning(f"RGB to HSV conversion error: {e}")
            return 0.0, 0.0, 0.0
    
    def hsv_to_rgb(self, h, s, v):
        """HSV를 RGB로 변환 (with bounds checking)"""
        try:
            h = h % 1.0
            s = max(0.0, min(1.0, s))
            v = max(0.0, min(1.0, v))
            rgb = colorsys.hsv_to_rgb(h, s, v)
            return tuple(max(0, min(255, int(x * 255))) for x in rgb)
        except (ValueError, TypeError) as e:
            logging.warning(f"HSV to RGB conversion error: {e}")
            return (0, 0, 0)
    
    def generate_complementary(self, rgb):
        """보색 생성"""
        h, s, v = self.rgb_to_hsv(*rgb)
        comp_h = (h + 0.5) % 1.0
        return self.hsv_to_rgb(comp_h, s, v)
    
    def generate_analogous(self, rgb, angle=30):
        """유사색 생성 (각도 기반)"""
        h, s, v = self.rgb_to_hsv(*rgb)
        analogous_colors = []
        
        for offset in [-angle/360, angle/360]:
            new_h = (h + offset) % 1.0
            analogous_colors.append(self.hsv_to_rgb(new_h, s, v))
        
        return analogous_colors
    
    def generate_triadic(self, rgb):
        """삼각 조화색 생성"""
        h, s, v = self.rgb_to_hsv(*rgb)
        triadic_colors = []
        
        for offset in [1/3, 2/3]:
            new_h = (h + offset) % 1.0
            triadic_colors.append(self.hsv_to_rgb(new_h, s, v))
        
        return triadic_colors
    
    def generate_monochromatic(self, rgb, count=4):
        """단색 조화 팔레트 생성 (명도/채도 변화)"""
        h, s, v = self.rgb_to_hsv(*rgb)
        mono_colors = []
        
        for i in range(1, count + 1):
            new_v = max(0.0, min(1.0, v * (0.3 + 0.7 * i / count)))
            new_s = max(0.0, min(1.0, s * (0.5 + 0.5 * i / count)))
            mono_colors.append(self.hsv_to_rgb(h, new_s, new_v))
        
        return mono_colors

    def generate_split_complementary(self, rgb):
        """스플릿 보색 조화"""
        h, s, v = self.rgb_to_hsv(*rgb)
        colors = []
        for offset in [150/360, 210/360]:
            new_h = (h + offset) % 1.0
            colors.append(self.hsv_to_rgb(new_h, s, v))
        return colors

    def generate_square(self, rgb):
        """스퀘어 조화"""
        h, s, v = self.rgb_to_hsv(*rgb)
        colors = []
        for offset in [120/360, 180/360, 240/360]:
            new_h = (h + offset) % 1.0
            colors.append(self.hsv_to_rgb(new_h, s, v))
        return colors

    def generate_tetradic(self, rgb):
        """테트라딕 조화"""
        h, s, v = self.rgb_to_hsv(*rgb)
        colors = []
        for offset in [60/360, 180/360, 240/360]:
            new_h = (h + offset) % 1.0
            colors.append(self.hsv_to_rgb(new_h, s, v))
        return colors

    def generate_double_complementary(self, rgb):
        """더블 보색"""
        h, s, v = self.rgb_to_hsv(*rgb)
        colors = []
        for offset in [30/360, 180/360, 210/360]:
            new_h = (h + offset) % 1.0
            colors.append(self.hsv_to_rgb(new_h, s, v))
        return colors

    def generate_random_color(self):
        """랜덤 색상 생성"""
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def adjust_brightness(self, rgb, factor):
        """밝기 조절 (-0.5 ~ 0.5)"""
        h, s, v = self.rgb_to_hsv(*rgb)
        new_v = max(0.0, min(1.0, v + factor))
        return self.hsv_to_rgb(h, s, new_v)

    def adjust_saturation(self, rgb, factor):
        """채도 조절 (-0.5 ~ 0.5)"""
        h, s, v = self.rgb_to_hsv(*rgb)
        new_s = max(0.0, min(1.0, s + factor))
        return self.hsv_to_rgb(h, new_s, v)

    def adjust_hue(self, rgb, degrees):
        """색조 조절 (-180 ~ 180 degrees)"""
        h, s, v = self.rgb_to_hsv(*rgb)
        new_h = (h + degrees / 360.0) % 1.0
        return self.hsv_to_rgb(new_h, s, v)

    def get_color_temperature(self, rgb):
        """색상 온도 계산 (warm=1, cool=-1, neutral=0)"""
        r, g, b = rgb
        if r > b + 30:
            return 1  # warm
        elif b > r + 30:
            return -1  # cool
        else:
            return 0  # neutral

    def generate_palette(self, source, source_type='hex'):
        """팔레트 생성"""
        if source_type == 'hex':
            base_color = self.hex_to_rgb(source)
        else:
            base_color = source

        palette = {
            'base': base_color,
            'complementary': self.generate_complementary(base_color),
            'analogous': self.generate_analogous(base_color),
            'triadic': self.generate_triadic(base_color),
            'monochromatic': self.generate_monochromatic(base_color),
            'split_complementary': self.generate_split_complementary(base_color),
            'square': self.generate_square(base_color),
            'tetradic': self.generate_tetradic(base_color),
            'double_complementary': self.generate_double_complementary(base_color)
        }
        
        return palette
