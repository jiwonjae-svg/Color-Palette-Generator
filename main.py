from PIL import Image, ImageTk, ImageGrab, ImageDraw
import colorsys
from collections import Counter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font as tkfont, colorchooser
import os
import random
import datetime
import tempfile
import logging
from cryptography.fernet import Fernet
import hashlib

class ColorPaletteGenerator:
    def __init__(self):
        pass
    
    def extract_main_colors(self, image_path, num_colors=5):
        """이미지에서 주요 색상 추출 (간단한 K-means 클러스터링 사용).

        동작:
        - 이미지를 작게 리사이즈해 픽셀을 샘플링
        - 고유 색상 수가 요청한 수보다 작거나 같으면 빈도 기반 상위 색상 반환
        - 그렇지 않으면 간단한 K-means를 수행해 서로 다른 대표 색상들을 반환
        """
        img = Image.open(image_path)
        img = img.convert('RGB')
        img = img.resize((150, 150))  # 성능을 위해 크기 축소

        pixels = list(img.getdata())
        unique_colors = set(pixels)
        unique_count = len(unique_colors)

        # If the image has relatively few distinct colors, return the most common ones
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
        """이미지의 대략적인 색상 수를 계산합니다.

        리사이즈해서 샘플링한 픽셀의 고유 색상 수를 반환합니다 (정확한 값 아님).
        """
        img = Image.open(image_path)
        img = img.convert('RGB')
        # Resize smaller for speed/approximation
        img = img.resize((120, 120))
        pixels = list(img.getdata())
        if sample_size and sample_size < len(pixels):
            pixels = random.sample(pixels, sample_size)
        return len(set(pixels))
    
    def rgb_to_hsv(self, r, g, b):
        """RGB를 HSV로 변환"""
        return colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    def hsv_to_rgb(self, h, s, v):
        """HSV를 RGB로 변환"""
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(x * 255) for x in rgb)
    
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
            # 명도/채도 변화 계산을 0-1 범위로 제한
            new_v = max(0.0, min(1.0, v * (0.3 + 0.7 * i / count)))
            new_s = max(0.0, min(1.0, s * (0.5 + 0.5 * i / count)))
            mono_colors.append(self.hsv_to_rgb(h, new_s, new_v))
        
        return mono_colors

    def generate_split_complementary(self, rgb):
        """스플릿 보색 조화 (보색 양옆 색상)"""
        h, s, v = self.rgb_to_hsv(*rgb)
        colors = []
        # 보색의 양옆 각도 (대략 150도와 210도)
        for offset in [150/360, 210/360]:
            new_h = (h + offset) % 1.0
            colors.append(self.hsv_to_rgb(new_h, s, v))
        return colors

    def generate_square(self, rgb):
        """스퀘어 조화 (정사각형 배치, 90도 간격 - 4색)"""
        h, s, v = self.rgb_to_hsv(*rgb)
        colors = []
        # 기본색 + 120도 + 240도 (실제 스퀘어는 90도이지만, 색상 휠에서 더 균형잡힌 배치)
        for offset in [120/360, 180/360, 240/360]:
            new_h = (h + offset) % 1.0
            colors.append(self.hsv_to_rgb(new_h, s, v))
        return colors

    def generate_tetradic(self, rgb):
        """테트라딕 조화 (사각형, 90도 간격 - 4색)"""
        h, s, v = self.rgb_to_hsv(*rgb)
        colors = []
        # 90도 간격 (정확한 사각형 배치)
        for offset in [90/360, 180/360, 270/360]:
            new_h = (h + offset) % 1.0
            colors.append(self.hsv_to_rgb(new_h, s, v))
        return colors

    def generate_double_complementary(self, rgb):
        """더블 보색 조화 (보색과 유사색의 보색)"""
        h, s, v = self.rgb_to_hsv(*rgb)
        colors = []
        # 보색 (180도)
        comp_h = (h + 0.5) % 1.0
        colors.append(self.hsv_to_rgb(comp_h, s, v))
        # 유사색들의 보색 (약 150도와 210도)
        for offset in [150/360, 210/360]:
            new_h = (h + offset) % 1.0
            colors.append(self.hsv_to_rgb(new_h, s, v))
        return colors
    
    def rgb_to_hex(self, rgb):
        """RGB를 HEX로 변환"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    def hex_to_rgb(self, hex_code):
        """HEX를 RGB로 변환"""
        hex_code = hex_code.lstrip('#')
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

    def generate_random_color(self):
        """랜덤 RGB 색상 생성"""
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    def generate_palette(self, source, source_type='hex'):
        """전체 팔레트 생성 (모든 조화 포함)"""
        if source_type == 'hex':
            base_color = self.hex_to_rgb(source)
        elif source_type == 'image':
            main_colors = self.extract_main_colors(source)
            base_color = main_colors[0]
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

class PaletteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("700x520")
        self.resizable(False, False)
        self.generator = ColorPaletteGenerator()
        self.image_path = None
        self._temp_screenshot = None  # track temp screenshot file for cleanup
        # Default selected harmony schemes
        self.selected_schemes = ['complementary', 'analogous', 'triadic', 'monochromatic']
        
        # Track current file and modified state
        self.current_file = None
        self.is_modified = False
        
        # Setup logging
        self.setup_logging()
        self.log_action("Application started")
        
        # Setup window close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()
        
        # Update title after widgets are created
        self.update_title()
    
    def create_widgets(self):
        frm_top = ttk.Frame(self, padding=10)
        frm_top.pack(fill='x')

        # Menu bar (File -> New PGF / Save PGF / Save As / Open PGF / Open Recent / Exit)
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='New PGF...', command=self.new_pgf)
        filemenu.add_command(label='Save PGF...', command=self.save_pgf)
        filemenu.add_command(label='Save As...', command=self.save_pgf_as)
        filemenu.add_command(label='Open PGF...', command=self.load_pgf)
        
        # Open Recent submenu
        self.recent_menu = tk.Menu(filemenu, tearoff=0)
        filemenu.add_cascade(label='Open Recent', menu=self.recent_menu)
        self.update_recent_menu()
        
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=self.quit)
        menubar.add_cascade(label='File', menu=filemenu)
        self.config(menu=menubar)

        # Source type radio
        self.source_type = tk.StringVar(value='hex')
        rb_hex = ttk.Radiobutton(frm_top, text='색상 선택', value='hex', variable=self.source_type, command=self.on_source_change)
        rb_img = ttk.Radiobutton(frm_top, text='이미지 선택', value='image', variable=self.source_type, command=self.on_source_change)
        rb_hex.grid(row=0, column=0, sticky='w')
        rb_img.grid(row=0, column=1, sticky='w', padx=(8,0))

        # make columns have reasonable minimum widths for alignment
        for i, ms in enumerate((80, 120, 110, 160, 60, 120)):
            try:
                frm_top.columnconfigure(i, minsize=ms)
            except Exception:
                pass

        # Color picker button and swatch display
        self.hex_entry = tk.StringVar(value="#3498db")  # store hex value internally
        self.color_swatch = tk.Canvas(frm_top, width=70, height=48, bd=0, relief='solid', highlightthickness=0)
        self.color_swatch.grid(row=1, column=0, pady=(8,0), sticky='nw', padx=(0,0))
        
        # Color info label (hex and RGB) - create BEFORE _update_color_swatch
        self.lbl_color_info = ttk.Label(frm_top, text="HEX: #3498db\nRGB: (52, 152, 219)", font=('Segoe UI', 9))
        # span two columns so it doesn't collide with buttons
        self.lbl_color_info.grid(row=2, column=0, columnspan=2, pady=(2,0), sticky='w')
        
        # Now update the swatch and color info
        self._update_color_swatch("#3498db")
        
        self.btn_color_picker = ttk.Button(frm_top, text="색상 선택...", command=self.open_color_picker)
        self.btn_color_picker.grid(row=1, column=1, pady=(8,0), padx=(8,0), sticky='w')

        # Image select
        self.btn_select_img = ttk.Button(frm_top, text="이미지 선택...", command=self.select_image)
        self.btn_select_img.grid(row=1, column=2, padx=(8,0), pady=(8,0), sticky='w')
        self.lbl_image = ttk.Label(frm_top, text="선택된 파일 없음")
        self.lbl_image.grid(row=1, column=3, padx=(8,0), sticky='w')
        # small thumbnail next to image name
        self.img_thumbnail_label = ttk.Label(frm_top)
        self.img_thumbnail_label.grid(row=1, column=4, padx=(8,0))
        # Screen picker button
        btn_screen_pick = ttk.Button(frm_top, text="스크린에서 추출", command=self.start_screen_picker)
        btn_screen_pick.grid(row=1, column=5, padx=(8,0), pady=(8,0), sticky='w')

        # action buttons row (separate row to avoid collisions)
        btn_generate = ttk.Button(frm_top, text="Generate", command=self.generate)
        btn_generate.grid(row=3, column=0, pady=(12,0), sticky='w')
        # Random color button
        btn_random = ttk.Button(frm_top, text="랜덤 색상", command=self.generate_random)
        btn_random.grid(row=3, column=1, padx=(8,0), pady=(12,0), sticky='w')
        # Color harmony options button
        btn_harmony = ttk.Button(frm_top, text="색상 조합 옵션", command=self.open_harmony_selector)
        btn_harmony.grid(row=3, column=2, padx=(8,0), pady=(12,0), sticky='w')
        

        # Separator
        sep = ttk.Separator(self, orient='horizontal')
        sep.pack(fill='x', pady=10)

        # Main content area: left = palette display, right = saved palettes panel
        content = ttk.Frame(self)
        content.pack(fill='both', expand=True)

        # Left: Palette display area
        self.frm_palette = ttk.Frame(content, padding=10)
        self.frm_palette.pack(side='left', fill='both', expand=True)

        # Color tabs (extracted swatches) shown above the palette area
        self.frm_color_tabs = ttk.Frame(self.frm_palette)
        self.frm_color_tabs.pack(fill='x', pady=(0,6))

        # Right: Saved palettes panel
        self.frm_saved = ttk.Frame(content, padding=(6,6))
        self.frm_saved.pack(side='right', fill='y')

        ttk.Label(self.frm_saved, text='저장된 팔레트', font=('Segoe UI', 10, 'bold')).pack(anchor='nw', side='top')
        
        # buttons: add / remove / copy / load (fixed at bottom - pack first)
        btns = tk.Frame(self.frm_saved, bg='#f0f0f0', height=40)
        btns.pack(side='bottom', fill='x', pady=(4,0))
        btns.pack_propagate(False)
        
        # Create buttons with emojis and tooltips
        btn_add = tk.Button(btns, text='➕', font=('Arial', 14), command=self.add_saved_palette, width=3, bg='#f0f0f0', relief='flat', cursor='hand2')
        btn_add.pack(side='left', padx=4, pady=5)
        self.create_tooltip(btn_add, '팔레트 추가')
        
        btn_delete = tk.Button(btns, text='❌', font=('Arial', 14), command=self.remove_saved_palette, width=3, bg='#f0f0f0', relief='flat', cursor='hand2')
        btn_delete.pack(side='left', padx=4, pady=5)
        self.create_tooltip(btn_delete, '팔레트 제거')
        
        btn_copy = tk.Button(btns, text='📋', font=('Arial', 14), command=self.copy_palette, width=3, bg='#f0f0f0', relief='flat', cursor='hand2')
        btn_copy.pack(side='left', padx=4, pady=5)
        self.create_tooltip(btn_copy, '팔레트 복사')
        
        btn_load = tk.Button(btns, text='📂', font=('Arial', 14), command=self.load_palette, width=3, bg='#f0f0f0', relief='flat', cursor='hand2')
        btn_load.pack(side='left', padx=4, pady=5)
        self.create_tooltip(btn_load, '팔레트 불러오기')
        
        # scrollable container for saved palette entries
        list_frame = ttk.Frame(self.frm_saved)
        list_frame.pack(fill='both', expand=True, pady=(6,6))
        
        self.saved_canvas = tk.Canvas(list_frame, borderwidth=0, highlightthickness=0, bg='white', width=200)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.saved_canvas.yview)
        self.saved_list_container = tk.Frame(self.saved_canvas, bg='white')
        
        self.saved_list_container.bind(
            '<Configure>',
            lambda e: self.saved_canvas.configure(scrollregion=self.saved_canvas.bbox('all'))
        )
        
        self.saved_canvas.create_window((0, 0), window=self.saved_list_container, anchor='nw')
        self.saved_canvas.configure(yscrollcommand=scrollbar.set)
        
        # bind canvas resize to update window width (with margin)
        def on_canvas_configure(e):
            # set width to canvas width minus scrollbar width and some margin
            new_width = e.width - 20
            if self.saved_canvas.find_withtag('all'):
                self.saved_canvas.itemconfig(self.saved_canvas.find_withtag('all')[0], width=new_width)
        self.saved_canvas.bind('<Configure>', on_canvas_configure)
        
        # enable mousewheel scrolling when mouse is over any part of the saved palette region
        def on_mousewheel(e):
            # Only scroll if scrollbar is actually needed
            try:
                bbox = self.saved_canvas.bbox('all')
                canvas_height = self.saved_canvas.winfo_height()
                if bbox and bbox[3] > canvas_height:
                    self.saved_canvas.yview_scroll(int(-1*(e.delta/120)), 'units')
            except Exception:
                pass
        
        # Store handler for rebinding after render
        self._saved_scroll_handler = on_mousewheel
        
        # Bind to all widgets in the saved palette region
        def bind_scroll_recursive(widget):
            try:
                widget.bind('<MouseWheel>', on_mousewheel, add='+')
                for child in widget.winfo_children():
                    bind_scroll_recursive(child)
            except Exception:
                pass
        
        bind_scroll_recursive(self.frm_saved)
        self.frm_saved.bind('<MouseWheel>', on_mousewheel)
        
        self.saved_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # storage for saved palettes (in-memory)
        self.saved_palettes = []  # list of dicts: {'name': str, 'colors': [hex,...]}
        self._saved_counter = 0
        self._saved_selected = None  # index of selected saved palette

        # create initial saved palette (without triggering mark_modified)
        name = f"새 팔레트{self._saved_counter + 1}"
        self._saved_counter += 1
        entry = {'name': name, 'colors': []}
        self.saved_palettes.append(entry)
        # select the first one by default
        if self.saved_palettes:
            self._saved_selected = 0
            self.render_saved_list()

        # Ensure saves directories exist
        self.saves_root = os.path.join(os.getcwd(), 'saves')
        for sub in ('txt', 'png', 'pgf'):
            try:
                os.makedirs(os.path.join(self.saves_root, sub), exist_ok=True)
            except Exception:
                pass

        # Scrollable canvas for palette (in case of small screens)
        self.palette_canvas = tk.Canvas(self.frm_palette, borderwidth=0, highlightthickness=0)
        self.palette_inner = ttk.Frame(self.palette_canvas)
        self.palette_vsb = ttk.Scrollbar(self.frm_palette, orient="vertical", command=self.palette_canvas.yview)
        self.palette_canvas.configure(yscrollcommand=self.palette_vsb.set)
        self.palette_vsb.pack(side="right", fill="y")
        self.palette_canvas.pack(side="left", fill="both", expand=True)
        self.palette_canvas.create_window((0,0), window=self.palette_inner, anchor="nw")
        self.palette_inner.bind("<Configure>", lambda e: self.palette_canvas.configure(scrollregion=self.palette_canvas.bbox("all")))
        
        # Enable mousewheel scrolling for main palette area
        def on_palette_mousewheel(e):
            try:
                bbox = self.palette_canvas.bbox('all')
                canvas_height = self.palette_canvas.winfo_height()
                if bbox and bbox[3] > canvas_height:
                    self.palette_canvas.yview_scroll(int(-1*(e.delta/120)), 'units')
            except Exception:
                pass
        
        # Store handler for rebinding after display updates
        self._palette_scroll_handler = on_palette_mousewheel
        
        # Bind to palette region widgets
        def bind_palette_scroll_recursive(widget):
            try:
                widget.bind('<MouseWheel>', on_palette_mousewheel, add='+')
                for child in widget.winfo_children():
                    bind_palette_scroll_recursive(child)
            except Exception:
                pass
        
        bind_palette_scroll_recursive(self.frm_palette)
        self.frm_palette.bind('<MouseWheel>', on_palette_mousewheel)

        # Initial generate
        self.on_source_change()
        self.generate()

    def on_source_change(self):
        mode = self.source_type.get()
        if mode == 'hex':
            # enable color picker button in HEX mode
            if hasattr(self, 'btn_color_picker'):
                self.btn_color_picker.state(['!disabled'])
            if hasattr(self, 'color_swatch'):
                self.color_swatch.config(state='normal')
            self.btn_select_img.state(['disabled'])
            # hide extracted swatches when switching to HEX mode
            self.hide_extracted_swatches()
        else:
            # disable color picker in image mode
            if hasattr(self, 'btn_color_picker'):
                self.btn_color_picker.state(['disabled'])
            if hasattr(self, 'color_swatch'):
                self.color_swatch.config(state='disabled')
            self.btn_select_img.state(['!disabled'])
            # if an image is already selected, show its extracted swatches
            if getattr(self, 'extracted_colors', None):
                self.show_extracted_swatches(self.extracted_colors)

    def select_image(self):
        # cleanup old temp screenshot file if it exists
        if getattr(self, '_temp_screenshot', None):
            try:
                os.unlink(self._temp_screenshot)
            except Exception:
                pass
            self._temp_screenshot = None

        path = filedialog.askopenfilename(title="이미지 선택", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All files","*.*")])
        if path:
            self.image_path = path
            name = os.path.basename(path)
            # truncate long filenames for display (append '...')
            max_len = 12
            if len(name) > max_len:
                name = name[:max_len-3] + '...'
            self.lbl_image.config(text=name)
            # create and show a small thumbnail image next to the filename
            try:
                img = Image.open(path)
                img.thumbnail((48, 48))
                photo = ImageTk.PhotoImage(img)
                self.img_thumbnail_label.config(image=photo)
                # keep a reference to avoid garbage collection
                self.img_thumbnail = photo
            except Exception:
                self.img_thumbnail_label.config(image='')
            # Do NOT extract colors immediately; wait for Generate button.
            self.extracted_colors = []

    def open_harmony_selector(self):
        """Open a dialog to select which color harmony schemes to display."""
        dialog = tk.Toplevel(self)
        dialog.title("색상 조합 선택")
        dialog.geometry("350x320")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="표시할 색상 조합을 선택하세요:", font=('Segoe UI', 10, 'bold')).pack(pady=10, padx=10, anchor='w')

        # Create a frame for checkboxes
        frm_checks = ttk.Frame(dialog)
        frm_checks.pack(padx=10, pady=5, fill='both', expand=True)

        # Define harmony schemes with labels
        schemes = [
            ('complementary', '보색 (Complementary)'),
            ('analogous', '유사색 (Analogous)'),
            ('triadic', '삼각 조화색 (Triadic)'),
            ('monochromatic', '단색 조화 (Monochromatic)'),
            ('split_complementary', '스플릿 보색 (Split-Complementary)'),
            ('square', '스퀘어 (Square)'),
            ('tetradic', '테트라딕 (Tetradic)'),
            ('double_complementary', '더블 보색 (Double-Complementary)')
        ]

        # Create checkbox variables
        scheme_vars = {}
        for scheme_key, scheme_label in schemes:
            var = tk.BooleanVar(value=(scheme_key in self.selected_schemes))
            scheme_vars[scheme_key] = var
            cb = ttk.Checkbutton(frm_checks, text=scheme_label, variable=var)
            cb.pack(anchor='w', pady=4)

        # Buttons
        frm_buttons = ttk.Frame(dialog)
        frm_buttons.pack(pady=10)

        def apply_selection():
            self.selected_schemes = [key for key, var in scheme_vars.items() if var.get()]
            if not self.selected_schemes:
                messagebox.showwarning('선택 오류', '최소 하나의 색상 조합을 선택해야 합니다.')
                return
            dialog.destroy()
            # Regenerate with new selection
            self.generate()

        def cancel():
            dialog.destroy()

        ttk.Button(frm_buttons, text="확인", command=apply_selection).grid(row=0, column=0, padx=5)
        ttk.Button(frm_buttons, text="취소", command=cancel).grid(row=0, column=1, padx=5)

    def _update_color_swatch(self, hex_color):
        """Update the color swatch canvas to show the selected color and display hex/RGB info."""
        try:
            # Delete previous rectangles
            self.color_swatch.delete("all")
            # Draw rectangle that fills the entire canvas (70x48)
            self.color_swatch.create_rectangle(0, 0, 70, 48, fill=hex_color, outline='', width=0)
        except tk.TclError:
            # fallback for invalid colors
            self.color_swatch.delete("all")
            self.color_swatch.create_rectangle(0, 0, 70, 48, fill="#ffffff", outline='', width=0)
            hex_color = "#ffffff"
        
        # Convert hex to RGB and update the info label
        try:
            rgb = self.generator.hex_to_rgb(hex_color)
            info_text = f"HEX: {hex_color}\nRGB: {rgb}"
            self.lbl_color_info.config(text=info_text)
        except Exception:
            self.lbl_color_info.config(text=f"HEX: {hex_color}\nRGB: (?, ?, ?)")

    def open_color_picker(self):
        """Open color chooser dialog and update the selected color."""
        # Get current color from hex_entry
        current_color = self.hex_entry.get()
        try:
            # colorchooser.askcolor returns ((R,G,B), '#RRGGBB')
            color_result = colorchooser.askcolor(color=current_color, title="색상 선택")
            if color_result[1]:  # if user didn't cancel
                hex_color = color_result[1]
                self.hex_entry.set(hex_color)
                self._update_color_swatch(hex_color)
        except Exception as e:
            messagebox.showerror("Color Picker Error", str(e))

    def start_screen_picker(self):
        """Begin screen color picker: make app transparent/hidden, capture screen,
        show fullscreen overlay and report color under mouse until click."""
        try:
            try:
                self._prev_alpha = self.attributes('-alpha')
            except Exception:
                self._prev_alpha = 1.0
            # attempt to make transparent
            try:
                self.attributes('-alpha', 0.0)
                self.update()
                self._did_withdraw = False
            except Exception:
                # fallback: withdraw
                try:
                    self.withdraw()
                    self._did_withdraw = True
                except Exception:
                    self._did_withdraw = False

            # allow transparency to apply, then capture
            self.after(120, self._capture_and_show_picker)
        except Exception as e:
            messagebox.showerror('Picker Error', str(e))

    def _capture_and_show_picker(self):
        # Try to grab all screens if Pillow supports it (multi-monitor setups)
        try:
            screen = ImageGrab.grab(all_screens=True)
        except TypeError:
            # older Pillow versions may not accept all_screens
            try:
                screen = ImageGrab.grab()
            except Exception as e:
                # restore UI
                try:
                    if getattr(self, '_did_withdraw', False):
                        self.deiconify()
                    else:
                        self.attributes('-alpha', self._prev_alpha)
                except Exception:
                    pass
                messagebox.showerror('Capture Error', f'Failed to capture screen: {e}')
                return
        except Exception as e:
            # restore UI
            try:
                if getattr(self, '_did_withdraw', False):
                    self.deiconify()
                else:
                    self.attributes('-alpha', self._prev_alpha)
            except Exception:
                pass
            messagebox.showerror('Capture Error', f'Failed to capture screen: {e}')
            return

        self._screen_image = screen
        img_w, img_h = screen.size

        # Determine virtual screen origin and size (Windows); fallback to captured image size
        x0 = 0
        y0 = 0
        width = img_w
        height = img_h
        try:
            if os.name == 'nt':
                import ctypes
                user32 = ctypes.windll.user32
                SM_XVIRTUALSCREEN = 76
                SM_YVIRTUALSCREEN = 77
                SM_CXVIRTUALSCREEN = 78
                SM_CYVIRTUALSCREEN = 79
                xv = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
                yv = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
                cvw = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
                cvh = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
                x0, y0, width, height = int(xv), int(yv), int(cvw), int(cvh)
        except Exception:
            x0, y0 = 0, 0
            width, height = img_w, img_h

        picker = tk.Toplevel(self)
        picker.overrideredirect(True)
        # set geometry to virtual screen coordinates so overlay covers all monitors
        try:
            picker.geometry(f"{width}x{height}+{x0}+{y0}")
        except Exception:
            try:
                picker.geometry(f"{img_w}x{img_h}+0+0")
            except Exception:
                pass
        try:
            picker.attributes('-topmost', True)
        except Exception:
            pass
        picker.lift()

        # Resize captured image to logical virtual screen size for correct on-screen display
        try:
            display_img = screen.resize((width, height))
        except Exception:
            display_img = screen

        photo = ImageTk.PhotoImage(display_img)
        # If in image-mode extraction, use rectangle selection; otherwise use pixel picker
        mode = self.source_type.get()
        if mode == 'image':
            # use canvas so we can draw selection rectangle
            canvas = tk.Canvas(picker, width=width, height=height, highlightthickness=0)
            canvas.photo = photo
            canvas.create_image(0, 0, image=photo, anchor='nw')
            canvas.pack(fill='both', expand=True)

            # state for rectangle selection
            canvas._rect_id = None
            canvas._start = None

            def on_press(e):
                # record start in root coords
                canvas._start = (e.x_root, e.y_root)
                # remove any existing rect
                if canvas._rect_id:
                    canvas.delete(canvas._rect_id)
                    canvas._rect_id = None

            def on_drag(e):
                if not canvas._start:
                    return
                x0_root, y0_root = canvas._start
                x1_root, y1_root = e.x_root, e.y_root
                # map to local display coords
                lx0 = int((x0_root - x0) * (width / max(1, width)))
                ly0 = int((y0_root - y0) * (height / max(1, height)))
                lx1 = int((x1_root - x0) * (width / max(1, width)))
                ly1 = int((y1_root - y0) * (height / max(1, height)))
                # draw rectangle
                if canvas._rect_id:
                    canvas.coords(canvas._rect_id, lx0, ly0, lx1, ly1)
                else:
                    canvas._rect_id = canvas.create_rectangle(lx0, ly0, lx1, ly1, outline='red', width=2)

            def on_release(e):
                if not canvas._start:
                    return
                x0_root, y0_root = canvas._start
                x1_root, y1_root = e.x_root, e.y_root
                # compute region in original image coords
                img_w, img_h = screen.size
                vw, vh = width, height
                scale_x = img_w / max(1, vw)
                scale_y = img_h / max(1, vh)
                sx = int((min(x0_root, x1_root) - x0) * scale_x)
                sy = int((min(y0_root, y1_root) - y0) * scale_y)
                ex = int((max(x0_root, x1_root) - x0) * scale_x)
                ey = int((max(y0_root, y1_root) - y0) * scale_y)
                # clamp
                sx = max(0, min(img_w - 1, sx))
                sy = max(0, min(img_h - 1, sy))
                ex = max(0, min(img_w, ex))
                ey = max(0, min(img_h, ey))
                if ex <= sx or ey <= sy:
                    # invalid
                    canvas._start = None
                    if canvas._rect_id:
                        canvas.delete(canvas._rect_id)
                        canvas._rect_id = None
                    return

                # crop region
                region = screen.crop((sx, sy, ex, ey))

                # save to temporary file for color extraction
                try:
                    temp_fd, temp_path = tempfile.mkstemp(suffix='.png')
                    os.close(temp_fd)  # close the file descriptor
                    region.save(temp_path)
                except Exception as e:
                    messagebox.showerror('Save Error', f'Failed to save screenshot region: {e}')
                    canvas._start = None
                    return

                # close picker
                try:
                    picker.destroy()
                except Exception:
                    pass

                # restore main window transparency / visibility
                try:
                    if getattr(self, '_did_withdraw', False):
                        self.deiconify()
                        self._did_withdraw = False
                    else:
                        # restore previous alpha if we changed it
                        try:
                            self.attributes('-alpha', self._prev_alpha)
                        except Exception:
                            pass
                except Exception:
                    pass

                # set thumbnail and label
                try:
                    # display small thumbnail from region (in-memory)
                    thumb = region.copy()
                    thumb.thumbnail((48,48))
                    photo_thumb = ImageTk.PhotoImage(thumb)
                    self.img_thumbnail_label.config(image=photo_thumb)
                    self.img_thumbnail = photo_thumb
                    self.lbl_image.config(text='**스크린샷**')
                    # set image_path to temp file so Generate can use it
                    self.image_path = temp_path
                    # store temp path for later cleanup
                    self._temp_screenshot = temp_path
                except Exception:
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass

                # extract colors from region using temp file (keep file for later Generate calls)
                try:
                    colors = self.generator.extract_main_colors(temp_path, num_colors=5)
                    self.extracted_colors = colors
                    # show extracted swatches in image mode
                    if self.source_type.get() == 'image':
                        self.show_extracted_swatches(colors)
                except Exception:
                    self.extracted_colors = []

            # bind events for rectangle selection (no HUD while selecting)
            canvas.bind('<Button-1>', on_press)
            canvas.bind('<B1-Motion>', on_drag)
            canvas.bind('<ButtonRelease-1>', on_release)
        else:
            lbl = tk.Label(picker, image=photo)
            lbl.image = photo
            lbl.place(x=0, y=0, width=width, height=height)

            floating = tk.Label(picker, text='', bd=1, relief='solid', padx=12, pady=8, font=('Segoe UI', 14, 'bold'))
            floating.place(x=20, y=20)

            self._picker_win = picker
            self._picker_floating = floating

            picker.bind('<Motion>', self._on_picker_move)
            picker.bind('<Button-1>', self._on_picker_click)

        # store virtual origin and size for coordinate mapping
        self._screen_origin = (x0, y0)
        self._virtual_size = (width, height)

        picker.focus_force()

    def _on_picker_move(self, event):
        x = event.x_root
        y = event.y_root
        img = self._screen_image
        x0, y0 = getattr(self, '_screen_origin', (0, 0))
        # Map global logical coordinates to original image pixel coordinates using scale
        img_w, img_h = img.size
        # virtual display size (may differ from captured image size)
        vw, vh = getattr(self, '_virtual_size', (img_w, img_h))
        vw = max(1, int(vw))
        vh = max(1, int(vh))
        scale_x = img_w / vw
        scale_y = img_h / vh

        local_x = int((x - x0) * scale_x)
        local_y = int((y - y0) * scale_y)
        w, h = img_w, img_h
        if local_x < 0 or local_y < 0 or local_x >= w or local_y >= h:
            return
        try:
            rgb = img.getpixel((local_x, local_y))
        except Exception:
            return
        if isinstance(rgb, int):
            rgb = (rgb, rgb, rgb)

        hx = self.generator.rgb_to_hex(rgb)
        lum = (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2])
        txt_fill = '#000000' if lum > 160 else '#ffffff'

        f = self._picker_floating
        f.config(text=hx, bg=hx, fg=txt_fill)

        # determine picker visible size
        try:
            vw = int(self._picker_win.winfo_width())
            vh = int(self._picker_win.winfo_height())
        except Exception:
            vw, vh = w, h

        midx = vw / 2
        midy = vh / 2

        pad = 8
        fw = f.winfo_reqwidth()
        fh = f.winfo_reqheight()

        # compute mouse position relative to virtual origin
        rel_x = x - x0
        rel_y = y - y0

        # determine quadrant of mouse (1=top-left,2=top-right,3=bottom-left,4=bottom-right)
        if rel_x <= midx and rel_y <= midy:
            quadrant = 1
        elif rel_x > midx and rel_y <= midy:
            quadrant = 2
        elif rel_x <= midx and rel_y > midy:
            quadrant = 3
        else:
            quadrant = 4

        # opposite quadrant mapping: 1<->4, 2<->3
        opp = {1:4, 2:3, 3:2, 4:1}[quadrant]

        if opp == 1:
            # top-left
            place_x = int(pad)
            place_y = int(pad)
        elif opp == 2:
            # top-right
            place_x = int(vw - pad - fw)
            place_y = int(pad)
        elif opp == 3:
            # bottom-left
            place_x = int(pad)
            place_y = int(vh - pad - fh)
        else:
            # bottom-right
            place_x = int(vw - pad - fw)
            place_y = int(vh - pad - fh)

        # clamp inside window
        place_x = max(4, min(place_x, vw - fw - 4))
        place_y = max(4, min(place_y, vh - fh - 4))
        f.place(x=place_x, y=place_y)

    def _on_picker_click(self, event):
        hx = self._picker_floating.cget('text')
        try:
            self._picker_win.destroy()
        except Exception:
            pass
        try:
            if getattr(self, '_did_withdraw', False):
                self.deiconify()
                self._did_withdraw = False
            else:
                self.attributes('-alpha', self._prev_alpha)
        except Exception:
            pass

        try:
            self.hex_entry.set(hx)
            self._update_color_swatch(hx)
            self.image_path = None
            self.extracted_colors = []
        except Exception:
            pass

    def save_palettes_txt(self):
        """Save current palettes as txt files under saves/txt."""
        if not getattr(self, 'current_palettes', None):
            messagebox.showwarning('No palettes', 'Generate a palette first before saving.')
            return

        dest_dir = os.path.join(self.saves_root, 'txt')
        now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        saved = []
        for i, p in enumerate(self.current_palettes, start=1):
            base_hex = self.generator.rgb_to_hex(p['base'])
            name = f"palette_{now}_{i}_{base_hex.lstrip('#')}.txt"
            path = os.path.join(dest_dir, name)
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(f"Palette {i}\n")
                    f.write(f"Base: {base_hex} | RGB: {p['base']}\n")
                    f.write('\n')
                    f.write(f"Complementary: {self.generator.rgb_to_hex(p['complementary'])} | RGB: {p['complementary']}\n")
                    f.write('\n')
                    f.write("Analogous:\n")
                    for col in p['analogous']:
                        f.write(f"  {self.generator.rgb_to_hex(col)} | RGB: {col}\n")
                    f.write('\n')
                    f.write("Triadic:\n")
                    for col in p['triadic']:
                        f.write(f"  {self.generator.rgb_to_hex(col)} | RGB: {col}\n")
                    f.write('\n')
                    f.write("Monochromatic:\n")
                    for col in p['monochromatic']:
                        f.write(f"  {self.generator.rgb_to_hex(col)} | RGB: {col}\n")
                saved.append(path)
            except Exception as e:
                messagebox.showerror('Save Error', f'Failed to save txt: {e}')
                return

        messagebox.showinfo('Saved', f'Saved {len(saved)} txt file(s) to {dest_dir}')

    def save_palettes_png(self):
        """Save current palettes as PNG images under saves/png.

        Each palette is saved as a horizontal row of swatches (base + complementary + analogous + triadic + monochromatic).
        """
        if not getattr(self, 'current_palettes', None):
            messagebox.showwarning('No palettes', 'Generate a palette first before saving.')
            return

        from PIL import ImageDraw

        dest_dir = os.path.join(self.saves_root, 'png')
        now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        saved = []
        for i, p in enumerate(self.current_palettes, start=1):
            # build swatch list
            swatches = [p['base']]
            # complementary is a single rgb
            swatches.append(p['complementary'])
            # analogous, triadic, monochromatic are lists
            swatches.extend(p['analogous'])
            swatches.extend(p['triadic'])
            swatches.extend(p['monochromatic'])

            sw_w = 100
            sw_h = 100
            padding = 4
            cols = len(swatches)
            img_w = cols * (sw_w + padding) + padding
            img_h = sw_h + padding * 2
            img = Image.new('RGB', (img_w, img_h), (255,255,255))
            draw = ImageDraw.Draw(img)
            x = padding
            for rgb in swatches:
                hx = self.generator.rgb_to_hex(rgb)
                draw.rectangle([x, padding, x + sw_w, padding + sw_h], fill=hx)
                x += sw_w + padding

            base_hex = self.generator.rgb_to_hex(p['base'])
            name = f"palette_{now}_{i}_{base_hex.lstrip('#')}.png"
            path = os.path.join(dest_dir, name)
            try:
                img.save(path)
                saved.append(path)
            except Exception as e:
                messagebox.showerror('Save Error', f'Failed to save png: {e}')
                return

        messagebox.showinfo('Saved', f'Saved {len(saved)} png file(s) to {dest_dir}')

    def new_pgf(self):
        """Create a new PGF workspace."""
        # Ask to save if modified
        if self.is_modified:
            response = messagebox.askyesnocancel('저장', '현재 작업을 저장하시겠습니까?')
            if response is None:  # Cancel
                return
            elif response:  # Yes
                saved = self.save_pgf()
                if not saved:  # User cancelled save dialog
                    return
        
        # Reset to default state
        self.saved_palettes = [{'name': '새 팔레트1', 'colors': []}]
        self.selected_schemes = ['complementary', 'analogous', 'triadic', 'monochromatic']
        self.source_type.set('hex')
        self.hex_entry.set('#3498db')
        self.current_palettes = []
        self._saved_counter = 1
        self._saved_selected = 0
        self.current_file = None
        
        # Update UI
        self._update_color_swatch('#3498db')
        self.on_source_change()
        self.render_saved_list()
        self.clear_palette_display()
        # Don't call generate() to avoid marking as modified
        # User can manually generate when needed
        
        # Now mark as not modified AFTER UI updates
        self.is_modified = False
        self.update_title()
        self.log_action("Created new workspace")

    def update_title(self):
        """Update window title with filename and modified state."""
        base_title = "Color Palette Generator"
        if self.current_file:
            filename = os.path.basename(self.current_file)
            title = f"{base_title} - {filename}"
        else:
            title = f"{base_title} - 제목없음"
        
        if self.is_modified:
            title += " *"
        
        self.title(title)

    def mark_modified(self):
        """Mark workspace as modified."""
        if not self.is_modified:
            self.is_modified = True
            self.update_title()

    def save_pgf(self):
        """Save entire workspace state to encrypted PGF file. Returns True if saved, False if cancelled."""
        # If file already exists, save directly without dialog
        if self.current_file:
            return self._save_to_file(self.current_file)
        else:
            # No current file, behave like Save As
            return self.save_pgf_as()
    
    def save_pgf_as(self):
        """Save As: Always prompt for new file location. Disabled if no current file."""
        try:
            # Disabled if no file is being worked on
            if not self.current_file and not self.is_modified:
                return False
            
            path = filedialog.asksaveasfilename(
                title='Save As...', 
                initialdir=self.saves_root,
                defaultextension='.pgf', 
                filetypes=[('PGF file', '*.pgf')]
            )
            if not path:
                return False
            
            result = self._save_to_file(path)
            if result:
                self.log_action(f"Saved workspace as: {path}")
            return result
        except Exception as e:
            messagebox.showerror('Save Error', f'Failed to save: {str(e)}')
            self.log_action(f"Save As failed: {str(e)}")
            return False
    
    def _save_to_file(self, path):
        """Internal method to save workspace to a specific file path using AES encryption."""
        try:
            import json
            
            # Collect all workspace state
            workspace_data = {
                'saved_palettes': self.saved_palettes,
                'selected_schemes': self.selected_schemes,
                'source_type': self.source_type.get(),
                'hex_entry': self.hex_entry.get(),
                'current_palettes': getattr(self, 'current_palettes', []),
                'saved_counter': self._saved_counter,
                'saved_selected': self._saved_selected
            }
            
            # Encrypt and save using AES
            data_json = json.dumps(workspace_data)
            encrypted = self._encrypt_aes(data_json)
            
            with open(path, 'wb') as f:
                f.write(encrypted)
            
            # Update state
            self.current_file = path
            self.is_modified = False
            self.update_title()
            
            # Add to recent files
            self.add_recent_file(path)
            messagebox.showinfo('Saved', f'Workspace saved to {path}')
            self.log_action(f"Saved workspace: {path}")
            return True
        except Exception as e:
            messagebox.showerror('Save Error', f'Failed to save: {str(e)}')
            self.log_action(f"Save failed: {str(e)}")
            return False
    
    def load_pgf(self):
        """Load workspace state from encrypted PGF file."""
        try:
            path = filedialog.askopenfilename(
                title='Open PGF...', 
                initialdir=self.saves_root,
                filetypes=[('PGF file', '*.pgf')]
            )
            if not path:
                return
            
            import json
            
            # Read and decrypt using AES
            with open(path, 'rb') as f:
                encrypted = f.read()
            
            data_json = self._decrypt_aes(encrypted)
            workspace_data = json.loads(data_json)
            
            # Restore workspace state
            self.saved_palettes = workspace_data.get('saved_palettes', [])
            self.selected_schemes = workspace_data.get('selected_schemes', ['complementary', 'analogous', 'triadic', 'monochromatic'])
            self.source_type.set(workspace_data.get('source_type', 'hex'))
            self.hex_entry.set(workspace_data.get('hex_entry', '#3498db'))
            self.current_palettes = workspace_data.get('current_palettes', [])
            self._saved_counter = workspace_data.get('saved_counter', 0)
            self._saved_selected = workspace_data.get('saved_selected', None)
            
            # Update UI
            self._update_color_swatch(self.hex_entry.get())
            self.on_source_change()
            self.render_saved_list()
            if self.current_palettes:
                self.clear_palette_display()
                # Re-render current palettes
                source_type = self.source_type.get()
                if source_type == 'hex' and self.current_palettes:
                    palette = self.current_palettes[0]
                    self.display_single_palette(palette)
                elif source_type == 'image' and self.current_palettes:
                    self.display_multiple_palettes(self.current_palettes)
            
            # Update state
            self.current_file = path
            self.is_modified = False
            self.update_title()
            
            # Add to recent files
            self.add_recent_file(path)
            messagebox.showinfo('Loaded', f'Workspace loaded from {path}')
            self.log_action(f"Loaded workspace: {path}")
        except Exception as e:
            messagebox.showerror('Load Error', f'Failed to load: {str(e)}')
            self.log_action(f"Load failed: {str(e)}")
    
    def _get_encryption_key(self):
        """Generate a consistent encryption key based on a fixed passphrase."""
        passphrase = "ColorPaletteGenerator2025SecretKey"
        key = hashlib.sha256(passphrase.encode()).digest()
        # Fernet requires base64-encoded 32-byte key
        import base64
        return base64.urlsafe_b64encode(key)
    
    def _encrypt_aes(self, data):
        """Encrypt data using AES (Fernet)."""
        key = self._get_encryption_key()
        f = Fernet(key)
        return f.encrypt(data.encode('utf-8'))
    
    def _decrypt_aes(self, encrypted_data):
        """Decrypt data using AES (Fernet)."""
        key = self._get_encryption_key()
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode('utf-8')
    
    def setup_logging(self):
        """Setup logging to file in Temp directory."""
        temp_dir = os.path.join(os.path.dirname(__file__), 'Temp')
        os.makedirs(temp_dir, exist_ok=True)
        log_file = os.path.join(temp_dir, 'app.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_action(self, action):
        """Log an action to the log file."""
        try:
            self.logger.info(action)
        except Exception:
            pass
    
    def on_closing(self):
        """Handle window close event - ask to save if modified."""
        if self.is_modified:
            response = messagebox.askyesnocancel(
                '저장', 
                '현재 작업이 수정되었습니다. 저장하시겠습니까?'
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                saved = self.save_pgf()
                if not saved:
                    return
        
        self.log_action("Application closed")
        self.destroy()
    
    def get_temp_dir(self):
        """Get or create Temp directory for app data."""
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Temp')
        try:
            os.makedirs(temp_dir, exist_ok=True)
        except Exception:
            pass
        return temp_dir
    
    def get_recent_files_path(self):
        """Get path to recent files list."""
        return os.path.join(self.get_temp_dir(), 'recent.dat')
    
    def load_recent_files(self):
        """Load recent files list from encrypted file."""
        try:
            import json
            
            path = self.get_recent_files_path()
            if not os.path.exists(path):
                return []
            
            with open(path, 'rb') as f:
                encrypted = f.read()
            
            data = self._decrypt_aes(encrypted)
            recent_files = json.loads(data)
            
            # Filter out non-existent files
            return [f for f in recent_files if os.path.exists(f)]
        except Exception:
            return []
    
    def save_recent_files(self, recent_files):
        """Save recent files list to encrypted file."""
        try:
            import json
            
            data = json.dumps(recent_files)
            encrypted = self._encrypt_aes(data)
            
            path = self.get_recent_files_path()
            with open(path, 'wb') as f:
                f.write(encrypted)
        except Exception:
            pass
    
    def add_recent_file(self, filepath):
        """Add file to recent files list (max 10)."""
        recent_files = self.load_recent_files()
        
        # Remove if already exists
        if filepath in recent_files:
            recent_files.remove(filepath)
        
        # Add to front
        recent_files.insert(0, filepath)
        
        # Keep only last 10
        recent_files = recent_files[:10]
        
        self.save_recent_files(recent_files)
        self.update_recent_menu()
    
    def update_recent_menu(self):
        """Update the Open Recent submenu."""
        try:
            self.recent_menu.delete(0, tk.END)
            
            recent_files = self.load_recent_files()
            
            if not recent_files:
                self.recent_menu.add_command(label='(No recent files)', state='disabled')
            else:
                for filepath in recent_files:
                    filename = os.path.basename(filepath)
                    self.recent_menu.add_command(
                        label=filename,
                        command=lambda p=filepath: self.load_recent_file(p)
                    )
        except Exception:
            pass
    
    def load_recent_file(self, filepath):
        """Load a file from recent files list."""
        if not os.path.exists(filepath):
            messagebox.showerror('Error', f'File not found: {filepath}')
            return
        
        try:
            import json
            import base64
            
            with open(filepath, 'r', encoding='utf-8') as f:
                encoded = f.read()
            
            data_json = base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
            workspace_data = json.loads(data_json)
            
            # Restore workspace state
            self.saved_palettes = workspace_data.get('saved_palettes', [])
            self.selected_schemes = workspace_data.get('selected_schemes', ['complementary', 'analogous', 'triadic', 'monochromatic'])
            self.source_type.set(workspace_data.get('source_type', 'hex'))
            self.hex_entry.set(workspace_data.get('hex_entry', '#3498db'))
            self.current_palettes = workspace_data.get('current_palettes', [])
            self._saved_counter = workspace_data.get('saved_counter', 0)
            self._saved_selected = workspace_data.get('saved_selected', None)
            
            # Update UI
            self._update_color_swatch(self.hex_entry.get())
            self.on_source_change()
            self.render_saved_list()
            if self.current_palettes:
                self.clear_palette_display()
                source_type = self.source_type.get()
                if source_type == 'hex' and self.current_palettes:
                    palette = self.current_palettes[0]
                    self.display_single_palette(palette)
                elif source_type == 'image' and self.current_palettes:
                    self.display_multiple_palettes(self.current_palettes)
            
            # Update state
            self.current_file = filepath
            self.is_modified = False
            self.update_title()
            
            self.add_recent_file(filepath)
        except Exception as e:
            messagebox.showerror('Load Error', f'Failed to load: {str(e)}')

    def save_palettes_to_single_txt(self, path):
        """Save all current palettes into a single text file at `path`."""
        with open(path, 'w', encoding='utf-8') as f:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"Palettes exported: {now}\n\n")
            for i, p in enumerate(self.current_palettes, start=1):
                base_hex = self.generator.rgb_to_hex(p['base'])
                f.write(f"Palette {i}\n")
                f.write(f"Base: {base_hex} | RGB: {p['base']}\n")
                f.write(f"  Complementary: {self.generator.rgb_to_hex(p['complementary'])} | RGB: {p['complementary']}\n")
                f.write('  Analogous:\n')
                for idx, col in enumerate(p['analogous'], 1):
                    f.write(f"    {idx}. {self.generator.rgb_to_hex(col)} | RGB: {col}\n")
                f.write('  Triadic:\n')
                for idx, col in enumerate(p['triadic'], 1):
                    f.write(f"    {idx}. {self.generator.rgb_to_hex(col)} | RGB: {col}\n")
                f.write('  Monochromatic:\n')
                for idx, col in enumerate(p['monochromatic'], 1):
                    f.write(f"    {idx}. {self.generator.rgb_to_hex(col)} | RGB: {col}\n")
                f.write('\n')

    def save_palettes_to_single_png(self, path):
        """Save all current palettes into a single PNG image with category labels and hex codes."""
        from PIL import ImageDraw, ImageFont

        palettes = self.current_palettes
        # build flattened swatch lists with category labels for each palette
        palette_rows = []
        for i, p in enumerate(palettes, start=1):
            row = []
            # base
            row.append(('Base', p['base']))
            # complementary
            row.append(('Complementary', p['complementary']))
            # analogous
            for idx, col in enumerate(p['analogous'], 1):
                row.append((f'Analogous {idx}', col))
            # triadic
            for idx, col in enumerate(p['triadic'], 1):
                row.append((f'Triadic {idx}', col))
            # monochromatic
            for idx, col in enumerate(p['monochromatic'], 1):
                row.append((f'Monochromatic {idx}', col))
            palette_rows.append((f'Palette {i}', row))

        # layout
        sw_w = 140
        sw_h = 100
        pad = 8
        # compute max columns
        max_cols = max(len(r[1]) for r in palette_rows)
        img_w = pad + max_cols * (sw_w + pad)
        # height: for each palette, have title area + swatch height + label areas
        title_h = 24
        label_h = 18
        row_h = title_h + sw_h + label_h + pad
        img_h = pad + len(palette_rows) * row_h

        img = Image.new('RGB', (img_w, img_h), (250,250,250))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        y = pad
        for title, row in palette_rows:
            # draw palette title
            draw.text((pad, y), title, fill=(0,0,0), font=font)
            y += title_h

            x = pad
            for label, rgb in row:
                hx = self.generator.rgb_to_hex(rgb)
                # draw swatch
                draw.rectangle([x, y, x + sw_w, y + sw_h], fill=hx)
                # category label above swatch
                draw.text((x + 4, y + sw_h + 2), label, fill=(0,0,0), font=font)
                # hex code overlay: choose contrasting color
                lum = (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2])
                txt_fill = (0,0,0) if lum > 160 else (255,255,255)
                # measure text size (robust across Pillow versions)
                try:
                    hex_w, hex_h = draw.textsize(hx, font=font)
                except Exception:
                    try:
                        hex_w, hex_h = font.getsize(hx)
                    except Exception:
                        # final fallback: use textbbox if available
                        try:
                            bbox = draw.textbbox((0,0), hx, font=font)
                            hex_w = bbox[2] - bbox[0]
                            hex_h = bbox[3] - bbox[1]
                        except Exception:
                            hex_w, hex_h = (len(hx) * 6, 10)

                tx = x + (sw_w - hex_w) / 2
                ty = y + sw_h/2 - hex_h/2
                draw.text((tx, ty), hx, fill=txt_fill, font=font)

                x += sw_w + pad

            y += sw_h + label_h + pad

        img.save(path)

    def generate_random(self):
        """랜덤 색상을 생성하여 HEX 입력란에 채우고 팔레트를 생성합니다."""
        # Ensure we're in HEX mode
        self.source_type.set('hex')
        self.on_source_change()

        rgb = self.generator.generate_random_color()
        hex_code = self.generator.rgb_to_hex(rgb)
        # hex_entry is a StringVar now
        try:
            self.hex_entry.set(hex_code)
        except Exception:
            pass
        # update swatch and trigger generation
        try:
            self._update_color_swatch(hex_code)
        except Exception:
            pass
        self.generate()

    def clear_palette_display(self):
        for child in self.palette_inner.winfo_children():
            child.destroy()

    def draw_color_box(self, parent, hex_color, label_text, clickable=True):
        # Use regular Frame instead of ttk.Frame so we can set background color
        frm = tk.Frame(parent, bg='white')
        frm.pack(fill='x', pady=0, padx=0)

        # Extended canvas width to reach near scrollbar
        canvas = tk.Canvas(frm, width=220, height=50, bd=0, relief='solid', highlightthickness=0, cursor='hand2', bg='white')
        canvas.pack(side='left', padx=0, pady=0)
        
        # Draw initial color
        try:
            rect_id = canvas.create_rectangle(0, 0, 220, 50, fill=hex_color, outline='', width=0)
        except tk.TclError:
            rect_id = canvas.create_rectangle(0, 0, 220, 50, fill="#ffffff", outline='', width=0)
        
        # Hover effect: change entire frame background to light blue
        def on_enter(e):
            try:
                frm.config(bg='#ADD8E6')  # light blue
                canvas.config(bg='#ADD8E6')
                lbl.config(background='#ADD8E6')
            except Exception:
                pass
        
        def on_leave(e):
            try:
                frm.config(bg='white')
                canvas.config(bg='white')
                lbl.config(background='white')
            except Exception:
                pass
        
        frm.bind('<Enter>', on_enter)
        frm.bind('<Leave>', on_leave)
        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)

        # clicking a color swatch should try to add the color to the selected saved palette
        if clickable:
            try:
                canvas.bind('<Button-1>', lambda e, hx=hex_color: self.on_palette_color_click(hx))
            except Exception:
                pass

        # Use regular Label instead of ttk.Label for background control
        lbl = tk.Label(frm, text=f"{label_text}\n{hex_color}", bg='white', cursor='hand2')
        lbl.pack(side='left', padx=10)
        lbl.bind('<Enter>', on_enter)
        lbl.bind('<Leave>', on_leave)
        
        # Make label clickable too
        if clickable:
            try:
                lbl.bind('<Button-1>', lambda e, hx=hex_color: self.on_palette_color_click(hx))
            except Exception:
                pass
        
        # Bind scroll handler to new widgets
        if hasattr(self, '_palette_scroll_handler'):
            try:
                frm.bind('<MouseWheel>', self._palette_scroll_handler, add='+')
                canvas.bind('<MouseWheel>', self._palette_scroll_handler, add='+')
                lbl.bind('<MouseWheel>', self._palette_scroll_handler, add='+')
            except Exception:
                pass

    # --- Saved palettes management ---
    def add_saved_palette(self):
        """Add a new saved palette entry (start empty) and render the saved list.

        Do NOT auto-preview or auto-select the new palette; user must click it to select.
        """
        name = f"새 팔레트{self._saved_counter + 1}"
        self._saved_counter += 1

        entry = {'name': name, 'colors': []}
        self.saved_palettes.append(entry)
        # do not auto-select or preview; just re-render to show the new empty palette
        self.render_saved_list()
        self.mark_modified()
        self.log_action(f"Added new palette: {name}")

    def remove_saved_palette(self):
        # 항상 최소 1개 팔레트 이상 유지
        if len(self.saved_palettes) <= 1:
            messagebox.showinfo('최소 유지', '최소 1개의 팔레트는 유지되어야 합니다.')
            return
        if self._saved_selected is None:
            return
        idx = self._saved_selected
        palette_name = self.saved_palettes[idx]['name'] if idx < len(self.saved_palettes) else 'Unknown'
        try:
            del self.saved_palettes[idx]
        except Exception:
            return
        # adjust selection
        if not self.saved_palettes:
            self._saved_selected = None
        else:
            self._saved_selected = max(0, idx - 1)
        self.render_saved_list()
        self.log_action(f"Removed palette: {palette_name}")
        self.mark_modified()

    def on_saved_select(self):
        # kept for backward compatibility; selection is handled by render callbacks
        return

    def preview_saved_palette(self, entry):
        """Preview a saved palette in the main palette area (non-destructive)."""
        # Clear current display but keep saved palettes intact
        for w in self.palette_inner.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        ttk.Label(self.palette_inner, text=entry.get('name', '저장된 팔레트'), font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        sw_frame = ttk.Frame(self.palette_inner)
        sw_frame.pack(fill='x', pady=(6,0))
        for c in entry.get('colors', []):
            try:
                hx = c if isinstance(c, str) else self.generator.rgb_to_hex(c)
            except Exception:
                hx = '#ffffff'
            box = tk.Canvas(sw_frame, width=48, height=48, highlightthickness=0, bd=0)
            box.create_rectangle(0,0,48,48, fill=hx, outline=hx)
            box.pack(side='left', padx=2)

    def on_palette_color_click(self, hex_color):
        """Handle clicks on palette swatches: add color to currently selected saved palette."""
        if self._saved_selected is None:
            messagebox.showinfo('선택 필요', '먼저 오른쪽에서 저장된 팔레트를 선택하세요.')
            return
        try:
            entry = self.saved_palettes[self._saved_selected]
            # append color (store as hex)
            hx = hex_color if isinstance(hex_color, str) else self.generator.rgb_to_hex(hex_color)
            entry['colors'].append(hx)
            # re-render saved list to update the visual bar
            self.render_saved_list()
            self.mark_modified()
            self.log_action(f"Added color {hx} to palette: {entry['name']}")
        except Exception:
            pass

    def render_saved_list(self):
        """Rebuild the saved palettes UI in the right panel with light blue highlight for selected."""
        for c in self.saved_list_container.winfo_children():
            try:
                c.destroy()
            except Exception:
                pass

        for idx, entry in enumerate(self.saved_palettes):
            # Use light blue background if selected
            if self._saved_selected == idx:
                ef = tk.Frame(self.saved_list_container, bg='#ADD8E6')  # light blue
            else:
                ef = tk.Frame(self.saved_list_container, bg='white')
            ef.pack(fill='x', pady=4, padx=2)
            # header with name
            lbl = ttk.Label(ef, text=entry.get('name', f'팔레트{idx+1}'))
            if self._saved_selected == idx:
                lbl.config(background='#ADD8E6')  # light blue
            else:
                lbl.config(background='white')
            lbl.pack(fill='x')
            # clickable area to select this saved palette
            def make_select(i):
                return lambda e=None: self._select_saved_entry(i)
            ef.bind('<Button-1>', make_select(idx))
            lbl.bind('<Button-1>', make_select(idx))

            # right-click context menu
            def make_context_menu(i):
                return lambda e: self.show_palette_context_menu(i, e)
            ef.bind('<Button-3>', make_context_menu(idx))
            lbl.bind('<Button-3>', make_context_menu(idx))

            # color bar: create N equally sized frames or checkerboard if empty
            bar_container = tk.Frame(ef)
            bar_container.pack(fill='x', pady=(4,0), padx=0)
            colors = entry.get('colors', [])
            view_mode = entry.get('view_mode', 'rgb')
            
            if not colors:
                # Draw checkerboard pattern for empty palette
                bar_canvas = tk.Canvas(bar_container, height=28, highlightthickness=0)
                bar_canvas.pack(fill='x')
                
                def make_checkerboard_drawer(canvas):
                    def draw():
                        canvas.delete('all')
                        width = canvas.winfo_width()
                        if width < 10:
                            width = 200
                        square_size = 8
                        for y in range(0, 28, square_size):
                            for x in range(0, width, square_size):
                                if (x // square_size + y // square_size) % 2 == 0:
                                    canvas.create_rectangle(x, y, x+square_size, y+square_size, fill='#cccccc', outline='')
                                else:
                                    canvas.create_rectangle(x, y, x+square_size, y+square_size, fill='#ffffff', outline='')
                    return draw
                
                drawer = make_checkerboard_drawer(bar_canvas)
                bar_canvas.bind('<Configure>', lambda e, d=drawer: d())
                bar_canvas.after(10, drawer)
            else:
                bar = tk.Frame(bar_container)
                bar.pack(fill='x')
                display_colors = colors
                if view_mode == 'value':
                    # Convert to grayscale using luminance
                    display_colors = []
                    for c in colors:
                        lum = self.get_luminance(c)
                        gray_val = int(lum * 255)
                        display_colors.append(f'#{gray_val:02x}{gray_val:02x}{gray_val:02x}')
                for c in display_colors:
                    f = tk.Frame(bar, bg=c, height=28)
                    f.pack(side='left', fill='both', expand=True)
        
        # Rebind scroll events to new widgets
        if hasattr(self, '_saved_scroll_handler'):
            def bind_scroll_recursive(widget):
                try:
                    widget.bind('<MouseWheel>', self._saved_scroll_handler, add='+')
                    for child in widget.winfo_children():
                        bind_scroll_recursive(child)
                except Exception:
                    pass
            bind_scroll_recursive(self.saved_list_container)

    def _select_saved_entry(self, idx):
        self._saved_selected = idx
        # do not clear main palette display; just re-render the saved list to show selection highlight
        self.render_saved_list()

    def show_palette_context_menu(self, idx, event):
        """Show context menu for palette operations."""
        self._saved_selected = idx
        self.render_saved_list()
        
        entry = self.saved_palettes[idx]
        current_mode = entry.get('view_mode', 'rgb')
        view_label = 'RGB로 보기' if current_mode == 'value' else '밸류로 보기'
        
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label='이름 바꾸기', command=lambda: self.rename_palette(idx))
        menu.add_command(label='팔레트 편집', command=lambda: self.open_palette_editor(idx))
        menu.add_command(label='팔레트 저장', command=lambda: self.save_palette_file(idx))
        menu.add_separator()
        menu.add_command(label='TXT로 내보내기', command=lambda: self.export_palette_txt(idx))
        menu.add_command(label='PNG로 내보내기', command=lambda: self.export_palette_png(idx))
        menu.add_separator()
        menu.add_command(label=view_label, command=lambda: self.toggle_palette_view(idx))
        
        try:
            menu.post(event.x_root, event.y_root)
        except Exception:
            pass

    def rename_palette(self, idx):
        """Allow inline editing of palette name."""
        try:
            entry = self.saved_palettes[idx]
            old_name = entry['name']
            
            # Create a simple dialog for renaming
            dialog = tk.Toplevel(self)
            dialog.title('이름 바꾸기')
            dialog.geometry('300x130')
            dialog.resizable(False, False)
            dialog.transient(self)
            dialog.grab_set()
            
            ttk.Label(dialog, text='새 이름:').pack(pady=(10,5))
            entry_name = ttk.Entry(dialog)
            entry_name.pack(padx=10, pady=5, fill='x')
            entry_name.insert(0, old_name)
            entry_name.focus()
            entry_name.select_range(0, len(old_name))
            
            def save_name():
                new_name = entry_name.get().strip()
                if new_name:
                    self.saved_palettes[idx]['name'] = new_name
                    self.render_saved_list()
                    self.mark_modified()
                dialog.destroy()
            
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(pady=10)
            ttk.Button(btn_frame, text='확인', command=save_name).pack(side='left', padx=5)
            ttk.Button(btn_frame, text='취소', command=dialog.destroy).pack(side='left', padx=5)
        except Exception as e:
            messagebox.showerror('오류', str(e))

    def open_palette_editor(self, idx):
        """Open editor window for palette colors."""
        try:
            entry = self.saved_palettes[idx]
            editor_dialog = tk.Toplevel(self)
            editor_dialog.title(f'팔레트 편집 - {entry["name"]}')
            editor_dialog.geometry('600x150')
            editor_dialog.resizable(True, True)
            editor_dialog.transient(self)
            editor_dialog.grab_set()
            
            # Store working copy of colors (empty list if no colors)
            working_colors = entry['colors'].copy() if entry['colors'] else []
            selected_color_idx = [None]  # use list to make it mutable in nested functions
            hover_color_idx = [None]  # track hover state
            
            # Top: color bar display (with padding)
            bar_container = tk.Frame(editor_dialog, bg='#f0f0f0')
            bar_container.pack(fill='x', expand=False, padx=10, pady=(10,5))
            self.palette_editor_bar = tk.Canvas(bar_container, bg='white', height=50, highlightthickness=0)
            self.palette_editor_bar.pack(fill='x', expand=False)
            
            def draw_checkerboard(canvas, width, height, square_size=10):
                """Draw a checkerboard pattern for empty palette."""
                for y in range(0, height, square_size):
                    for x in range(0, width, square_size):
                        if (x // square_size + y // square_size) % 2 == 0:
                            canvas.create_rectangle(x, y, x+square_size, y+square_size, fill='#cccccc', outline='')
                        else:
                            canvas.create_rectangle(x, y, x+square_size, y+square_size, fill='#ffffff', outline='')
            
            def draw_colors():
                self.palette_editor_bar.delete('all')
                canvas_width = self.palette_editor_bar.winfo_width()
                if canvas_width < 100:
                    canvas_width = 600
                
                if not working_colors:
                    # Draw checkerboard pattern for empty palette
                    draw_checkerboard(self.palette_editor_bar, canvas_width, 50)
                    return
                
                canvas_width = self.palette_editor_bar.winfo_width()
                if canvas_width < 100:
                    canvas_width = 600
                
                box_width = canvas_width / len(working_colors)
                
                for i, color in enumerate(working_colors):
                    x0 = i * box_width
                    x1 = (i + 1) * box_width
                    
                    # Draw color box
                    self.palette_editor_bar.create_rectangle(x0, 0, x1, 50, fill=color, outline='')
                    
                    # Draw hover border (darker/lighter based on luminance)
                    if hover_color_idx[0] == i:
                        lum = self.get_luminance(color)
                        hover_border = '#000000' if lum > 128 else '#ffffff'
                        self.palette_editor_bar.create_rectangle(x0+1, 1, x1-1, 49, outline=hover_border, width=1)
                    
                    # Draw selection border (complementary color)
                    if selected_color_idx[0] == i:
                        lum = self.get_luminance(color)
                        # Get complementary border color
                        rgb = self.generator.hex_to_rgb(color)
                        comp_rgb = tuple(255 - c for c in rgb)
                        comp_color = self.generator.rgb_to_hex(comp_rgb)
                        self.palette_editor_bar.create_rectangle(x0+1, 1, x1-1, 49, outline=comp_color, width=2)
            
            # Drag-and-drop state
            drag_state = {'dragging': False, 'start_idx': None, 'current_idx': None}
            
            # Bind canvas events
            def on_canvas_press(e):
                if not working_colors:
                    return
                canvas_width = self.palette_editor_bar.winfo_width()
                box_width = canvas_width / len(working_colors)
                clicked_idx = int(e.x / box_width)
                clicked_idx = max(0, min(clicked_idx, len(working_colors) - 1))
                
                # Start drag operation
                drag_state['dragging'] = True
                drag_state['start_idx'] = clicked_idx
                drag_state['current_idx'] = clicked_idx
                
                selected_color_idx[0] = clicked_idx
                draw_colors()
                update_button_states()
            
            def on_canvas_drag(e):
                if not working_colors or not drag_state['dragging']:
                    # Just update hover if not dragging
                    if working_colors and not drag_state['dragging']:
                        canvas_width = self.palette_editor_bar.winfo_width()
                        box_width = canvas_width / len(working_colors)
                        hovered_idx = int(e.x / box_width)
                        hovered_idx = max(0, min(hovered_idx, len(working_colors) - 1))
                        if hover_color_idx[0] != hovered_idx:
                            hover_color_idx[0] = hovered_idx
                            draw_colors()
                    return
                
                canvas_width = self.palette_editor_bar.winfo_width()
                box_width = canvas_width / len(working_colors)
                current_idx = int(e.x / box_width)
                current_idx = max(0, min(current_idx, len(working_colors) - 1))
                
                if current_idx != drag_state['current_idx']:
                    # Swap colors during drag
                    start = drag_state['start_idx']
                    current = drag_state['current_idx']
                    
                    # Move from current position to new position
                    color = working_colors.pop(current)
                    working_colors.insert(current_idx, color)
                    
                    drag_state['current_idx'] = current_idx
                    selected_color_idx[0] = current_idx
                    draw_colors()
            
            def on_canvas_release(e):
                if drag_state['dragging']:
                    drag_state['dragging'] = False
                    drag_state['start_idx'] = None
                    drag_state['current_idx'] = None
                    draw_colors()
            
            def on_canvas_motion(e):
                if not drag_state['dragging'] and working_colors:
                    canvas_width = self.palette_editor_bar.winfo_width()
                    box_width = canvas_width / len(working_colors)
                    hovered_idx = int(e.x / box_width)
                    hovered_idx = max(0, min(hovered_idx, len(working_colors) - 1))
                    if hover_color_idx[0] != hovered_idx:
                        hover_color_idx[0] = hovered_idx
                        draw_colors()
            
            def on_canvas_leave(e):
                if not drag_state['dragging'] and hover_color_idx[0] is not None:
                    hover_color_idx[0] = None
                    draw_colors()
            
            self.palette_editor_bar.bind('<Button-1>', on_canvas_press)
            self.palette_editor_bar.bind('<B1-Motion>', on_canvas_drag)
            self.palette_editor_bar.bind('<ButtonRelease-1>', on_canvas_release)
            self.palette_editor_bar.bind('<Motion>', on_canvas_motion)
            self.palette_editor_bar.bind('<Leave>', on_canvas_leave)
            self.palette_editor_bar.bind('<Configure>', lambda e: draw_colors())
            editor_dialog.after(100, draw_colors)
            
            # Bottom: buttons
            btn_frame = tk.Frame(editor_dialog)
            btn_frame.pack(fill='x', padx=10, pady=(5,5))
            
            def add_color():
                color_result = colorchooser.askcolor(title='색상 추가')
                if color_result[1]:
                    hex_color = color_result[1]
                    if selected_color_idx[0] is not None and working_colors:
                        working_colors.insert(selected_color_idx[0], hex_color)
                    else:
                        working_colors.append(hex_color)
                    draw_colors()
                    update_button_states()
            
            def delete_color():
                if selected_color_idx[0] is not None and working_colors:
                    working_colors.pop(selected_color_idx[0])
                    selected_color_idx[0] = max(0, selected_color_idx[0] - 1) if working_colors else None
                    draw_colors()
                    update_button_states()
            
            def confirm():
                entry['colors'] = working_colors.copy()
                self.render_saved_list()
                self.mark_modified()
                editor_dialog.destroy()
            
            def update_button_states():
                # Enable/disable buttons based on selection
                # Allow adding colors even if nothing is selected
                add_btn.config(state='normal')
                if selected_color_idx[0] is not None and working_colors:
                    del_btn.config(state='normal')
                else:
                    del_btn.config(state='disabled')
            
            # Left group: Add/Delete
            left_btns = tk.Frame(btn_frame)
            left_btns.pack(side='left')
            add_btn = ttk.Button(left_btns, text='색상 추가', command=add_color, state='normal')
            add_btn.pack(side='left', padx=5)
            del_btn = ttk.Button(left_btns, text='색상 삭제', command=delete_color, state='disabled')
            del_btn.pack(side='left', padx=5)
            
            # Right group: Confirm/Cancel
            right_btns = tk.Frame(btn_frame)
            right_btns.pack(side='right')
            ttk.Button(right_btns, text='확인', command=confirm).pack(side='left', padx=5)
            ttk.Button(right_btns, text='취소', command=editor_dialog.destroy).pack(side='left', padx=5)
            
        except Exception as e:
            messagebox.showerror('오류', str(e))

    def get_luminance(self, hex_color):
        """Calculate luminance (brightness) of a color (0-255)."""
        try:
            rgb = self.generator.hex_to_rgb(hex_color)
            lum = int(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
            return lum
        except Exception:
            return 128

    def save_palette_file(self, idx):
        """Save palette to .mps file."""
        try:
            entry = self.saved_palettes[idx]
            filename = filedialog.asksaveasfilename(
                defaultextension='.mps',
                filetypes=[('My Palette', '*.mps'), ('All Files', '*.*')],
                initialfile=entry['name']
            )
            if filename:
                import json
                import base64
                data = json.dumps({'name': entry['name'], 'colors': entry['colors']})
                encoded = base64.b64encode(data.encode('utf-8')).decode('utf-8')
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(encoded)
        except Exception as e:
            messagebox.showerror('오류', f'저장 실패: {str(e)}')

    def toggle_palette_view(self, idx):
        """Toggle between RGB and Value (luminance) view."""
        try:
            entry = self.saved_palettes[idx]
            # Toggle view mode (default is 'rgb')
            current_mode = entry.get('view_mode', 'rgb')
            entry['view_mode'] = 'value' if current_mode == 'rgb' else 'rgb'
            self.render_saved_list()
        except Exception as e:
            messagebox.showerror('오류', str(e))

    def export_palette_txt(self, idx):
        """Export palette colors to TXT file."""
        try:
            entry = self.saved_palettes[idx]
            colors = entry.get('colors', [])
            if not colors:
                messagebox.showinfo('내보내기', '팔레트에 색상이 없습니다.')
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension='.txt',
                filetypes=[('Text File', '*.txt'), ('All Files', '*.*')],
                initialfile=f"{entry['name']}.txt"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"팔레트: {entry['name']}\n")
                    f.write(f"색상 개수: {len(colors)}\n\n")
                    for i, color in enumerate(colors, 1):
                        f.write(f"{i}. {color}\n")
        except Exception as e:
            messagebox.showerror('오류', f'TXT 내보내기 실패: {str(e)}')

    def export_palette_png(self, idx):
        """Export palette colors as PNG image."""
        try:
            entry = self.saved_palettes[idx]
            colors = entry.get('colors', [])
            if not colors:
                messagebox.showinfo('내보내기', '팔레트에 색상이 없습니다.')
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension='.png',
                filetypes=[('PNG Image', '*.png'), ('All Files', '*.*')],
                initialfile=f"{entry['name']}.png"
            )
            if filename:
                # Create image with colors side by side
                color_width = 100
                img_width = color_width * len(colors)
                img_height = 100
                
                img = Image.new('RGB', (img_width, img_height))
                draw = ImageDraw.Draw(img)
                
                try:
                    from PIL import ImageFont
                    font = ImageFont.load_default()
                except Exception:
                    font = None
                
                for i, color in enumerate(colors):
                    x0 = i * color_width
                    x1 = x0 + color_width
                    draw.rectangle([x0, 0, x1, img_height], fill=color)
                    
                    # Draw color hex code on top
                    try:
                        rgb = self.generator.hex_to_rgb(color)
                        lum = int(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
                        text_color = (0, 0, 0) if lum > 128 else (255, 255, 255)
                        
                        # Draw text at center
                        text = color.upper()
                        try:
                            bbox = draw.textbbox((0, 0), text, font=font)
                            text_width = bbox[2] - bbox[0]
                            text_height = bbox[3] - bbox[1]
                        except Exception:
                            text_width = len(text) * 6
                            text_height = 10
                        
                        text_x = x0 + (color_width - text_width) // 2
                        text_y = (img_height - text_height) // 2
                        draw.text((text_x, text_y), text, fill=text_color, font=font)
                    except Exception:
                        pass
                
                img.save(filename)
        except Exception as e:
            messagebox.showerror('오류', f'PNG 내보내기 실패: {str(e)}')

    def show_extracted_swatches(self, colors):
        """색상 목록(리스트 of RGB tuples)을 상단의 색상 탭 프레임에 표시합니다."""
        # clear existing
        for c in self.frm_color_tabs.winfo_children():
            c.destroy()

        for rgb in colors:
            try:
                hx = self.generator.rgb_to_hex(rgb)
            except Exception:
                # if input is already hex
                if isinstance(rgb, str):
                    hx = rgb
                else:
                    hx = '#ffffff'

            sw = tk.Canvas(self.frm_color_tabs, width=36, height=36, bd=1, relief='solid', highlightthickness=0)
            sw.pack(side='left', padx=4)
            try:
                sw.create_rectangle(0, 0, 36, 36, fill=hx, outline='')
            except tk.TclError:
                sw.create_rectangle(0, 0, 36, 36, fill='#ffffff', outline='')

    def hide_extracted_swatches(self):
        for c in self.frm_color_tabs.winfo_children():
            c.destroy()
        # also remove stored extracted colors reference
        self.extracted_colors = []

    def generate(self):
        source_type = self.source_type.get()
        try:
            if source_type == 'hex':
                hex_code = self.hex_entry.get().strip()
                if not hex_code.startswith('#') or len(hex_code) not in (4,7):
                    # Allow #RGB or #RRGGBB
                    if len(hex_code) == 4 and hex_code.startswith('#'):
                        pass
                    else:
                        raise ValueError("올바른 HEX 코드를 입력하세요 (예: #3498db).")
                palette = self.generator.generate_palette(hex_code, source_type='hex')
                # store current palettes for saving
                self.current_palettes = [palette]
                self.log_action(f"Generated palette from HEX: {hex_code}")
            else:
                if not self.image_path:
                    raise ValueError("이미지 파일을 선택하세요.")
                # First estimate approximate distinct color count, then run k-means up to 5 clusters
                approx = self.generator.approximate_color_count(self.image_path, sample_size=1000)
                k = min(5, approx) if approx >= 1 else 1
                main_colors = self.generator.extract_main_colors(self.image_path, num_colors=k)
                # store extracted colors and only display them (top tabs) when Generate is pressed
                self.extracted_colors = main_colors
                palettes = [self.generator.generate_palette(c, source_type='rgb') for c in main_colors]
                # store current palettes for saving
                self.current_palettes = palettes
                self.log_action(f"Generated palette from image: {os.path.basename(self.image_path)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log_action(f"Generate error: {str(e)}")
            return

        self.clear_palette_display()
        # if image mode, show the extracted swatches at top (only after Generate)
        if source_type == 'image' and getattr(self, 'extracted_colors', None):
            self.show_extracted_swatches(self.extracted_colors)
        # If HEX mode, show single palette; if image mode, show palettes for each representative color
        if source_type == 'hex':
            palette = palette
            base = palette['base']
            if isinstance(base, list):
                base = tuple(base)
            base_hex = self.generator.rgb_to_hex(base)
            ttk.Label(self.palette_inner, text="기본 색상", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
            self.draw_color_box(self.palette_inner, base_hex, f"RGB: {base}")

            # Display only selected harmony schemes
            scheme_labels = {
                'complementary': '보색',
                'analogous': '유사색',
                'triadic': '삼각 조화색',
                'monochromatic': '단색 조화',
                'split_complementary': '스플릿 보색',
                'square': '스퀘어',
                'tetradic': '테트라딕',
                'double_complementary': '더블 보색'
            }

            for scheme in self.selected_schemes:
                if scheme not in palette:
                    continue
                colors = palette[scheme]
                label = scheme_labels.get(scheme, scheme)
                
                ttk.Label(self.palette_inner, text=label, font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(8,0), padx=0)
                
                # Handle single color vs list
                if isinstance(colors, tuple) and len(colors) == 3 and all(isinstance(c, int) for c in colors):
                    # Single color (e.g., complementary)
                    hx = self.generator.rgb_to_hex(colors)
                    self.draw_color_box(self.palette_inner, hx, f"RGB: {colors}")
                elif isinstance(colors, list) and len(colors) == 3 and all(isinstance(c, int) for c in colors):
                    # Single color as list
                    colors = tuple(colors)
                    hx = self.generator.rgb_to_hex(colors)
                    self.draw_color_box(self.palette_inner, hx, f"RGB: {colors}")
                else:
                    # List of colors
                    for idx, col in enumerate(colors, 1):
                        if isinstance(col, list):
                            col = tuple(col)
                        hx = self.generator.rgb_to_hex(col)
                        self.draw_color_box(self.palette_inner, hx, f"{idx}. RGB: {col}")
        else:
            # palettes is a list of palette dicts for the 5 main colors
            for i, p in enumerate(palettes, start=1):
                ttk.Label(self.palette_inner, text=f"대표 색상 {i}", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(6,0), padx=0)
                base = p['base']
                if isinstance(base, list):
                    base = tuple(base)
                base_hex = self.generator.rgb_to_hex(base)
                self.draw_color_box(self.palette_inner, base_hex, f"Base RGB: {base}")

                # Display only selected harmony schemes
                scheme_labels = {
                    'complementary': '보색',
                    'analogous': '유사색',
                    'triadic': '삼각 조화색',
                    'monochromatic': '단색 조화',
                    'split_complementary': '스플릿 보색',
                    'square': '스퀘어',
                    'tetradic': '테트라딕',
                    'double_complementary': '더블 보색'
                }

                for scheme in self.selected_schemes:
                    if scheme not in p:
                        continue
                    colors = p[scheme]
                    label = scheme_labels.get(scheme, scheme)
                    
                    ttk.Label(self.palette_inner, text=f"  {label}", font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=0)
                    
                    # Handle single color vs list
                    if isinstance(colors, (tuple, list)) and len(colors) == 3 and all(isinstance(c, int) for c in colors):
                        # Single color
                        if isinstance(colors, list):
                            colors = tuple(colors)
                        hx = self.generator.rgb_to_hex(colors)
                        self.draw_color_box(self.palette_inner, hx, f"RGB: {colors}", clickable=True)
                    else:
                        # List of colors
                        for idx, col in enumerate(colors, 1):
                            if isinstance(col, list):
                                col = tuple(col)
                            hx = self.generator.rgb_to_hex(col)
                            self.draw_color_box(self.palette_inner, hx, f"{idx}. RGB: {col}", clickable=True)

    def display_single_palette(self, palette):
        """Display a single palette (for HEX mode)."""
        base = palette['base']
        if isinstance(base, list):
            base = tuple(base)
        base_hex = self.generator.rgb_to_hex(base)
        ttk.Label(self.palette_inner, text="기본 색상", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.draw_color_box(self.palette_inner, base_hex, f"RGB: {base}")

        scheme_labels = {
            'complementary': '보색',
            'analogous': '유사색',
            'triadic': '삼각 조화색',
            'monochromatic': '단색 조화',
            'split_complementary': '스플릿 보색',
            'square': '스퀘어',
            'tetradic': '테트라딕',
            'double_complementary': '더블 보색'
        }

        for scheme in self.selected_schemes:
            if scheme not in palette:
                continue
            colors = palette[scheme]
            label = scheme_labels.get(scheme, scheme)
            
            ttk.Label(self.palette_inner, text=label, font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(8,0), padx=0)
            
            # Handle single color (complementary)
            if isinstance(colors, (tuple, list)) and len(colors) == 3 and all(isinstance(c, int) for c in colors):
                if isinstance(colors, list):
                    colors = tuple(colors)
                hx = self.generator.rgb_to_hex(colors)
                self.draw_color_box(self.palette_inner, hx, f"RGB: {colors}")
            else:
                # Handle list of colors
                for idx, col in enumerate(colors, 1):
                    if isinstance(col, list):
                        col = tuple(col)
                    hx = self.generator.rgb_to_hex(col)
                    self.draw_color_box(self.palette_inner, hx, f"{idx}. RGB: {col}")
    def display_multiple_palettes(self, palettes):
        """Display multiple palettes (for image mode)."""
        for i, p in enumerate(palettes, start=1):
            ttk.Label(self.palette_inner, text=f"대표 색상 {i}", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(6,0), padx=0)
            base = p['base']
            if isinstance(base, list):
                base = tuple(base)
            base_hex = self.generator.rgb_to_hex(base)
            self.draw_color_box(self.palette_inner, base_hex, f"Base RGB: {base}")

            scheme_labels = {
                'complementary': '보색',
                'analogous': '유사색',
                'triadic': '삼각 조화색',
                'monochromatic': '단색 조화',
                'split_complementary': '스플릿 보색',
                'square': '스퀘어',
                'tetradic': '테트라딕',
                'double_complementary': '더블 보색'
            }

            for scheme in self.selected_schemes:
                if scheme not in p:
                    continue
                colors = p[scheme]
                label = scheme_labels.get(scheme, scheme)
                
                ttk.Label(self.palette_inner, text=f"  {label}", font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=0)
                
                if isinstance(colors, (tuple, list)) and len(colors) == 3 and all(isinstance(c, int) for c in colors):
                    if isinstance(colors, list):
                        colors = tuple(colors)
                    hx = self.generator.rgb_to_hex(colors)
                    self.draw_color_box(self.palette_inner, hx, f"RGB: {colors}", clickable=True)
                else:
                    for idx, col in enumerate(colors, 1):
                        if isinstance(col, list):
                            col = tuple(col)
                        hx = self.generator.rgb_to_hex(col)
                        self.draw_color_box(self.palette_inner, hx, f"{idx}. RGB: {col}", clickable=True)

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def on_enter(e):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{e.x_root+10}+{e.y_root+10}")
            label = tk.Label(tooltip, text=text, background='#ffffe0', relief='solid', borderwidth=1, font=('Arial', 9))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(e):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def copy_palette(self):
        """Copy currently selected palette."""
        if self._saved_selected is None:
            messagebox.showinfo('선택 필요', '팔레트를 선택해주세요.')
            return
        try:
            entry = self.saved_palettes[self._saved_selected]
            new_entry = {
                'name': f"{entry['name']} (복사)",
                'colors': entry['colors'].copy()
            }
            self.saved_palettes.append(new_entry)
            self._saved_selected = len(self.saved_palettes) - 1
            self.render_saved_list()
        except Exception as e:
            messagebox.showerror('오류', str(e))

    def load_palette(self):
        """Load palette from .mps file."""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[('My Palette', '*.mps'), ('All Files', '*.*')]
            )
            if filename:
                import json
                import base64
                with open(filename, 'r', encoding='utf-8') as f:
                    encoded = f.read()
                data = json.loads(base64.b64decode(encoded.encode('utf-8')).decode('utf-8'))
                new_entry = {'name': data['name'], 'colors': data['colors']}
                self.saved_palettes.append(new_entry)
                self._saved_selected = len(self.saved_palettes) - 1
                self.render_saved_list()
        except Exception as e:
            messagebox.showerror('오류', f'불러오기 실패: {str(e)}')

if __name__ == "__main__":
    app = PaletteApp()
    app.mainloop()
