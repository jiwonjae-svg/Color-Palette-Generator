from PIL import Image, ImageTk, ImageGrab
import colorsys
from collections import Counter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font as tkfont
import os
import random
import datetime

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
        """전체 팔레트 생성"""
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
            'monochromatic': self.generate_monochromatic(base_color)
        }
        
        return palette

class PaletteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Color Palette Generator")
        self.geometry("700x520")
        self.resizable(False, False)
        self.generator = ColorPaletteGenerator()
        self.image_path = None

        self.create_widgets()
    
    def create_widgets(self):
        frm_top = ttk.Frame(self, padding=10)
        frm_top.pack(fill='x')

        # Menu bar (File -> Save / Load)
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='Save...', command=self.save_as_dialog)
        filemenu.add_command(label='Load...', command=self.load_not_implemented)
        menubar.add_cascade(label='File', menu=filemenu)
        self.config(menu=menubar)

        # Source type radio
        self.source_type = tk.StringVar(value='hex')
        rb_hex = ttk.Radiobutton(frm_top, text='HEX 입력', value='hex', variable=self.source_type, command=self.on_source_change)
        rb_img = ttk.Radiobutton(frm_top, text='이미지 선택', value='image', variable=self.source_type, command=self.on_source_change)
        rb_hex.grid(row=0, column=0, sticky='w')
        rb_img.grid(row=0, column=1, sticky='w', padx=(8,0))

        # HEX entry
        ttk.Label(frm_top, text="HEX:").grid(row=1, column=0, pady=(8,0), sticky='w')
        self.hex_entry = ttk.Entry(frm_top, width=20)
        self.hex_entry.grid(row=1, column=1, pady=(8,0), sticky='w')
        self.hex_entry.insert(0, "#3498db")

        # Image select
        self.btn_select_img = ttk.Button(frm_top, text="이미지 선택...", command=self.select_image)
        self.btn_select_img.grid(row=1, column=2, padx=(8,0))
        self.lbl_image = ttk.Label(frm_top, text="선택된 파일 없음")
        self.lbl_image.grid(row=1, column=3, padx=(8,0), sticky='w')
        # small thumbnail next to image name
        self.img_thumbnail_label = ttk.Label(frm_top)
        self.img_thumbnail_label.grid(row=1, column=4, padx=(8,0))
        # Screen picker button
        btn_screen_pick = ttk.Button(frm_top, text="스크린에서 추출", command=self.start_screen_picker)
        btn_screen_pick.grid(row=1, column=5, padx=(8,0))

        # Generate button
        btn_generate = ttk.Button(frm_top, text="Generate", command=self.generate)
        btn_generate.grid(row=2, column=0, columnspan=2, pady=(12,0), sticky='w')
        # Random color button
        btn_random = ttk.Button(frm_top, text="랜덤 색상", command=self.generate_random)
        btn_random.grid(row=2, column=2, padx=(8,0), sticky='w')
        

        # Separator
        sep = ttk.Separator(self, orient='horizontal')
        sep.pack(fill='x', pady=10)

        # Palette display area
        self.frm_palette = ttk.Frame(self, padding=10)
        self.frm_palette.pack(fill='both', expand=True)

        # Color tabs (extracted swatches) shown above the palette area
        self.frm_color_tabs = ttk.Frame(self.frm_palette)
        self.frm_color_tabs.pack(fill='x', pady=(0,6))

        # Ensure saves directories exist
        self.saves_root = os.path.join(os.getcwd(), 'saves')
        for sub in ('txt', 'png', 'pgf'):
            try:
                os.makedirs(os.path.join(self.saves_root, sub), exist_ok=True)
            except Exception:
                pass

        # Scrollable canvas for palette (in case of small screens)
        canvas = tk.Canvas(self.frm_palette, borderwidth=0, highlightthickness=0)
        self.palette_inner = ttk.Frame(canvas)
        vsb = ttk.Scrollbar(self.frm_palette, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0,0), window=self.palette_inner, anchor="nw")
        self.palette_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Initial generate
        self.on_source_change()
        self.generate()

    def on_source_change(self):
        mode = self.source_type.get()
        if mode == 'hex':
            self.hex_entry.config(state='normal')
            self.btn_select_img.state(['disabled'])
            # hide extracted swatches when switching to HEX mode
            self.hide_extracted_swatches()
        else:
            self.hex_entry.config(state='disabled')
            self.btn_select_img.state(['!disabled'])
            # if an image is already selected, show its extracted swatches
            if getattr(self, 'extracted_colors', None):
                self.show_extracted_swatches(self.extracted_colors)

    def select_image(self):
        path = filedialog.askopenfilename(title="이미지 선택", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All files","*.*")])
        if path:
            self.image_path = path
            name = os.path.basename(path)
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
        lbl = tk.Label(picker, image=photo)
        lbl.image = photo
        lbl.place(x=0, y=0, width=width, height=height)

        # store virtual origin and size for coordinate mapping
        self._screen_origin = (x0, y0)
        self._virtual_size = (width, height)

        # larger floating label for color preview
        fl_font = ('Segoe UI', 14, 'bold')
        floating = tk.Label(picker, text='', bd=1, relief='solid', padx=12, pady=8, font=fl_font)
        floating.place(x=20, y=20)

        self._picker_win = picker
        self._picker_floating = floating

        picker.bind('<Motion>', self._on_picker_move)
        picker.bind('<Button-1>', self._on_picker_click)
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
            self.hex_entry.delete(0, 'end')
            self.hex_entry.insert(0, hx)
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

    def save_as_dialog(self):
        """Open a save-as dialog to save all current palettes into a single file (txt or png)."""
        if not getattr(self, 'current_palettes', None):
            messagebox.showwarning('No palettes', 'Generate a palette first before saving.')
            return

        filetypes = [('Text file', '*.txt'), ('PNG image', '*.png'), ('PGF file', '*.pgf')]
        path = filedialog.asksaveasfilename(title='Save palettes as...', initialdir=self.saves_root,
                                            defaultextension='.txt', filetypes=filetypes)
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()
        if ext == '.txt':
            try:
                self.save_palettes_to_single_txt(path)
                messagebox.showinfo('Saved', f'Saved palettes to {path}')
            except Exception as e:
                messagebox.showerror('Save Error', str(e))
        elif ext == '.png':
            try:
                self.save_palettes_to_single_png(path)
                messagebox.showinfo('Saved', f'Saved palettes to {path}')
            except Exception as e:
                messagebox.showerror('Save Error', str(e))
        elif ext == '.pgf':
            messagebox.showinfo('Not implemented', 'PGF save is not implemented yet.')
        else:
            messagebox.showerror('Save Error', 'Unsupported file extension')

    def load_not_implemented(self):
        messagebox.showinfo('Not implemented', 'Load feature is not implemented yet.')

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
        self.hex_entry.delete(0, 'end')
        self.hex_entry.insert(0, hex_code)
        self.generate()

    def clear_palette_display(self):
        for child in self.palette_inner.winfo_children():
            child.destroy()

    def draw_color_box(self, parent, hex_color, label_text):
        frm = ttk.Frame(parent)
        frm.pack(fill='x', pady=6)

        canvas = tk.Canvas(frm, width=120, height=50, bd=1, relief='solid')
        canvas.pack(side='left')
        try:
            canvas.create_rectangle(0,0,120,50, fill=hex_color, outline='')
        except tk.TclError:
            canvas.create_rectangle(0,0,120,50, fill="#ffffff", outline='')

        lbl = ttk.Label(frm, text=f"{label_text}\n{hex_color}")
        lbl.pack(side='left', padx=10)

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
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.clear_palette_display()
        # if image mode, show the extracted swatches at top (only after Generate)
        if source_type == 'image' and getattr(self, 'extracted_colors', None):
            self.show_extracted_swatches(self.extracted_colors)
        # If HEX mode, show single palette; if image mode, show palettes for each representative color
        if source_type == 'hex':
            palette = palette
            base_hex = self.generator.rgb_to_hex(palette['base'])
            ttk.Label(self.palette_inner, text="기본 색상", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
            self.draw_color_box(self.palette_inner, base_hex, f"RGB: {palette['base']}")

            ttk.Label(self.palette_inner, text="보색", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(8,0))
            comp_hex = self.generator.rgb_to_hex(palette['complementary'])
            self.draw_color_box(self.palette_inner, comp_hex, f"RGB: {palette['complementary']}")

            ttk.Label(self.palette_inner, text="유사색", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(8,0))
            for idx, col in enumerate(palette['analogous'], 1):
                hx = self.generator.rgb_to_hex(col)
                self.draw_color_box(self.palette_inner, hx, f"{idx}. RGB: {col}")

            ttk.Label(self.palette_inner, text="삼각 조화색", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(8,0))
            for idx, col in enumerate(palette['triadic'], 1):
                hx = self.generator.rgb_to_hex(col)
                self.draw_color_box(self.palette_inner, hx, f"{idx}. RGB: {col}")

            ttk.Label(self.palette_inner, text="단색 조화", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(8,0))
            for idx, col in enumerate(palette['monochromatic'], 1):
                hx = self.generator.rgb_to_hex(col)
                self.draw_color_box(self.palette_inner, hx, f"{idx}. RGB: {col}")
        else:
            # palettes is a list of palette dicts for the 5 main colors
            for i, p in enumerate(palettes, start=1):
                ttk.Label(self.palette_inner, text=f"대표 색상 {i}", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(6,2))
                base_hex = self.generator.rgb_to_hex(p['base'])
                self.draw_color_box(self.palette_inner, base_hex, f"Base RGB: {p['base']}")

                # Complementary
                ttk.Label(self.palette_inner, text="  보색", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
                comp_hex = self.generator.rgb_to_hex(p['complementary'])
                self.draw_color_box(self.palette_inner, comp_hex, f"RGB: {p['complementary']}")

                # Analogous
                ttk.Label(self.palette_inner, text="  유사색", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
                for idx, col in enumerate(p['analogous'], 1):
                    hx = self.generator.rgb_to_hex(col)
                    self.draw_color_box(self.palette_inner, hx, f"{idx}. RGB: {col}")

                # Triadic
                ttk.Label(self.palette_inner, text="  삼각 조화색", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
                for idx, col in enumerate(p['triadic'], 1):
                    hx = self.generator.rgb_to_hex(col)
                    self.draw_color_box(self.palette_inner, hx, f"{idx}. RGB: {col}")

                # Monochromatic
                ttk.Label(self.palette_inner, text="  단색 조화", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
                for idx, col in enumerate(p['monochromatic'], 1):
                    hx = self.generator.rgb_to_hex(col)
                    self.draw_color_box(self.palette_inner, hx, f"{idx}. RGB: {col}")

if __name__ == "__main__":
    app = PaletteApp()
    app.mainloop()