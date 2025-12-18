from PIL import Image, ImageTk, ImageGrab, ImageDraw
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font as tkfont, colorchooser
import os
import datetime
import tempfile
import logging
import hashlib
import colorsys
from cryptography.fernet import Fernet

# Import new modules
from color_generator import ColorPaletteGenerator
from file_handler import FileHandler
from config_manager import ConfigManager
from image_recolorer import ImageRecolorer
from language_manager import LanguageManager

# Import color adjuster if available
try:
    from color_adjuster import apply_contrast, apply_warmth
    COLOR_ADJUSTER_AVAILABLE = True
except Exception:
    COLOR_ADJUSTER_AVAILABLE = False
    apply_contrast = None
    apply_warmth = None

# ColorPaletteGenerator class is now in color_generator.py

class PaletteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.file_handler = FileHandler()
        self.config_manager = ConfigManager(self.file_handler)
        
        # Initialize language manager
        current_lang = self.config_manager.get('language', 'ko')
        self.lang = LanguageManager(current_lang)
        
        # Apply standard ttk style
        self.style = ttk.Style()
        
        window_width = self.config_manager.get('window_width', 700)
        window_height = self.config_manager.get('window_height', 520)
        self.geometry(f"{window_width}x{window_height}")
        self.resizable(False, False)
        
        self.generator = ColorPaletteGenerator()
        self.image_path = None
        self._temp_screenshot = None
        
        self.ai_recommender = None
        self.ai_palettes = []
        self.ai_palette_offset = 0
        
        self.selected_schemes = ['complementary', 'analogous', 'triadic', 'monochromatic']
        
        self.current_file = None
        self.is_modified = False
        
        self.auto_save_enabled = self.config_manager.get('auto_save_enabled', True)
        self.auto_save_interval = self.config_manager.get('auto_save_interval', 300) * 1000
        self.auto_save_timer = None
        
        # Recent colors storage
        self.recent_colors = self.config_manager.get('recent_colors', []) or []
        try:
            self.max_recent_colors = int(self.config_manager.get('max_recent_colors', 50))
        except Exception:
            self.max_recent_colors = 50
        self.max_recent_colors = max(1, min(100, self.max_recent_colors))

        if len(self.recent_colors) > self.max_recent_colors:
            self.recent_colors = self.recent_colors[:self.max_recent_colors]
            self.config_manager.set('recent_colors', self.recent_colors)
            self.config_manager.save_config()
        
        self.setup_logging()
        self.log_action("Application started")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.bind_shortcuts()
        
        self.setup_drag_drop()

        self.create_widgets()
        
        self.update_title()
        
        if self.auto_save_enabled:
            self.start_auto_save()
    
    def create_widgets(self):
        frm_top = ttk.Frame(self, padding=10)
        frm_top.pack(fill='x')

        # Menu bar (File -> New PGF / Save PGF / Save As / Open PGF / Open Recent / Exit)
        menubar = tk.Menu(self)
        
        self.filemenu = tk.Menu(menubar, tearoff=0)
        self.filemenu.add_command(label=self.lang.get('file_new'), command=self.new_pgf)
        self.filemenu.add_command(label=self.lang.get('file_save'), command=self.save_pgf)
        self.filemenu.add_command(label=self.lang.get('file_save_as'), command=self.save_pgf_as)
        self.filemenu.add_command(label=self.lang.get('file_open'), command=self.load_pgf)
        
        # Open Recent submenu
        self.recent_menu = tk.Menu(self.filemenu, tearoff=0)
        self.filemenu.add_cascade(label=self.lang.get('open_recent'), menu=self.recent_menu)
        self.update_recent_menu()
        
        self.filemenu.add_separator()
        self.filemenu.add_command(label=self.lang.get('file_exit'), command=self.quit)
        menubar.add_cascade(label=self.lang.get('menu_file'), menu=self.filemenu)
        
        # Options menu
        optionsmenu = tk.Menu(menubar, tearoff=0)
        optionsmenu.add_command(label=self.lang.get('settings_title'), command=self.open_settings)
        optionsmenu.add_command(label=self.lang.get('settings_api'), command=self.open_ai_settings)
        optionsmenu.add_separator()
        optionsmenu.add_command(label=self.lang.get('reset_to_defaults'), command=self.reset_settings)
        menubar.add_cascade(label=self.lang.get('menu_settings'), menu=optionsmenu)
        
        # Tools menu
        toolsmenu = tk.Menu(menubar, tearoff=0)
        toolsmenu.add_command(label=self.lang.get('apply_palette_to_image'), command=self.apply_palette_to_image)
        toolsmenu.add_separator()
        toolsmenu.add_command(label=self.lang.get('custom_color_harmonies'), command=self.open_custom_harmony)
        toolsmenu.add_separator()
        toolsmenu.add_command(label=self.lang.get('preset_palettes'), command=self.open_preset_palettes)
        menubar.add_cascade(label=self.lang.get('tools'), menu=toolsmenu)
        
        self.config(menu=menubar)

        # Source type radio
        self.source_type = tk.StringVar(value='hex')
        rb_hex = ttk.Radiobutton(frm_top, text=self.lang.get('pick_color'), value='hex', variable=self.source_type, command=self.on_source_change)
        rb_img = ttk.Radiobutton(frm_top, text=self.lang.get('from_image'), value='image', variable=self.source_type, command=self.on_source_change)
        rb_ai = ttk.Radiobutton(frm_top, text=self.lang.get('ai_palette'), value='ai', variable=self.source_type, command=self.on_source_change)
        rb_hex.grid(row=0, column=0, sticky='w')
        rb_img.grid(row=0, column=1, sticky='w', padx=(8,0))
        rb_ai.grid(row=0, column=2, sticky='w', padx=(8,0))

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
        self.lbl_color_info = ttk.Label(
            frm_top,
            text=(
                self.lang.get('label_hex').format(value='#3498db')
                + "\n"
                + self.lang.get('label_rgb').format(value='(52, 152, 219)')
            ),
            font=('Segoe UI', 9),
        )
        # span two columns so it doesn't collide with buttons
        self.lbl_color_info.grid(row=2, column=0, columnspan=2, pady=(2,0), sticky='w')
        
        # Now update the swatch and color info
        self._update_color_swatch("#3498db")
        
        self.btn_color_picker = ttk.Button(
            frm_top,
            text=self.lang.get('pick_color') + self.lang.get('ellipsis'),
            command=self.open_color_picker,
        )
        self.btn_color_picker.grid(row=1, column=1, pady=(8,0), padx=(8,0), sticky='w')

        # Image select
        self.btn_select_img = ttk.Button(frm_top, text=self.lang.get('select_image'), command=self.select_image)
        self.btn_select_img.grid(row=1, column=2, padx=(8,0), pady=(8,0), sticky='w')
        self.lbl_image = ttk.Label(frm_top, text=self.lang.get('no_file_selected'))
        self.lbl_image.grid(row=1, column=3, padx=(8,0), sticky='w')
        # small thumbnail next to image name
        self.img_thumbnail_label = ttk.Label(frm_top)
        self.img_thumbnail_label.grid(row=1, column=4, padx=(8,0))
        # Screen picker button
        btn_screen_pick = ttk.Button(frm_top, text=self.lang.get('extract_from_screen'), command=self.start_screen_picker)
        btn_screen_pick.grid(row=1, column=5, padx=(8,0), pady=(8,0), sticky='w')

        # action buttons row (separate row to avoid collisions)
        btn_generate = ttk.Button(frm_top, text=self.lang.get('generate'), command=self.generate)
        btn_generate.grid(row=3, column=0, pady=(12,0), sticky='w')
        # Random color button
        btn_random = ttk.Button(frm_top, text=self.lang.get('random_color'), command=self.generate_random)
        btn_random.grid(row=3, column=1, padx=(8,0), pady=(12,0), sticky='w')
        # Color harmony options button
        btn_harmony = ttk.Button(frm_top, text=self.lang.get('harmony_options'), command=self.open_harmony_selector)
        btn_harmony.grid(row=3, column=2, padx=(8,0), pady=(12,0), sticky='w')

        # Separator
        sep = ttk.Separator(self, orient='horizontal')
        sep.pack(fill='x', pady=0)

        # Main content area: left = palette display, right = saved palettes panel
        content = ttk.Frame(self)
        content.pack(fill='both', expand=True)

        # Left: Palette display area
        self.frm_palette = ttk.Frame(content, padding=10)
        self.frm_palette.pack(side='left', fill='both', expand=True)

        # Right: Container for recent colors and saved palettes
        right_panel = ttk.Frame(content)
        right_panel.pack(side='right', fill='y')
        
        # Recent colors panel (top)
        self.frm_recent = ttk.Frame(right_panel, padding=(6,6))
        self.frm_recent.pack(side='top', fill='x')
        
        recent_header = ttk.Frame(self.frm_recent)
        recent_header.pack(fill='x')
        ttk.Label(recent_header, text=self.lang.get('recent_colors_title'), font=('Segoe UI', 9, 'bold')).pack(side='left', anchor='w')
        
        # Clear history button
        btn_clear_recent = tk.Button(recent_header, text='🗑', font=('Arial', 8), command=self.clear_recent_colors, 
                                      width=2, bg='#f0f0f0', relief='flat', cursor='hand2', borderwidth=0)
        btn_clear_recent.pack(side='right')
        self.create_tooltip(btn_clear_recent, self.lang.get('recent_colors_clear'))

        # Container for recent color boxes (scrollable; prevents panel from growing)
        recent_body = ttk.Frame(self.frm_recent)
        recent_body.pack(fill='x', pady=(5, 0))
        # Fixed height: one row of swatches + a little padding + optional scrollbar
        recent_body.configure(height=54)
        recent_body.pack_propagate(False)

        self.recent_colors_canvas = tk.Canvas(recent_body, height=44, highlightthickness=0)
        self.recent_colors_scrollbar = ttk.Scrollbar(recent_body, orient='horizontal', command=self.recent_colors_canvas.xview)

        self.recent_colors_container = ttk.Frame(self.recent_colors_canvas)
        self._recent_colors_window = self.recent_colors_canvas.create_window(
            (0, 0), window=self.recent_colors_container, anchor='nw'
        )
        self.recent_colors_canvas.configure(xscrollcommand=self.recent_colors_scrollbar.set)

        self.recent_colors_canvas.pack(side='top', fill='both', expand=True)
        self.recent_colors_scrollbar.pack(side='bottom', fill='x')
        self.recent_colors_scrollbar.pack_forget()  # only show when needed

        # Keep scrollregion and inner-frame width in sync
        self.recent_colors_container.bind('<Configure>', self._on_recent_colors_container_configure)
        self.recent_colors_canvas.bind('<Configure>', self._on_recent_colors_canvas_configure)

        # Mouse wheel scrolling should only work while the cursor is over this panel
        self.recent_colors_canvas.bind('<Enter>', self._bind_recent_colors_wheel)
        self.recent_colors_canvas.bind('<Leave>', self._unbind_recent_colors_wheel)
        
        # Initial display
        self.update_recent_colors_display()
        
        ttk.Separator(right_panel, orient='horizontal').pack(fill='x', pady=8)
        
        # Saved palettes panel (bottom)
        self.frm_saved = ttk.Frame(right_panel, padding=(6,6))
        self.frm_saved.pack(side='top', fill='both', expand=True)

        ttk.Label(self.frm_saved, text=self.lang.get('saved_palettes'), font=('Segoe UI', 10, 'bold')).pack(anchor='nw', side='top')
        
        # buttons: add / remove / copy / load (fixed at bottom - pack first)
        btns_outer = tk.Frame(self.frm_saved, bg='#f0f0f0')
        btns_outer.pack(side='bottom', fill='x', pady=(4,0))
        
        # Center container for buttons
        btns_center = tk.Frame(btns_outer, bg='#f0f0f0')
        btns_center.pack(expand=True)
        
        btns = tk.Frame(btns_center, bg='#f0f0f0')
        btns.pack(pady=5)
        
        # Create buttons with emojis and tooltips
        self.btn_add = tk.Button(btns, text='📄', font=('Arial', 11), command=self.add_saved_palette, width=2, bg='#f0f0f0', relief='raised', cursor='hand2')
        self.btn_add.pack(side='left', padx=2, pady=5)
        self.create_tooltip(self.btn_add, self.lang.get('tooltip_add_palette'))
        
        self.btn_delete = tk.Button(btns, text='❌', font=('Arial', 11), command=self.remove_saved_palette, width=2, bg='#f0f0f0', relief='raised', cursor='hand2')
        self.btn_delete.pack(side='left', padx=2, pady=5)
        self.create_tooltip(self.btn_delete, self.lang.get('tooltip_delete_palette'))
        
        self.btn_copy = tk.Button(btns, text='📋', font=('Arial', 11), command=self.copy_palette, width=2, bg='#f0f0f0', relief='raised', cursor='hand2')
        self.btn_copy.pack(side='left', padx=2, pady=5)
        self.create_tooltip(self.btn_copy, self.lang.get('tooltip_copy_palette'))
        
        self.btn_load = tk.Button(btns, text='📂', font=('Arial', 11), command=self.load_palette, width=2, bg='#f0f0f0', relief='raised', cursor='hand2')
        self.btn_load.pack(side='left', padx=2, pady=5)
        self.create_tooltip(self.btn_load, self.lang.get('tooltip_load_palette'))
        
        if COLOR_ADJUSTER_AVAILABLE:
            self.btn_adjust = tk.Button(btns, text='🎨', font=('Arial', 11), command=self.open_color_adjuster, width=2, bg='#f0f0f0', relief='raised', cursor='hand2')
            self.btn_adjust.pack(side='left', padx=2, pady=5)
            self.create_tooltip(self.btn_adjust, self.lang.get('tooltip_adjust_color'))
        
        # scrollable container for saved palette entries
        self.list_frame = ttk.Frame(self.frm_saved)
        self.list_frame.pack(fill='both', expand=True, pady=(6,6))
        
        self.saved_canvas = tk.Canvas(self.list_frame, borderwidth=0, highlightthickness=0, bg='white', width=240)
        scrollbar = ttk.Scrollbar(self.list_frame, orient='vertical', command=self.saved_canvas.yview)
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
        name = self.lang.get('new_palette_numbered').format(i=self._saved_counter + 1)
        self._saved_counter += 1
        entry = {'name': name, 'colors': []}
        self.saved_palettes.append(entry)
        if self.saved_palettes:
            self._saved_selected = 0
            self.render_saved_list()

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
            if hasattr(self, 'btn_color_picker'):
                self.btn_color_picker.state(['!disabled'])
            if hasattr(self, 'color_swatch'):
                self.color_swatch.config(state='normal')
            self.btn_select_img.state(['disabled'])
                
        elif mode == 'image':
            if hasattr(self, 'btn_color_picker'):
                self.btn_color_picker.state(['disabled'])
            if hasattr(self, 'color_swatch'):
                self.color_swatch.config(state='disabled')
            self.btn_select_img.state(['!disabled'])
                
        elif mode == 'ai':
            if hasattr(self, 'btn_color_picker'):
                self.btn_color_picker.state(['disabled'])
            if hasattr(self, 'color_swatch'):
                self.color_swatch.config(state='disabled')
            self.btn_select_img.state(['disabled'])

    def select_image(self):
        """Select image with validation, size check, and error handling."""
        if getattr(self, '_temp_screenshot', None):
            try:
                os.unlink(self._temp_screenshot)
            except Exception:
                pass
            self._temp_screenshot = None

        path = filedialog.askopenfilename(
            title=self.lang.get('dialog_select_image'),
            filetypes=[
                (self.lang.get('image_files'), "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
                (self.lang.get('all_files'), "*.*"),
            ],
        )
        if not path:
            return
        
        # Validate file exists and is readable
        try:
            if not os.path.exists(path):
                messagebox.showerror(self.lang.get('error'), self.lang.get('msg_file_not_found'))
                return
            
            # Check file size (limit to 50MB for safety)
            file_size = os.path.getsize(path)
            if file_size > 50 * 1024 * 1024:
                response = messagebox.askyesno(
                    self.lang.get('msg_large_file_title'),
                    self.lang.get('msg_large_file_prompt').format(size_mb=file_size // (1024 * 1024)),
                )
                if not response:
                    return
            
            self.image_path = path
            self.log_action(f"Selected image: {os.path.basename(path)}")
            
            name = os.path.basename(path)
            # truncate long filenames for display (append ellipsis)
            max_len = 12
            if len(name) > max_len:
                name = name[:max_len-3] + self.lang.get('ellipsis')
            self.lbl_image.config(text=name)
            
            # create and show a small thumbnail image next to the filename
            try:
                img = Image.open(path)
                img.thumbnail((48, 48), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.img_thumbnail_label.config(image=photo)
                # keep a reference to avoid garbage collection
                self.img_thumbnail = photo
                # Explicitly close image to free memory
                img.close()
            except Exception as e:
                self.log_action(f"Thumbnail creation failed: {str(e)}")
                self.img_thumbnail_label.config(image='')
                messagebox.showwarning(self.lang.get('warning'), self.lang.get('msg_thumbnail_failed'))
            
            # Do NOT extract colors immediately; wait for Generate button.
            self.extracted_colors = []
            
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_image_load_failed').format(error=str(e)))
            self.log_action(f"Image selection failed: {str(e)}")

    def validate_hex_color(self, hex_code):
        """Validate HEX color format."""
        if not isinstance(hex_code, str):
            return False
        hex_code = hex_code.strip()
        if not hex_code.startswith('#'):
            return False
        hex_code = hex_code[1:]
        if len(hex_code) not in (3, 6):
            return False
        try:
            int(hex_code, 16)
            return True
        except ValueError:
            return False
    
    def open_harmony_selector(self):
        """Open a dialog to select which color harmony schemes to display."""
        dialog = tk.Toplevel(self)
        dialog.title(self.lang.get('harmonies_title'))
        dialog.geometry("400x500")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text=self.lang.get('select_harmonies'), font=('Segoe UI', 10, 'bold')).pack(pady=10, padx=10, anchor='w')

        # Create a scrollable frame for checkboxes
        canvas_frame = ttk.Frame(dialog)
        canvas_frame.pack(padx=10, pady=5, fill='both', expand=True)
        
        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        frm_checks = ttk.Frame(canvas)
        
        frm_checks.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=frm_checks, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mousewheel scrolling
        def on_mousewheel(e):
            try:
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            except Exception:
                pass
        
        canvas.bind('<MouseWheel>', on_mousewheel)
        frm_checks.bind('<MouseWheel>', on_mousewheel)

        # Define built-in harmony schemes with localized labels
        schemes = [
            ('complementary', self.lang.get('complementary_label')),
            ('analogous', self.lang.get('analogous_label')),
            ('triadic', self.lang.get('triadic_label')),
            ('monochromatic', self.lang.get('monochromatic')),
            ('split_complementary', self.lang.get('split_complementary')),
            ('square', self.lang.get('square')),
            ('tetradic', self.lang.get('tetradic')),
            ('double_complementary', self.lang.get('double_complementary')),
        ]

        # Create checkbox variables
        scheme_vars = {}
        for scheme_key, scheme_label in schemes:
            var = tk.BooleanVar(value=(scheme_key in self.selected_schemes))
            scheme_vars[scheme_key] = var
            cb = ttk.Checkbutton(frm_checks, text=scheme_label, variable=var)
            cb.pack(anchor='w', pady=4)
        
        # Add separator for custom harmonies
        try:
            from custom_harmony import CustomHarmonyManager
            manager = CustomHarmonyManager(self.file_handler)
            
            if manager.harmonies:
                ttk.Separator(frm_checks, orient='horizontal').pack(fill='x', pady=10)
                ttk.Label(frm_checks, text=self.lang.get('custom_harmonies'), font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=4)
                
                for i, harmony in enumerate(manager.harmonies):
                    harmony_name = harmony.get('name', self.lang.get('custom_harmony_numbered').format(i=i + 1))
                    scheme_key = f'custom_{i}'
                    var = tk.BooleanVar(value=(scheme_key in self.selected_schemes))
                    scheme_vars[scheme_key] = var
                    cb = ttk.Checkbutton(frm_checks, text=harmony_name, variable=var)
                    cb.pack(anchor='w', pady=4)
        except ImportError:
            pass

        # Buttons at bottom
        frm_buttons = ttk.Frame(dialog)
        frm_buttons.pack(pady=10, fill='x')

        def apply_selection():
            self.selected_schemes = [key for key, var in scheme_vars.items() if var.get()]
            if not self.selected_schemes:
                messagebox.showwarning(self.lang.get('warning'), self.lang.get('msg_select_harmony_required'))
                return
            dialog.destroy()
            self.generate()

        def cancel():
            dialog.destroy()

        # Create button container for centering
        btn_container = ttk.Frame(frm_buttons)
        btn_container.pack(expand=True)
        
        ttk.Button(btn_container, text=self.lang.get('ok'), command=apply_selection).pack(side='left', padx=5)
        ttk.Button(btn_container, text=self.lang.get('cancel'), command=cancel).pack(side='left', padx=5)

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
            info_text = (
                self.lang.get('label_hex').format(value=hex_color)
                + "\n"
                + self.lang.get('label_rgb').format(value=str(rgb))
            )
            self.lbl_color_info.config(text=info_text)
        except Exception:
            info_text = (
                self.lang.get('label_hex').format(value=hex_color)
                + "\n"
                + self.lang.get('label_rgb').format(value=self.lang.get('rgb_unknown'))
            )
            self.lbl_color_info.config(text=info_text)
    
    def add_to_recent_colors(self, hex_color):
        """Add a color to recent colors history."""
        # Normalize hex color to uppercase
        hex_color = hex_color.upper()
        
        # Remove if already exists (to move to front)
        if hex_color in self.recent_colors:
            self.recent_colors.remove(hex_color)
        
        # Add to front
        self.recent_colors.insert(0, hex_color)
        
        # Limit to max recent colors
        self.recent_colors = self.recent_colors[:self.max_recent_colors]
        
        # Save to config
        self.config_manager.set('recent_colors', self.recent_colors)
        self.config_manager.save_config()
        
        # Update display
        self.update_recent_colors_display()
    
    def update_recent_colors_display(self):
        """Update the recent colors display panel."""
        # Clear existing widgets
        for widget in self.recent_colors_container.winfo_children():
            widget.destroy()
        
        if not self.recent_colors:
            ttk.Label(self.recent_colors_container, text=self.lang.get('recent_colors_empty'), 
                     font=('Segoe UI', 8), foreground='gray').pack(pady=10)
            return
        
        # Display colors in a single horizontal row (scrollable)
        for idx, hex_color in enumerate(self.recent_colors):
            row = 0
            col = idx
            
            # Create color box with click handler
            self._create_color_box(self.recent_colors_container, hex_color, row, col, 
                                  lambda c=hex_color: self._use_color(c))

        try:
            self.recent_colors_canvas.update_idletasks()
            self.recent_colors_canvas.configure(scrollregion=self.recent_colors_canvas.bbox('all'))
        except Exception:
            pass
        self._update_recent_colors_scrollbar_visibility()

    def _bind_recent_colors_wheel(self, _event=None):
        try:
            self.recent_colors_canvas.bind('<MouseWheel>', self._on_recent_colors_mousewheel)
            self.recent_colors_canvas.bind('<Shift-MouseWheel>', self._on_recent_colors_mousewheel)
        except Exception:
            pass

    def _unbind_recent_colors_wheel(self, _event=None):
        try:
            self.recent_colors_canvas.unbind('<MouseWheel>')
            self.recent_colors_canvas.unbind('<Shift-MouseWheel>')
        except Exception:
            pass

    def _on_recent_colors_container_configure(self, _event=None):
        if hasattr(self, 'recent_colors_canvas'):
            try:
                self.recent_colors_canvas.configure(scrollregion=self.recent_colors_canvas.bbox('all'))
            except Exception:
                pass
            self._update_recent_colors_scrollbar_visibility()

    def _on_recent_colors_canvas_configure(self, event):
        try:
            self.recent_colors_canvas.configure(scrollregion=self.recent_colors_canvas.bbox('all'))
        except Exception:
            pass
        self._update_recent_colors_scrollbar_visibility()

    def _on_recent_colors_mousewheel(self, event):
        try:
            self.recent_colors_canvas.xview_scroll(int(-1 * (event.delta / 120)), 'units')
        except Exception:
            pass

    def _update_recent_colors_scrollbar_visibility(self):
        if not hasattr(self, 'recent_colors_canvas') or not hasattr(self, 'recent_colors_scrollbar'):
            return
        try:
            self.recent_colors_canvas.update_idletasks()

            bbox = self.recent_colors_canvas.bbox('all')
            if bbox:
                content_width = max(0, int(bbox[2] - bbox[0]))
            else:
                content_width = 0
            canvas_width = self.recent_colors_canvas.winfo_width()

            if content_width > canvas_width + 2:
                if not self.recent_colors_scrollbar.winfo_ismapped():
                    self.recent_colors_scrollbar.pack(side='bottom', fill='x')
            else:
                if self.recent_colors_scrollbar.winfo_ismapped():
                    self.recent_colors_scrollbar.pack_forget()
        except Exception:
            pass
    
    def _create_color_box(self, parent, hex_color, row, col, on_click):
        """Helper: Create a clickable color box with tooltip (코드 중복 제거)"""
        frm = tk.Frame(parent, bg='white', relief='solid', borderwidth=1, cursor='hand2')
        frm.grid(row=row, column=col, padx=2, pady=2)
        
        canvas = tk.Canvas(frm, width=30, height=30, bg=hex_color, highlightthickness=0)
        canvas.pack()
        
        # Bind click events to both frame and canvas
        for widget in (frm, canvas):
            widget.bind('<Button-1>', lambda e: on_click())
        
        # Create tooltip with RGB, Hex, Luminance
        rgb = self.generator.hex_to_rgb(hex_color)
        luminance = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
        tooltip_text = self.lang.get('tooltip_recent_color_info').format(
            rgb=str(rgb),
            hex=hex_color,
            lum=f"{luminance:.1f}/255",
        )
        # Bind tooltip to both frame and canvas to avoid missing hover events
        self.create_recent_color_tooltip((frm, canvas), tooltip_text)
    
    def _use_color(self, hex_color):
        """Helper: Use a color from recent colors or palette (코드 중복 제거)"""
        self.hex_entry.set(hex_color)
        self._update_color_swatch(hex_color)
        self.log_action(f"Used color: {hex_color}")
    
    def clear_recent_colors(self):
        """Clear recent colors history."""
        if not self.recent_colors:
            return
        
        self.recent_colors = []
        self.config_manager.set('recent_colors', [])
        self.config_manager.save_config()
        self.update_recent_colors_display()
        self.log_action("Cleared recent colors history")

    def open_color_picker(self):
        """Open color chooser dialog and update the selected color."""
        # Get current color from hex_entry
        current_color = self.hex_entry.get()
        try:
            # colorchooser.askcolor returns ((R,G,B), '#RRGGBB')
            color_result = colorchooser.askcolor(color=current_color, title=self.lang.get('pick_color_title'))
            if color_result[1]:  # if user didn't cancel
                hex_color = color_result[1]
                self.hex_entry.set(hex_color)
                self._update_color_swatch(hex_color)
                self.add_to_recent_colors(hex_color)
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_color_picker_failed').format(error=str(e)))

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
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_screen_picker_failed').format(error=str(e)))

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
                messagebox.showerror(self.lang.get('error'), self.lang.get('msg_capture_failed').format(error=str(e)))
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
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_capture_failed').format(error=str(e)))
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
                    messagebox.showerror(self.lang.get('save_error_title'), self.lang.get('msg_save_screenshot_failed').format(error=str(e)))
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
                    self.lbl_image.config(text=self.lang.get('screenshot_label'))
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
            self.add_to_recent_colors(hx)
            self.image_path = None
            self.extracted_colors = []
        except Exception:
            pass

    def save_palettes_txt(self):
        """Save current palettes as txt files under saves/txt."""
        if not getattr(self, 'current_palettes', None):
            messagebox.showwarning(self.lang.get('warning'), self.lang.get('msg_generate_palette_first'))
            return

        dest_dir = os.getcwd()
        now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        saved = []
        for i, p in enumerate(self.current_palettes, start=1):
            base_hex = self.generator.rgb_to_hex(p['base'])
            name = f"palette_{now}_{i}_{base_hex.lstrip('#')}.txt"
            path = os.path.join(dest_dir, name)
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.lang.get('export_txt_palette_title').format(i=i) + "\n")
                    f.write(
                        self.lang.get('export_txt_line_base').format(hex=base_hex, rgb=str(p['base'])) + "\n"
                    )
                    f.write("\n")
                    f.write(
                        self.lang.get('export_txt_line_complementary').format(
                            hex=self.generator.rgb_to_hex(p['complementary']),
                            rgb=str(p['complementary']),
                        )
                        + "\n"
                    )
                    f.write("\n")

                    f.write(self.lang.get('export_txt_section_analogous') + "\n")
                    for col in p['analogous']:
                        f.write(
                            "  "
                            + self.lang.get('export_txt_color_line').format(
                                hex=self.generator.rgb_to_hex(col),
                                rgb=str(col),
                            )
                            + "\n"
                        )
                    f.write("\n")

                    f.write(self.lang.get('export_txt_section_triadic') + "\n")
                    for col in p['triadic']:
                        f.write(
                            "  "
                            + self.lang.get('export_txt_color_line').format(
                                hex=self.generator.rgb_to_hex(col),
                                rgb=str(col),
                            )
                            + "\n"
                        )
                    f.write("\n")

                    f.write(self.lang.get('export_txt_section_monochromatic') + "\n")
                    for col in p['monochromatic']:
                        f.write(
                            "  "
                            + self.lang.get('export_txt_color_line').format(
                                hex=self.generator.rgb_to_hex(col),
                                rgb=str(col),
                            )
                            + "\n"
                        )
                saved.append(path)
            except Exception as e:
                messagebox.showerror(self.lang.get('save_error_title'), self.lang.get('msg_save_txt_failed').format(error=str(e)))
                return

        messagebox.showinfo(self.lang.get('saved_title'), self.lang.get('msg_saved_txt_summary').format(count=len(saved), dest_dir=dest_dir))

    def save_palettes_png(self):
        """Save current palettes as PNG images under saves/png.

        Each palette is saved as a horizontal row of swatches (base + complementary + analogous + triadic + monochromatic).
        """
        if not getattr(self, 'current_palettes', None):
            messagebox.showwarning(self.lang.get('warning'), self.lang.get('msg_generate_palette_first'))
            return

        from PIL import ImageDraw

        dest_dir = os.getcwd()
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
                messagebox.showerror(self.lang.get('save_error_title'), self.lang.get('msg_save_png_failed').format(error=str(e)))
                return

        messagebox.showinfo(self.lang.get('saved_title'), self.lang.get('msg_saved_png_summary').format(count=len(saved), dest_dir=dest_dir))

    def new_pgf(self):
        """Create a new PGF workspace."""
        # Ask to save if modified
        if self.is_modified:
            response = messagebox.askyesnocancel(self.lang.get('save_prompt_title'), self.lang.get('msg_save_changes_prompt'))
            if response is None:  # Cancel
                return
            elif response:  # Yes
                saved = self.save_pgf()
                if not saved:  # User cancelled save dialog
                    return
        
        # Reset to default state
        self.saved_palettes = [{'name': self.lang.get('new_palette_numbered').format(i=1), 'colors': []}]
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
        base_title = self.lang.get('title')
        if self.current_file:
            filename = os.path.basename(self.current_file)
            title = f"{base_title} - {filename}"
        else:
            title = f"{base_title} - {self.lang.get('untitled')}"
        
        if self.is_modified:
            title += " *"
        
        self.title(title)
        self.update_menu_states()
    
    def update_menu_states(self):
        """Update menu item and button states based on current state."""
        try:
            # Save As: only enabled if a file is already open
            if self.current_file:
                # Use index instead of label (label is localized)
                self.filemenu.entryconfig(2, state='normal')
            else:
                self.filemenu.entryconfig(2, state='disabled')
            
            # Delete button: disabled if only 1 palette or none selected
            if hasattr(self, 'btn_delete'):
                if len(self.saved_palettes) <= 1 or self._saved_selected is None:
                    self.btn_delete.config(state='disabled', cursor='arrow')
                else:
                    self.btn_delete.config(state='normal', cursor='hand2')
        except Exception:
            pass

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
            # No current file, prompt for new file location
            try:
                path = filedialog.asksaveasfilename(
                    title=self.lang.get('dialog_save_pgf'), 
                    initialdir=os.getcwd(),
                    defaultextension='.pgf', 
                    filetypes=[('PGF file', '*.pgf')]
                )
                if not path:
                    return False
                
                result = self._save_to_file(path)
                if result:
                    self.log_action(f"Saved new workspace: {path}")
                return result
            except Exception as e:
                messagebox.showerror(self.lang.get('save_error_title'), self.lang.get('msg_save_failed').format(error=str(e)))
                self.log_action(f"Save failed: {str(e)}")
                return False
    
    def save_pgf_as(self):
        """Save As: Always prompt for new file location. Only enabled if a file is already open."""
        try:
            # This function should only be called when menu is enabled (checked by update_menu_states)
            if not self.current_file:
                return False
            
            path = filedialog.asksaveasfilename(
                title=self.lang.get('dialog_save_as'), 
                initialdir=os.getcwd(),
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
            messagebox.showerror(self.lang.get('save_error_title'), self.lang.get('msg_save_failed').format(error=str(e)))
            self.log_action(f"Save As failed: {str(e)}")
            return False
    
    def _save_to_file(self, path):
        """Internal method to save workspace to a specific file path using AES encryption."""
        try:
            import json
            
            # Validate path
            if not path:
                raise ValueError(self.lang.get('msg_no_save_path'))
            
            # Ensure directory exists
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Collect all workspace state with validation
            workspace_data = {
                'saved_palettes': self.saved_palettes or [],
                'selected_schemes': self.selected_schemes or [],
                'source_type': self.source_type.get() if hasattr(self, 'source_type') else 'hex',
                'hex_entry': self.hex_entry.get() if hasattr(self, 'hex_entry') else '#3498db',
                'current_palettes': getattr(self, 'current_palettes', []),
                'saved_counter': self._saved_counter,
                'saved_selected': self._saved_selected,
                'version': '1.0'  # Add version for future compatibility
            }
            
            # Encrypt and save using AES
            data_json = json.dumps(workspace_data, ensure_ascii=False)
            encrypted = self._encrypt_aes(data_json)
            
            # Write to temporary file first
            temp_path = path + '.tmp'
            try:
                with open(temp_path, 'wb') as f:
                    f.write(encrypted)
                
                # Replace original file atomically
                if os.path.exists(path):
                    backup_path = path + '.bak'
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(path, backup_path)
                
                os.rename(temp_path, path)
                
                # Clean up backup if save was successful
                backup_path = path + '.bak'
                if os.path.exists(backup_path):
                    try:
                        os.remove(backup_path)
                    except Exception:
                        pass
                        
            except Exception as write_error:
                # Clean up temp file
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                raise write_error
            
            # Update state only after successful save
            self.current_file = path
            self.is_modified = False
            self.update_title()
            
            # Add to recent files
            self.add_recent_file(path)
            messagebox.showinfo(self.lang.get('saved_title'), self.lang.get('msg_workspace_saved').format(path=path))
            self.log_action(f"Saved workspace: {path}")
            return True
            
        except PermissionError:
            messagebox.showerror(self.lang.get('save_error_title'), self.lang.get('msg_permission_denied_write'))
            self.log_action(f"Save failed: Permission denied for {path}")
            return False
        except OSError as e:
            messagebox.showerror(self.lang.get('save_error_title'), self.lang.get('msg_disk_error').format(error=str(e)))
            self.log_action(f"Save failed: OS error - {str(e)}")
            return False
        except Exception as e:
            messagebox.showerror(self.lang.get('save_error_title'), self.lang.get('msg_save_failed').format(error=str(e)))
            self.log_action(f"Save failed: {str(e)}")
            return False
    
    def load_pgf(self):
        """Load workspace state from encrypted PGF file."""
        try:
            path = filedialog.askopenfilename(
                title=self.lang.get('dialog_open_pgf'), 
                initialdir=os.getcwd(),
                filetypes=[('PGF file', '*.pgf')]
            )
            if not path:
                return
            
            import json
            import base64
            
            # Try to load as AES first, fallback to base64 for old files
            with open(path, 'rb') as f:
                file_data = f.read()
            
            try:
                # Try AES decryption first
                data_json = self._decrypt_aes(file_data)
                workspace_data = json.loads(data_json)
            except Exception:
                # Fallback to base64 for old files
                try:
                    data_json = base64.b64decode(file_data).decode('utf-8')
                    workspace_data = json.loads(data_json)
                except Exception as e2:
                    raise Exception(f"Failed to decrypt file: {str(e2)}")
            
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
            messagebox.showinfo(self.lang.get('loaded_title'), self.lang.get('msg_workspace_loaded').format(path=path))
            self.log_action(f"Loaded workspace: {path}")
        except Exception as e:
            messagebox.showerror(self.lang.get('load_error_title'), self.lang.get('msg_load_failed').format(error=str(e)))
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
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        log_file = os.path.join(temp_dir, 'app.log')
        
        # Clear existing handlers to avoid duplicates
        logger = logging.getLogger(__name__)
        logger.handlers.clear()
        
        # Set logging level
        logger.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.logger = logger
        self.logger.info("="*50)
        self.logger.info("Logging system initialized")
    
    def log_action(self, action):
        """Log an action to the log file."""
        try:
            if hasattr(self, 'logger'):
                self.logger.info(action)
        except Exception as e:
            print(f"Logging error: {e}")
    
    def bind_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.bind('<Control-s>', lambda e: self.save_pgf())
        self.bind('<Control-Shift-S>', lambda e: self.save_pgf_as())
        self.bind('<Control-n>', lambda e: self.new_pgf())
        self.bind('<Control-o>', lambda e: self.load_pgf())
        self.bind('<Delete>', lambda e: self.remove_saved_palette())
        self.bind('<F5>', lambda e: self.generate())
        self.log_action("Keyboard shortcuts enabled")
    
    def setup_drag_drop(self):
        """Setup drag and drop for image files."""
        try:
            # Windows-specific drag and drop using tkinterdnd2 or basic implementation
            def on_drop(event):
                files = self.tk.splitlist(event.data)
                if files:
                    file_path = files[0]
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                        self.image_path = file_path
                        self.source_type.set('image')
                        self.on_source_change()
                        self.log_action(f"Image dropped: {os.path.basename(file_path)}")
                        messagebox.showinfo(self.lang.get('info'), self.lang.get('msg_image_loaded').format(filename=os.path.basename(file_path)))
                    elif file_path.lower().endswith('.pgf'):
                        self._load_pgf_file(file_path)
            
            # Register drop target (basic implementation)
            self.drop_target_register('DND_Files')
            self.dnd_bind('<<Drop>>', on_drop)
        except Exception:
            # Drag-and-drop not available, continue without it
            pass
    
    def start_auto_save(self):
        """Start auto-save timer."""
        if self.auto_save_enabled and self.is_modified and self.current_file:
            try:
                self._save_to_file(self.current_file)
                self.log_action("Auto-saved workspace")
            except Exception as e:
                self.log_action(f"Auto-save failed: {str(e)}")
        
        # Schedule next auto-save
        if self.auto_save_enabled:
            self.auto_save_timer = self.after(self.auto_save_interval, self.start_auto_save)
    
    def stop_auto_save(self):
        """Stop auto-save timer."""
        if self.auto_save_timer:
            self.after_cancel(self.auto_save_timer)
            self.auto_save_timer = None
    
    def on_closing(self):
        """Handle window close event - ask to save if modified."""
        # Stop auto-save
        self.stop_auto_save()
        
        if self.is_modified:
            response = messagebox.askyesnocancel(
                self.lang.get('save_prompt_title'),
                self.lang.get('msg_save_changes_prompt'),
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
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
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
                self.recent_menu.add_command(label=self.lang.get('no_recent_files'), state='disabled')
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
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_file_not_found_path').format(path=filepath))
            return
        
        try:
            import json
            import base64
            
            # Try to load as AES first, fallback to base64 for old files
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            try:
                # Try AES decryption first
                data_json = self._decrypt_aes(file_data)
                workspace_data = json.loads(data_json)
            except Exception:
                # Fallback to base64 for old files
                try:
                    data_json = base64.b64decode(file_data).decode('utf-8')
                    workspace_data = json.loads(data_json)
                except Exception as e2:
                    raise Exception(f"Failed to decrypt file: {str(e2)}")
            
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
            messagebox.showerror(self.lang.get('load_error_title'), self.lang.get('msg_load_failed').format(error=str(e)))

    def save_palettes_to_single_txt(self, path):
        """Save all current palettes into a single text file at `path`."""
        with open(path, 'w', encoding='utf-8') as f:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(self.lang.get('export_txt_file_header').format(timestamp=now) + "\n\n")
            for i, p in enumerate(self.current_palettes, start=1):
                base_hex = self.generator.rgb_to_hex(p['base'])
                f.write(self.lang.get('export_txt_palette_title').format(i=i) + "\n")
                f.write(
                    self.lang.get('export_txt_line_base').format(hex=base_hex, rgb=str(p['base'])) + "\n"
                )
                f.write(
                    "  "
                    + self.lang.get('export_txt_line_complementary').format(
                        hex=self.generator.rgb_to_hex(p['complementary']),
                        rgb=str(p['complementary']),
                    )
                    + "\n"
                )
                f.write("  " + self.lang.get('export_txt_section_analogous') + "\n")
                for idx, col in enumerate(p['analogous'], 1):
                    f.write(
                        "    "
                        + self.lang.get('export_txt_indexed_color_line').format(
                            i=idx,
                            hex=self.generator.rgb_to_hex(col),
                            rgb=str(col),
                        )
                        + "\n"
                    )
                f.write("  " + self.lang.get('export_txt_section_triadic') + "\n")
                for idx, col in enumerate(p['triadic'], 1):
                    f.write(
                        "    "
                        + self.lang.get('export_txt_indexed_color_line').format(
                            i=idx,
                            hex=self.generator.rgb_to_hex(col),
                            rgb=str(col),
                        )
                        + "\n"
                    )
                f.write("  " + self.lang.get('export_txt_section_monochromatic') + "\n")
                for idx, col in enumerate(p['monochromatic'], 1):
                    f.write(
                        "    "
                        + self.lang.get('export_txt_indexed_color_line').format(
                            i=idx,
                            hex=self.generator.rgb_to_hex(col),
                            rgb=str(col),
                        )
                        + "\n"
                    )
                f.write("\n")

    def save_palettes_to_single_png(self, path):
        """Save all current palettes into a single PNG image with category labels and hex codes."""
        from PIL import ImageDraw, ImageFont

        palettes = self.current_palettes
        # build flattened swatch lists with category labels for each palette
        palette_rows = []
        for i, p in enumerate(palettes, start=1):
            row = []
            # base
            row.append((self.lang.get('export_png_label_base'), p['base']))
            # complementary
            row.append((self.lang.get('export_png_label_complementary'), p['complementary']))
            # analogous
            for idx, col in enumerate(p['analogous'], 1):
                row.append(
                    (
                        self.lang.get('export_png_label_numbered').format(
                            label=self.lang.get('export_png_label_analogous'),
                            i=idx,
                        ),
                        col,
                    )
                )
            # triadic
            for idx, col in enumerate(p['triadic'], 1):
                row.append(
                    (
                        self.lang.get('export_png_label_numbered').format(
                            label=self.lang.get('export_png_label_triadic'),
                            i=idx,
                        ),
                        col,
                    )
                )
            # monochromatic
            for idx, col in enumerate(p['monochromatic'], 1):
                row.append(
                    (
                        self.lang.get('export_png_label_numbered').format(
                            label=self.lang.get('export_png_label_monochromatic'),
                            i=idx,
                        ),
                        col,
                    )
                )
            palette_rows.append((self.lang.get('export_png_palette_title').format(i=i), row))

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
        """Clear palette display with proper cleanup and error handling."""
        try:
            # Get all children first to avoid iteration issues
            children = self.palette_inner.winfo_children()
            for child in children:
                try:
                    child.destroy()
                except tk.TclError:
                    # Widget already destroyed
                    pass
                except Exception as e:
                    self.log_action(f"Widget cleanup error: {str(e)}")
        except Exception as e:
            self.log_action(f"Clear palette display error: {str(e)}")
        except Exception as e:
            self.log_action(f"Clear palette display error: {str(e)}")

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
        
        # Hover effect: change entire frame background to light blue and show tooltip
        tooltip_window = [None]  # Use list to make it mutable
        
        def show_tooltip(e):
            # Hide any existing tooltip
            if tooltip_window[0]:
                try:
                    tooltip_window[0].destroy()
                except Exception:
                    pass
            
            # Create new tooltip
            tip = tk.Toplevel(self)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{e.x_root+10}+{e.y_root+10}")
            
            label = tk.Label(tip, text=self.lang.get('color_box_tooltip'), 
                           bg='#FFFFE0', relief='solid', borderwidth=1, font=('Segoe UI', 9), padx=5, pady=3)
            label.pack()
            tooltip_window[0] = tip
        
        def hide_tooltip(e):
            if tooltip_window[0]:
                try:
                    tooltip_window[0].destroy()
                    tooltip_window[0] = None
                except Exception:
                    pass
        
        def on_enter(e):
            try:
                frm.config(bg='#ADD8E6')  # light blue
                canvas.config(bg='#ADD8E6')
                lbl.config(background='#ADD8E6')
                if clickable:
                    show_tooltip(e)
            except Exception:
                pass
        
        def on_leave(e):
            try:
                frm.config(bg='white')
                canvas.config(bg='white')
                lbl.config(background='white')
                hide_tooltip(e)
            except Exception:
                pass
        
        frm.bind('<Enter>', on_enter)
        frm.bind('<Leave>', on_leave)
        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)

        # clicking a color swatch should try to add the color to the selected saved palette
        if clickable:
            try:
                def on_left_click(e, hx=hex_color):
                    hide_tooltip(e)
                    self.on_palette_color_click(hx)
                
                def on_right_click(e, hx=hex_color):
                    hide_tooltip(e)
                    self.set_base_color(hx)
                
                canvas.bind('<Button-1>', on_left_click)
                # Right-click: set as base color
                canvas.bind('<Button-3>', on_right_click)
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
                def on_label_left_click(e, hx=hex_color):
                    hide_tooltip(e)
                    self.on_palette_color_click(hx)
                
                def on_label_right_click(e, hx=hex_color):
                    hide_tooltip(e)
                    self.set_base_color(hx)
                
                lbl.bind('<Button-1>', on_label_left_click)
                lbl.bind('<Button-3>', on_label_right_click)
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
        name = self.lang.get('new_palette_numbered').format(i=self._saved_counter + 1)
        self._saved_counter += 1

        entry = {'name': name, 'colors': []}
        self.saved_palettes.append(entry)
        # do not auto-select or preview; just re-render to show the new empty palette
        self.render_saved_list()
        self.mark_modified()
        self.log_action(f"Added new palette: {name}")

    def remove_saved_palette(self):
        # Button is disabled when only 1 palette or nothing selected (checked by update_menu_states)
        # This function should only be called when it's safe to delete
        if len(self.saved_palettes) <= 1 or self._saved_selected is None:
            return
        idx = self._saved_selected
        palette_name = self.saved_palettes[idx]['name'] if idx < len(self.saved_palettes) else self.lang.get('unknown')
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

        ttk.Label(self.palette_inner, text=entry.get('name', self.lang.get('saved_palette_default_name')), font=('Segoe UI', 10, 'bold')).pack(anchor='w')
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
            messagebox.showinfo(self.lang.get('selection_required'), self.lang.get('select_palette_first'))
            return
        
        try:
            entry = self.saved_palettes[self._saved_selected]
            # Normalize to hex string
            hex_str = hex_color if isinstance(hex_color, str) else self.generator.rgb_to_hex(hex_color)
            
            # Add color to palette and recent colors
            entry['colors'].append(hex_str)
            self.add_to_recent_colors(hex_str)
            
            # Update UI
            self.render_saved_list()
            self.mark_modified()
            self.log_action(f"Added color {hex_str} to palette: {entry['name']}")
        except Exception as e:
            self.log_action(f"Error adding color to palette: {str(e)}")
    
    def set_base_color(self, hex_color):
        """Set the clicked color as the base color and regenerate palette."""
        try:
            # Set source type to HEX
            self.source_type.set('hex')
            self.on_source_change()
            
            # Set the color in hex_entry
            self.hex_entry.set(hex_color)
            self._update_color_swatch(hex_color)
            
            # Regenerate palette
            self.generate()
            self.log_action(f"Set base color to {hex_color}")
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_set_base_color_failed').format(error=str(e)))

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
            lbl = ttk.Label(ef, text=entry.get('name', self.lang.get('palette_numbered').format(i=idx+1)))
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
        
        # Update menu states after rendering
        self.update_menu_states()

    def _select_saved_entry(self, idx):
        self._saved_selected = idx
        # do not clear main palette display; just re-render the saved list to show selection highlight
        self.render_saved_list()
        self.update_menu_states()

    def show_palette_context_menu(self, idx, event):
        """Show context menu for palette operations."""
        self._saved_selected = idx
        self.render_saved_list()
        
        entry = self.saved_palettes[idx]
        current_mode = entry.get('view_mode', 'rgb')
        view_label = self.lang.get('view_rgb') if current_mode == 'value' else self.lang.get('view_value')
        
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=self.lang.get('context_rename'), command=lambda: self.rename_palette(idx))
        menu.add_command(label=self.lang.get('context_edit_palette'), command=lambda: self.open_palette_editor(idx))
        menu.add_command(label=self.lang.get('context_save_palette'), command=lambda: self.save_palette_file(idx))
        menu.add_separator()
        menu.add_command(label=self.lang.get('context_export_txt'), command=lambda: self.export_palette_txt(idx))
        menu.add_command(label=self.lang.get('context_export_png'), command=lambda: self.export_palette_png(idx))
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
            dialog.title(self.lang.get('rename'))
            dialog.geometry('300x130')
            dialog.resizable(False, False)
            dialog.transient(self)
            dialog.grab_set()
            
            ttk.Label(dialog, text=f"{self.lang.get('new_name')}:").pack(pady=(10,5))
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
                    self.log_action(f"Renamed palette: {old_name} -> {new_name}")
                dialog.destroy()
            
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(pady=10)
            ttk.Button(btn_frame, text=self.lang.get('ok'), command=save_name).pack(side='left', padx=5)
            ttk.Button(btn_frame, text=self.lang.get('cancel'), command=dialog.destroy).pack(side='left', padx=5)
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), str(e))

    def open_palette_editor(self, idx):
        """Open editor window for palette colors."""
        try:
            entry = self.saved_palettes[idx]
            editor_dialog = tk.Toplevel(self)
            editor_dialog.title(self.lang.get('palette_editor_title').format(name=entry["name"]))
            editor_dialog.geometry('600x200')
            editor_dialog.resizable(False, False)
            editor_dialog.transient(self)
            editor_dialog.grab_set()
            
            # Store working copy of colors (empty list if no colors)
            working_colors = entry['colors'].copy() if entry['colors'] else []
            selected_color_idx = [None]  # use list to make it mutable in nested functions
            hover_color_idx = [None]  # track hover state
            show_as_value = [False]  # toggle for value display
            
            # Top: color bar display (with padding)
            bar_container = tk.Frame(editor_dialog, bg='#f0f0f0')
            bar_container.pack(fill='x', expand=False, padx=10, pady=(10,5))
            self.palette_editor_bar = tk.Canvas(bar_container, bg='white', height=50, highlightthickness=0)
            self.palette_editor_bar.pack(fill='x', expand=False)
            
            # Value display toggle
            toggle_frame = tk.Frame(editor_dialog)
            toggle_frame.pack(fill='x', padx=10, pady=(0,5))
            show_value_var = tk.BooleanVar(value=False)
            
            def toggle_value_display():
                show_as_value[0] = show_value_var.get()
                draw_colors()
            
            ttk.Checkbutton(toggle_frame, text=self.lang.get('view_value'), variable=show_value_var, command=toggle_value_display).pack(side='left')
            
            # Tooltip label for color info (hidden by default)
            tooltip_label = tk.Label(editor_dialog, text='', bg='#FFFFE0', relief='solid', borderwidth=1, font=('Segoe UI', 9))
            tooltip_label.pack_forget()  # Hidden initially
            tooltip_state = {'label': tooltip_label, 'visible': False}
            
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
                    
                    # Determine fill color based on display mode
                    if show_as_value[0]:
                        # Show as grayscale value (brightness)
                        lum = self.get_luminance(color)
                        gray_hex = self.generator.rgb_to_hex((lum, lum, lum))
                        fill_color = gray_hex
                    else:
                        fill_color = color
                    
                    # Draw color box
                    self.palette_editor_bar.create_rectangle(x0, 0, x1, 50, fill=fill_color, outline='')
                    
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
                    
                    # Show tooltip with color info including Luminance (grayscale value)
                    if hovered_idx < len(working_colors):
                        hex_color = working_colors[hovered_idx]
                        try:
                            rgb = self.generator.hex_to_rgb(hex_color)
                            # Calculate Luminance (흑백 변환 시 밝기)
                            lum = int(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
                            tooltip_text = self.lang.get('tooltip_palette_color_info').format(
                                hex=hex_color,
                                rgb=rgb,
                                lum=lum,
                            )
                            tooltip_state['label'].config(text=tooltip_text)
                            # Position tooltip near cursor
                            x = e.x_root + 10
                            y = e.y_root + 10
                            tooltip_state['label'].place(x=x - editor_dialog.winfo_rootx(), y=y - editor_dialog.winfo_rooty())
                            tooltip_state['label'].lift()
                            tooltip_state['visible'] = True
                        except Exception:
                            pass
            
            def on_canvas_leave(e):
                if not drag_state['dragging'] and hover_color_idx[0] is not None:
                    hover_color_idx[0] = None
                    draw_colors()
                # Hide tooltip
                if tooltip_state['visible']:
                    tooltip_state['label'].place_forget()
                    tooltip_state['visible'] = False
            
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
                if not COLOR_ADJUSTER_AVAILABLE:
                    # 폴백: 색상 피커 사용
                    color_result = colorchooser.askcolor(title=self.lang.get('add_color_title'))
                    if color_result[1]:
                        hex_color = color_result[1]
                        if selected_color_idx[0] is not None and working_colors:
                            working_colors.insert(selected_color_idx[0], hex_color)
                        else:
                            working_colors.append(hex_color)
                        draw_colors()
                        update_button_states()
                else:
                    # HSV 슬라이더 사용
                    initial_color = '#808080'  # 회색으로 시작
                    
                    def on_color_selected(new_hex):
                        if selected_color_idx[0] is not None and working_colors:
                            working_colors.insert(selected_color_idx[0], new_hex)
                        else:
                            working_colors.append(new_hex)
                        draw_colors()
                        update_button_states()
                    
                    SingleColorAdjusterDialog(editor_dialog, self.generator, initial_color, on_color_selected, lang_manager=self.lang)
            
            def edit_color():
                if selected_color_idx[0] is not None and working_colors:
                    current_color = working_colors[selected_color_idx[0]]
                    
                    if not COLOR_ADJUSTER_AVAILABLE:
                        # 폴백: 색상 피커 사용
                        color_result = colorchooser.askcolor(color=current_color, title=self.lang.get('edit_color_title'))
                        if color_result[1]:
                            working_colors[selected_color_idx[0]] = color_result[1]
                            draw_colors()
                    else:
                        # HSV 슬라이더 사용
                        def on_color_edited(new_hex):
                            working_colors[selected_color_idx[0]] = new_hex
                            draw_colors()
                        
                        SingleColorAdjusterDialog(editor_dialog, self.generator, current_color, on_color_edited, lang_manager=self.lang)
            
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
                self.log_action(f"Edited palette: {entry['name']}")
                editor_dialog.destroy()
            
            def update_button_states():
                # Enable/disable buttons based on selection
                # Allow adding colors even if nothing is selected
                add_btn.config(state='normal')
                if selected_color_idx[0] is not None and working_colors:
                    edit_btn.config(state='normal')
                    del_btn.config(state='normal')
                else:
                    edit_btn.config(state='disabled')
                    del_btn.config(state='disabled')
                
                # Enable HSV adjust if there are colors (regardless of selection)
                if working_colors:
                    hsv_btn.config(state='normal')
                else:
                    hsv_btn.config(state='disabled')
            
            def open_hsv_adjuster():
                """Open HSV adjuster for palette colors."""
                if not working_colors:
                    messagebox.showinfo(self.lang.get('info'), self.lang.get('msg_palette_has_no_colors'))
                    return
                
                if not COLOR_ADJUSTER_AVAILABLE:
                    messagebox.showerror(self.lang.get('error'), self.lang.get('msg_color_adjust_unavailable'))
                    return
                
                try:
                    # Convert hex to RGB
                    rgb_colors = []
                    for hex_color in working_colors:
                        try:
                            rgb = self.generator.hex_to_rgb(hex_color)
                            rgb_colors.append(rgb)
                        except Exception:
                            continue
                    
                    if not rgb_colors:
                        messagebox.showinfo(self.lang.get('info'), self.lang.get('msg_no_valid_colors'))
                        return
                    
                    # Callback to apply adjusted colors
                    def apply_adjusted_colors(adjusted_colors):
                        # Convert back to hex
                        new_colors = []
                        for rgb in adjusted_colors:
                            hex_color = self.generator.rgb_to_hex(rgb)
                            new_colors.append(hex_color)
                        
                        # Update working colors
                        working_colors.clear()
                        working_colors.extend(new_colors)
                        draw_colors()
                    
                    ColorAdjusterDialog(editor_dialog, self.generator, rgb_colors, apply_adjusted_colors)
                    
                except Exception as e:
                    messagebox.showerror(self.lang.get('error'), self.lang.get('msg_color_adjust_failed').format(error=str(e)))
            
            def sort_by_hue():
                """색조로 정렬"""
                import colorsys
                def get_hue(hex_color):
                    rgb = self.generator.hex_to_rgb(hex_color)
                    h, s, v = colorsys.rgb_to_hsv(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
                    return h
                working_colors.sort(key=get_hue)
                selected_color_idx[0] = None
                draw_colors()
            
            def sort_by_saturation():
                """채도로 정렬"""
                import colorsys
                def get_saturation(hex_color):
                    rgb = self.generator.hex_to_rgb(hex_color)
                    h, s, v = colorsys.rgb_to_hsv(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
                    return s
                working_colors.sort(key=get_saturation)
                selected_color_idx[0] = None
                draw_colors()
            
            def sort_by_luminance():
                """밸류(흑백 명도)로 정렬"""
                def get_luminance(hex_color):
                    rgb = self.generator.hex_to_rgb(hex_color)
                    # 흑백 변환 시 명도: 0.299*R + 0.587*G + 0.114*B
                    lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
                    return lum
                working_colors.sort(key=get_luminance)
                selected_color_idx[0] = None
                draw_colors()
            
            def reverse_order():
                """역순으로 정렬"""
                working_colors.reverse()
                selected_color_idx[0] = None
                draw_colors()
            
            # Bottom: buttons - 2 rows
            btn_frame = tk.Frame(editor_dialog)
            btn_frame.pack(fill='x', padx=10, pady=(5,5))
            
            # First row: Add/Edit/Delete/HSV Adjust
            row1_frame = tk.Frame(btn_frame)
            row1_frame.pack(fill='x', pady=(0, 5))
            
            left_btns = tk.Frame(row1_frame)
            left_btns.pack(side='left')
            add_btn = ttk.Button(left_btns, text=self.lang.get('add_color'), command=add_color, state='normal')
            add_btn.pack(side='left', padx=5)
            edit_btn = ttk.Button(left_btns, text=self.lang.get('edit_color'), command=edit_color, state='disabled')
            edit_btn.pack(side='left', padx=5)
            del_btn = ttk.Button(left_btns, text=self.lang.get('delete_color'), command=delete_color, state='disabled')
            del_btn.pack(side='left', padx=5)
            hsv_btn = ttk.Button(left_btns, text=self.lang.get('hsv_adjust'), command=open_hsv_adjuster, state='disabled')
            hsv_btn.pack(side='left', padx=5)
            
            # Right side of first row: Confirm/Cancel
            right_btns = tk.Frame(row1_frame)
            right_btns.pack(side='right')
            ttk.Button(right_btns, text=self.lang.get('confirm'), command=confirm).pack(side='left', padx=5)
            ttk.Button(right_btns, text=self.lang.get('cancel'), command=editor_dialog.destroy).pack(side='left', padx=5)
            
            # Second row: Sort buttons (centered)
            row2_frame = tk.Frame(btn_frame)
            row2_frame.pack(fill='x')
            
            sort_container = tk.Frame(row2_frame)
            sort_container.pack(expand=True)
            
            ttk.Button(sort_container, text=self.lang.get('sort_by_hue'), command=sort_by_hue).pack(side='left', padx=2)
            ttk.Button(sort_container, text=self.lang.get('sort_by_saturation'), command=sort_by_saturation).pack(side='left', padx=2)
            ttk.Button(sort_container, text=self.lang.get('sort_by_luminance'), command=sort_by_luminance).pack(side='left', padx=2)
            ttk.Button(sort_container, text=self.lang.get('sort_reverse'), command=reverse_order).pack(side='left', padx=2)
            
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), str(e))

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
                filetypes=[(self.lang.get('my_palette_file'), '*.mps'), (self.lang.get('all_files'), '*.*')],
                initialfile=entry['name']
            )
            if filename:
                import json
                import base64
                data = json.dumps({'name': entry['name'], 'colors': entry['colors']})
                encoded = base64.b64encode(data.encode('utf-8')).decode('utf-8')
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(encoded)
                self.log_action(f"Saved palette to MPS: {entry['name']}")
        except Exception as e:
            messagebox.showerror(self.lang.get('save_error_title'), self.lang.get('msg_save_failed').format(error=str(e)))
            self.log_action(f"Save palette failed: {str(e)}")

    def toggle_palette_view(self, idx):
        """Toggle between RGB and Value (luminance) view."""
        try:
            entry = self.saved_palettes[idx]
            # Toggle view mode (default is 'rgb')
            current_mode = entry.get('view_mode', 'rgb')
            entry['view_mode'] = 'value' if current_mode == 'rgb' else 'rgb'
            self.render_saved_list()
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), str(e))

    def export_palette_txt(self, idx):
        """Export palette colors to TXT file."""
        try:
            entry = self.saved_palettes[idx]
            colors = entry.get('colors', [])
            if not colors:
                messagebox.showinfo(self.lang.get('export_title'), self.lang.get('msg_palette_has_no_colors'))
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension='.txt',
                filetypes=[(self.lang.get('text_file'), '*.txt'), (self.lang.get('all_files'), '*.*')],
                initialfile=f"{entry['name']}.txt"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.lang.get('export_txt_palette_label').format(name=entry['name']) + "\n")
                    f.write(self.lang.get('export_txt_color_count_label').format(count=len(colors)) + "\n\n")
                    for i, color in enumerate(colors, 1):
                        f.write(f"{i}. {color}\n")
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_export_txt_failed').format(error=str(e)))

    def export_palette_png(self, idx):
        """Export palette colors as PNG image."""
        try:
            entry = self.saved_palettes[idx]
            colors = entry.get('colors', [])
            if not colors:
                messagebox.showinfo(self.lang.get('export_title'), self.lang.get('msg_palette_has_no_colors'))
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension='.png',
                filetypes=[(self.lang.get('png_image'), '*.png'), (self.lang.get('all_files'), '*.*')],
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
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_export_png_failed').format(error=str(e)))

    def generate(self):
        """Generate palette with comprehensive validation and error handling."""
        source_type = self.source_type.get()
        try:
            if source_type == 'ai':
                from ai_color_recommender import AISettings, AIColorRecommender
                
                settings = AISettings.load_settings(self.file_handler)
                api_key = settings.get('api_key', '')
                
                if not api_key:
                    messagebox.showwarning(self.lang.get('warning'), self.lang.get('msg_ai_api_key_required'))
                    return
                
                if not self.ai_recommender:
                    try:
                        self.ai_recommender = AIColorRecommender(api_key, lang=self.lang)
                    except Exception as e:
                        messagebox.showerror(self.lang.get('error'), self.lang.get('msg_ai_init_failed').format(error=str(e)))
                        return
                
                num_colors = settings.get('num_colors', 5)
                keywords = settings.get('keywords', '')
                
                # Show loading dialog
                loading_dialog = tk.Toplevel(self)
                loading_dialog.title(self.lang.get('ai_generating_title'))
                loading_dialog.geometry("300x100")
                loading_dialog.transient(self)
                loading_dialog.grab_set()
                
                ttk.Label(loading_dialog, text=self.lang.get('ai_generating'), 
                         font=('Segoe UI', 10)).pack(pady=20)
                
                progress = ttk.Progressbar(loading_dialog, mode='indeterminate', length=250)
                progress.pack(pady=10)
                progress.start(10)
                
                def generate_ai_palettes():
                    try:
                        new_palettes = self.ai_recommender.generate_palettes(
                            num_palettes=5,
                            keywords=keywords,
                            num_colors=num_colors
                        )
                        
                        self.after(0, lambda: self._finish_ai_generation(new_palettes, loading_dialog))
                    except Exception as e:
                        error_msg = str(e)
                        # Check for specific error types
                        if 'quota' in error_msg.lower() or '429' in error_msg:
                            error_key = 'ai_quota_exceeded'
                        elif 'invalid' in error_msg.lower() or '401' in error_msg or '403' in error_msg:
                            error_key = 'ai_api_invalid_key'
                        elif 'network' in error_msg.lower() or 'connection' in error_msg.lower():
                            error_key = 'ai_api_network_error'
                        else:
                            error_key = 'ai_generation_failed'
                        
                        self.after(0, lambda err=error_msg, key=error_key: self._handle_ai_error(err, loading_dialog, key))
                
                import threading
                thread = threading.Thread(target=generate_ai_palettes, daemon=True)
                thread.start()
                return
                    
            elif source_type == 'hex':
                hex_code = self.hex_entry.get().strip()
                
                if not self.validate_hex_color(hex_code):
                    raise ValueError(self.lang.get('msg_invalid_hex_prompt'))
                
                palette = self.generator.generate_palette(hex_code, source_type='hex')
                # store current palettes for saving
                self.current_palettes = [palette]
                self.log_action(f"Generated palette from HEX: {hex_code}")
            else:
                if not self.image_path:
                    raise ValueError(self.lang.get('msg_select_image_first'))
                
                # Validate image file still exists
                if not os.path.exists(self.image_path):
                    self.image_path = None
                    self.lbl_image.config(text=self.lang.get('no_image_label'))
                    raise ValueError(self.lang.get('msg_image_file_not_found'))
                
                # First estimate approximate distinct color count, then run k-means up to 5 clusters
                approx = self.generator.approximate_color_count(self.image_path, sample_size=1000)
                k = min(5, max(1, approx))  # Ensure k is at least 1
                main_colors = self.generator.extract_main_colors(self.image_path, num_colors=k)
                
                if not main_colors:
                    raise ValueError(self.lang.get('msg_extract_colors_failed'))
                
                # store extracted colors and only display them (top tabs) when Generate is pressed
                self.extracted_colors = main_colors
                palettes = [self.generator.generate_palette(c, source_type='rgb') for c in main_colors]
                # store current palettes for saving
                self.current_palettes = palettes
                self.log_action(f"Generated palette from image: {os.path.basename(self.image_path)}")
        except ValueError as e:
            messagebox.showerror(self.lang.get('input_error_title'), str(e))
            self.log_action(f"Generate validation error: {str(e)}")
            return
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_palette_generation_failed').format(error=str(e)))
            self.log_action(f"Generate error: {str(e)}")
            return

        self.clear_palette_display()
        # AI mode - display AI palettes
        if source_type == 'ai':
            self.display_ai_palettes(self.ai_palettes)
        # If HEX mode, show single palette; if image mode, show palettes for each representative color
        elif source_type == 'hex':
            palette = palette
            base = palette['base']
            if isinstance(base, list):
                base = tuple(base)
            base_hex = self.generator.rgb_to_hex(base)
            ttk.Label(self.palette_inner, text=self.lang.get('base_color_label'), font=('Segoe UI', 10, 'bold')).pack(anchor='w')
            self.draw_color_box(self.palette_inner, base_hex, self.lang.get('label_rgb').format(value=str(base)))

            # Display only selected harmony schemes
            scheme_labels = {
                'complementary': self.lang.get('complementary_label'),
                'analogous': self.lang.get('analogous_label'),
                'triadic': self.lang.get('triadic_label'),
                'monochromatic': self.lang.get('monochromatic'),
                'split_complementary': self.lang.get('split_complementary'),
                'square': self.lang.get('square'),
                'tetradic': self.lang.get('tetradic'),
                'double_complementary': self.lang.get('double_complementary')
            }

            for scheme in self.selected_schemes:
                if scheme.startswith('custom_'):
                    try:
                        from custom_harmony import CustomHarmonyManager
                        manager = CustomHarmonyManager(self.file_handler)
                        idx = int(scheme.split('_')[1])
                        
                        if idx < len(manager.harmonies):
                            harmony = manager.harmonies[idx]
                            colors = manager.apply_harmony(base_hex, idx)
                            label = harmony.get('name', self.lang.get('custom_harmony_default_name'))
                            
                            ttk.Label(self.palette_inner, text=label, font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(8,0), padx=0)
                            
                            for idx, color_hex in enumerate(colors, 1):
                                rgb = self.generator.hex_to_rgb(color_hex)
                                hx = color_hex
                                self.draw_color_box(
                                    self.palette_inner,
                                    hx,
                                    self.lang.get('label_numbered_rgb').format(i=idx, value=str(rgb)),
                                )
                    except (ImportError, IndexError, ValueError):
                        continue
                elif scheme not in palette:
                    continue
                else:
                    colors = palette[scheme]
                    label = scheme_labels.get(scheme, scheme)
                    
                    ttk.Label(self.palette_inner, text=label, font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(8,0), padx=0)
                    
                    # Handle single color vs list
                    if isinstance(colors, tuple) and len(colors) == 3 and all(isinstance(c, int) for c in colors):
                        # Single color (e.g., complementary)
                        hx = self.generator.rgb_to_hex(colors)
                        self.draw_color_box(self.palette_inner, hx, self.lang.get('label_rgb').format(value=str(colors)))
                    elif isinstance(colors, list) and len(colors) == 3 and all(isinstance(c, int) for c in colors):
                        # Single color as list
                        colors = tuple(colors)
                        hx = self.generator.rgb_to_hex(colors)
                        self.draw_color_box(self.palette_inner, hx, self.lang.get('label_rgb').format(value=str(colors)))
                    else:
                        # List of colors
                        for idx, col in enumerate(colors, 1):
                            if isinstance(col, list):
                                col = tuple(col)
                            hx = self.generator.rgb_to_hex(col)
                            self.draw_color_box(
                                self.palette_inner,
                                hx,
                                self.lang.get('label_numbered_rgb').format(i=idx, value=str(col)),
                            )
        else:
            # palettes is a list of palette dicts for the 5 main colors
            self.display_multiple_palettes(palettes)

    def _finish_ai_generation(self, new_palettes, loading_dialog):
        """Handle successful AI palette generation."""
        try:
            loading_dialog.destroy()
            
            self.ai_palettes.extend(new_palettes)
            self.current_palettes = self.ai_palettes
            self.log_action(f"Generated AI palettes: {len(new_palettes)} new palettes")
            
            self.clear_palette_display()
            self.display_ai_palettes(self.ai_palettes)
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_display_palettes_failed').format(error=str(e)))
    
    def _handle_ai_error(self, error_msg, loading_dialog, error_key='ai_generation_failed'):
        """Handle AI generation error."""
        try:
            loading_dialog.destroy()
        except:
            pass
        
        # Get localized error message
        if error_key == 'ai_generation_failed':
            message = self.lang.get(error_key).format(error=error_msg)
        else:
            message = self.lang.get(error_key)
        
        messagebox.showerror(self.lang.get('ai_error_title'), message)
        self.log_action(f"AI generation error: {error_msg}")

    def display_ai_palettes(self, palettes):
        """Display AI-generated color palettes."""
        if not palettes:
            ttk.Label(self.palette_inner, text=self.lang.get('ai_no_palettes'), 
                     font=('Segoe UI', 10)).pack(pady=20)
            return
        
        for i, palette_data in enumerate(palettes, start=1):
            # 딕셔너리 형식인지 확인 (새 형식)
            if isinstance(palette_data, dict):
                palette_name = palette_data.get('name', self.lang.get('ai_palette_name').format(i=i))
                palette_colors = palette_data.get('colors', [])
            else:
                # 리스트 형식 (구 형식, 하위 호환성)
                palette_name = self.lang.get('ai_palette_name').format(i=i)
                palette_colors = palette_data
            
            # Palette header
            ttk.Label(self.palette_inner, text=palette_name, 
                     font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(10 if i > 1 else 0, 5))
            
            # Draw color boxes with RGB format (기존 display_single_palette 방식과 동일)
            for j, color_hex in enumerate(palette_colors, start=1):
                # HEX를 RGB로 변환
                rgb = self.generator.hex_to_rgb(color_hex)
                label_text = self.lang.get('label_numbered_rgb').format(i=j, value=str(rgb))
                self.draw_color_box(self.palette_inner, color_hex, label_text, clickable=True)
            
            # Separator
            if i < len(palettes):
                ttk.Separator(self.palette_inner, orient='horizontal').pack(fill='x', pady=8)
    
    def display_single_palette(self, palette):
        """Display a single palette (for HEX mode)."""
        base = palette['base']
        if isinstance(base, list):
            base = tuple(base)
        base_hex = self.generator.rgb_to_hex(base)
        ttk.Label(self.palette_inner, text=self.lang.get('base_color_label'), font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.draw_color_box(self.palette_inner, base_hex, self.lang.get('label_rgb').format(value=str(base)))

        scheme_labels = {
            'complementary': self.lang.get('complementary_label'),
            'analogous': self.lang.get('analogous_label'),
            'triadic': self.lang.get('triadic_label'),
            'monochromatic': self.lang.get('monochromatic'),
            'split_complementary': self.lang.get('split_complementary'),
            'square': self.lang.get('square'),
            'tetradic': self.lang.get('tetradic'),
            'double_complementary': self.lang.get('double_complementary')
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
                self.draw_color_box(self.palette_inner, hx, self.lang.get('label_rgb').format(value=str(colors)))
            else:
                # Handle list of colors
                for idx, col in enumerate(colors, 1):
                    if isinstance(col, list):
                        col = tuple(col)
                    hx = self.generator.rgb_to_hex(col)
                    self.draw_color_box(
                        self.palette_inner,
                        hx,
                        self.lang.get('label_numbered_rgb').format(i=idx, value=str(col)),
                    )
    def display_multiple_palettes(self, palettes):
        """Display multiple palettes (for image mode)."""
        scheme_labels = {
            'complementary': self.lang.get('complementary'),
            'analogous': self.lang.get('analogous'),
            'triadic': self.lang.get('triadic'),
            'monochromatic': self.lang.get('monochromatic'),
            'split_complementary': self.lang.get('split_complementary'),
            'square': self.lang.get('square'),
            'tetradic': self.lang.get('tetradic'),
            'double_complementary': self.lang.get('double_complementary')
        }
        
        for i, p in enumerate(palettes, start=1):
            ttk.Label(self.palette_inner, text=f"{self.lang.get('representative_color')} {i}", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(6,0), padx=0)
            base = p['base']
            if isinstance(base, list):
                base = tuple(base)
            base_hex = self.generator.rgb_to_hex(base)
            self.draw_color_box(
                self.palette_inner,
                base_hex,
                f"{self.lang.get('base_color')} {self.lang.get('label_rgb').format(value=str(base))}",
            )

            for scheme in self.selected_schemes:
                # Handle custom harmonies
                if scheme.startswith('custom_'):
                    try:
                        from custom_harmony import CustomHarmonyManager
                        manager = CustomHarmonyManager(self.file_handler)
                        idx = int(scheme.split('_')[1])
                        
                        if idx < len(manager.harmonies):
                            harmony = manager.harmonies[idx]
                            colors = manager.apply_harmony(base_hex, idx)
                            label = harmony.get('name', self.lang.get('custom_harmony_default_name'))
                            
                            ttk.Label(self.palette_inner, text=f"  {label}", font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=0)
                            
                            for color_idx, color_hex in enumerate(colors, 1):
                                rgb = self.generator.hex_to_rgb(color_hex)
                                hx = color_hex
                                self.draw_color_box(
                                    self.palette_inner,
                                    hx,
                                    self.lang.get('label_numbered_rgb').format(i=color_idx, value=str(rgb)),
                                    clickable=True,
                                )
                    except (ImportError, IndexError, ValueError):
                        continue
                # Check if scheme exists in palette
                elif scheme not in p:
                    continue
                else:
                    colors = p[scheme]
                    label = scheme_labels.get(scheme, scheme)
                    
                    ttk.Label(self.palette_inner, text=f"  {label}", font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=0)
                    
                    if isinstance(colors, (tuple, list)) and len(colors) == 3 and all(isinstance(c, int) for c in colors):
                        if isinstance(colors, list):
                            colors = tuple(colors)
                        hx = self.generator.rgb_to_hex(colors)
                        self.draw_color_box(
                            self.palette_inner,
                            hx,
                            self.lang.get('label_rgb').format(value=str(colors)),
                            clickable=True,
                        )
                    else:
                        for idx, col in enumerate(colors, 1):
                            if isinstance(col, list):
                                col = tuple(col)
                            hx = self.generator.rgb_to_hex(col)
                            self.draw_color_box(
                                self.palette_inner,
                                hx,
                                self.lang.get('label_numbered_rgb').format(i=idx, value=str(col)),
                                clickable=True,
                            )

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
    
    def create_recent_color_tooltip(self, widgets, text):
        """Create a tooltip for recent color widgets.

        Notes:
        - Accepts a single widget or an iterable of widgets.
        - Uses a small delay + shared state to prevent missed tooltips and residue.
        """
        if isinstance(widgets, (list, tuple, set)):
            widget_list = list(widgets)
        else:
            widget_list = [widgets]

        tooltip_window = [None]
        show_after_id = [None]

        def destroy_tooltip():
            if tooltip_window[0] is not None:
                try:
                    tooltip_window[0].destroy()
                except Exception:
                    pass
                tooltip_window[0] = None

        def show_tooltip(x_root, y_root):
            destroy_tooltip()
            tooltip = tk.Toplevel(self)
            tooltip.wm_overrideredirect(True)
            try:
                tooltip.attributes('-topmost', True)
            except Exception:
                pass
            tooltip.wm_geometry(f"+{x_root + 10}+{y_root + 10}")
            label = tk.Label(
                tooltip,
                text=text,
                background='#ffffe0',
                relief='solid',
                borderwidth=1,
                font=('Arial', 9),
                justify='left',
            )
            label.pack()
            tooltip_window[0] = tooltip

        def on_enter(e):
            if show_after_id[0] is not None:
                try:
                    self.after_cancel(show_after_id[0])
                except Exception:
                    pass
                show_after_id[0] = None

            show_after_id[0] = self.after(120, lambda: show_tooltip(e.x_root, e.y_root))

        def on_leave(_e):
            if show_after_id[0] is not None:
                try:
                    self.after_cancel(show_after_id[0])
                except Exception:
                    pass
                show_after_id[0] = None
            destroy_tooltip()

        def on_motion(e):
            if tooltip_window[0] is not None:
                try:
                    tooltip_window[0].wm_geometry(f"+{e.x_root + 10}+{e.y_root + 10}")
                except Exception:
                    pass

        for w in widget_list:
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)
            w.bind('<Motion>', on_motion)

    def copy_palette(self):
        """Copy currently selected palette."""
        if self._saved_selected is None:
            messagebox.showinfo(self.lang.get('selection_required'), self.lang.get('select_palette_first'))
            return
        try:
            entry = self.saved_palettes[self._saved_selected]
            new_entry = {
                'name': f"{entry['name']}{self.lang.get('copy_suffix')}",
                'colors': entry['colors'].copy()
            }
            self.saved_palettes.append(new_entry)
            self._saved_selected = len(self.saved_palettes) - 1
            self.render_saved_list()
            self.mark_modified()
            self.log_action(f"Copied palette: {entry['name']}")
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), str(e))

    def load_palette(self):
        """Load palette from .mps file."""
        try:
            filename = filedialog.askopenfilename(
                title=self.lang.get('dialog_open_mps'),
                filetypes=[(self.lang.get('my_palette_file'), '*.mps'), (self.lang.get('all_files'), '*.*')]
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
                self.mark_modified()
                self.log_action(f"Loaded palette from MPS: {data['name']}")
        except Exception as e:
            messagebox.showerror(self.lang.get('load_error_title'), self.lang.get('msg_load_failed').format(error=str(e)))
            self.log_action(f"Load palette failed: {str(e)}")
    
    def open_color_adjuster(self):
        """Open color adjustment dialog for selected palette."""
        if self._saved_selected is None:
            messagebox.showinfo(self.lang.get('selection_required'), self.lang.get('select_palette_to_adjust'))
            return
        
        if not COLOR_ADJUSTER_AVAILABLE:
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_color_adjust_unavailable'))
            return
        
        try:
            entry = self.saved_palettes[self._saved_selected]
            colors = entry.get('colors', [])
            
            if not colors:
                messagebox.showinfo(self.lang.get('info'), self.lang.get('msg_palette_has_no_colors'))
                return
            
            # Convert hex to RGB
            rgb_colors = []
            for hex_color in colors:
                try:
                    rgb = self.generator.hex_to_rgb(hex_color)
                    rgb_colors.append(rgb)
                except Exception:
                    continue
            
            if not rgb_colors:
                messagebox.showinfo(self.lang.get('info'), self.lang.get('msg_no_valid_colors'))
                return
            
            # Open adjuster dialog
            def apply_adjusted_colors(adjusted_colors):
                # Convert back to hex
                new_colors = []
                for rgb in adjusted_colors:
                    hex_color = self.generator.rgb_to_hex(rgb)
                    new_colors.append(hex_color)
                
                entry['colors'] = new_colors
                self.render_saved_list()
                self.mark_modified()
                self.log_action(f"Adjusted colors for palette: {entry['name']}")
            
            ColorAdjusterDialog(self, self.generator, rgb_colors, apply_adjusted_colors)
            
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), self.lang.get('msg_color_adjust_failed').format(error=str(e)))
    
    def open_settings(self):
        """Open settings dialog."""
        dialog = tk.Toplevel(self)
        dialog.title(self.lang.get('dialog_settings'))
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Settings frame with padding
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Language settings
        ttk.Label(scrollable_frame, text=self.lang.get('settings_language_section'), font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0,10))
        
        lang_frame = ttk.Frame(scrollable_frame)
        lang_frame.pack(anchor='w', padx=10, pady=5, fill='x')
        ttk.Label(lang_frame, text=self.lang.get('language_label')).pack(side='left')
        current_lang = self.config_manager.get('language', 'ko')
        lang_var = tk.StringVar(value='한국어' if current_lang == 'ko' else 'English')
        lang_combo = ttk.Combobox(lang_frame, textvariable=lang_var, 
                                 values=['한국어', 'English'], 
                                 state='readonly', width=15)
        lang_combo.pack(side='left', padx=5)
        
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # Auto-save settings
        ttk.Label(scrollable_frame, text=self.lang.get('settings_autosave_section'), font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0,10))
        
        auto_save_var = tk.BooleanVar(value=self.config_manager.get('auto_save_enabled', True))
        ttk.Checkbutton(scrollable_frame, text=self.lang.get('settings_autosave_enable'), variable=auto_save_var).pack(anchor='w', padx=10)
        
        interval_frame = ttk.Frame(scrollable_frame)
        interval_frame.pack(anchor='w', padx=10, pady=5)
        ttk.Label(interval_frame, text=self.lang.get('settings_autosave_interval')).pack(side='left')
        interval_var = tk.IntVar(value=self.config_manager.get('auto_save_interval', 300))
        ttk.Spinbox(interval_frame, from_=60, to=3600, textvariable=interval_var, width=10).pack(side='left', padx=5)
        
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # K-means settings
        ttk.Label(scrollable_frame, text=self.lang.get('settings_extraction_section'), font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0,10))
        
        kmeans_frame = ttk.Frame(scrollable_frame)
        kmeans_frame.pack(anchor='w', padx=10, pady=5)
        ttk.Label(kmeans_frame, text=self.lang.get('settings_max_colors')).pack(side='left')
        max_colors_var = tk.IntVar(value=self.config_manager.get('kmeans_max_colors', 5))
        ttk.Spinbox(kmeans_frame, from_=2, to=10, textvariable=max_colors_var, width=10).pack(side='left', padx=5)
        
        filter_bg_var = tk.BooleanVar(value=self.config_manager.get('kmeans_filter_background', True))
        ttk.Checkbutton(scrollable_frame, text=self.lang.get('settings_filter_background'), variable=filter_bg_var).pack(anchor='w', padx=10, pady=5)
        
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # UI settings
        ttk.Label(scrollable_frame, text=self.lang.get('settings_ui_section'), font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0,10))
        
        window_frame = ttk.Frame(scrollable_frame)
        window_frame.pack(anchor='w', padx=10, pady=5)
        ttk.Label(window_frame, text=self.lang.get('settings_window_size')).pack(side='left')
        width_var = tk.IntVar(value=self.config_manager.get('window_width', 700))
        ttk.Spinbox(window_frame, from_=600, to=1200, textvariable=width_var, width=8).pack(side='left', padx=5)
        ttk.Label(window_frame, text=self.lang.get('settings_window_size_separator')).pack(side='left')
        height_var = tk.IntVar(value=self.config_manager.get('window_height', 520))
        ttk.Spinbox(window_frame, from_=400, to=900, textvariable=height_var, width=8).pack(side='left', padx=5)
        
        recent_files_frame = ttk.Frame(scrollable_frame)
        recent_files_frame.pack(anchor='w', padx=10, pady=5)
        ttk.Label(recent_files_frame, text=self.lang.get('settings_recent_files')).pack(side='left')
        max_recent_var = tk.IntVar(value=self.config_manager.get('max_recent_files', 10))
        ttk.Spinbox(recent_files_frame, from_=5, to=20, textvariable=max_recent_var, width=10).pack(side='left', padx=5)

        recent_colors_frame = ttk.Frame(scrollable_frame)
        recent_colors_frame.pack(anchor='w', padx=10, pady=5)
        ttk.Label(recent_colors_frame, text=self.lang.get('settings_recent_colors')).pack(side='left')
        max_recent_colors_var = tk.IntVar(value=self.config_manager.get('max_recent_colors', self.max_recent_colors))
        ttk.Spinbox(recent_colors_frame, from_=1, to=100, textvariable=max_recent_colors_var, width=10).pack(side='left', padx=5)
        
        # Spacer
        ttk.Frame(scrollable_frame, height=20).pack()
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        dialog.protocol("WM_DELETE_WINDOW", lambda: (canvas.unbind_all("<MouseWheel>"), dialog.destroy()))
        
        # Button frame (fixed at bottom, centered)
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(side='bottom', fill='x', padx=20, pady=10)
        
        # Center container for buttons
        btn_container = ttk.Frame(btn_frame)
        btn_container.pack(expand=True)
        
        def save_settings():
            # Save language
            new_lang = 'ko' if lang_var.get() == '한국어' else 'en'
            self.config_manager.set('language', new_lang)
            
            # Save other settings
            self.config_manager.set('auto_save_enabled', auto_save_var.get())
            self.config_manager.set('auto_save_interval', interval_var.get())
            self.config_manager.set('kmeans_max_colors', max_colors_var.get())
            self.config_manager.set('kmeans_filter_background', filter_bg_var.get())
            self.config_manager.set('window_width', width_var.get())
            self.config_manager.set('window_height', height_var.get())
            self.config_manager.set('max_recent_files', max_recent_var.get())
            self.config_manager.set('max_recent_colors', max(1, min(100, int(max_recent_colors_var.get()))))
            
            if self.config_manager.save_config():
                canvas.unbind_all("<MouseWheel>")
                messagebox.showinfo(self.lang.get('settings_saved_title'), self.lang.get('settings_saved'))
                self.log_action("Settings saved")
                
                # Apply auto-save settings immediately
                self.auto_save_enabled = auto_save_var.get()
                self.auto_save_interval = interval_var.get() * 1000
                if self.auto_save_enabled:
                    self.stop_auto_save()
                    self.start_auto_save()
                else:
                    self.stop_auto_save()

                # Apply recent colors max immediately
                try:
                    self.max_recent_colors = int(self.config_manager.get('max_recent_colors', self.max_recent_colors))
                except Exception:
                    self.max_recent_colors = 50
                self.max_recent_colors = max(1, min(100, self.max_recent_colors))
                if len(self.recent_colors) > self.max_recent_colors:
                    self.recent_colors = self.recent_colors[:self.max_recent_colors]
                    self.config_manager.set('recent_colors', self.recent_colors)
                    self.config_manager.save_config()
                self.update_recent_colors_display()
                
                dialog.destroy()
            else:
                messagebox.showerror(self.lang.get('settings_save_failed_title'), self.lang.get('settings_save_failed'))
        
        def cancel_settings():
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()
        
        ttk.Button(btn_container, text=self.lang.get('button_save'), command=save_settings).pack(side='left', padx=5)
        ttk.Button(btn_container, text=self.lang.get('button_cancel'), command=cancel_settings).pack(side='left', padx=5)
    
    def reset_settings(self):
        """Reset settings to default."""
        response = messagebox.askyesno(self.lang.get('reset_settings_title'), self.lang.get('msg_reset_settings_confirm'))
        if response:
            self.config_manager.reset_to_defaults()
            messagebox.showinfo(self.lang.get('reset_done_title'), self.lang.get('msg_settings_reset_done'))
            self.log_action("Settings reset to defaults")
    
    def apply_palette_to_image(self):
        """Apply palette to image with integrated preview window"""
        if not self.saved_palettes:
            messagebox.showwarning(self.lang.get('warning'), self.lang.get('msg_no_saved_palettes'))
            return
        
        # Create main dialog
        dialog = tk.Toplevel(self)
        dialog.title(self.lang.get('dialog_apply_palette'))
        dialog.geometry('600x500')
        dialog.transient(self)
        
        # State variables
        state = {
            'image_path': None,
            'original_image': None,
            'current_palette_idx': 0,
            'preview_photo': None,
            'recolored_cache': {},
        }

        recolorer = ImageRecolorer()
        
        # Top panel: palette selection
        top_frame = ttk.Frame(dialog, padding=10)
        top_frame.pack(fill='x')
        
        ttk.Label(top_frame, text=self.lang.get('recolor_select_palette'), font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        
        palette_names = [
            p.get('name', self.lang.get('palette_numbered').format(i=i + 1))
            for i, p in enumerate(self.saved_palettes)
        ]
        palette_var = tk.StringVar(value=palette_names[0])
        palette_combo = ttk.Combobox(top_frame, textvariable=palette_var, values=palette_names, state='readonly', width=30)
        palette_combo.pack(side='left', padx=5)
        palette_combo.current(0)  # Select first palette by default
        
        def on_palette_change(event):
            state['current_palette_idx'] = palette_combo.current()
            update_palette_display()
            if state['image_path']:  # Auto-update preview if image is loaded
                update_preview()
        
        palette_combo.bind('<<ComboboxSelected>>', on_palette_change)
        
        # Show selected palette colors
        palette_display = tk.Canvas(top_frame, width=150, height=30, bg='white', highlightthickness=1, highlightbackground='gray')
        palette_display.pack(side='left', padx=10)
        
        def update_palette_display():
            palette = self.saved_palettes[state['current_palette_idx']]
            colors = palette.get('colors', [])
            palette_display.delete('all')
            
            if not colors:
                # Draw checkerboard pattern for empty palette
                square_size = 10
                for y in range(0, 30, square_size):
                    for x in range(0, 150, square_size):
                        if (x // square_size + y // square_size) % 2 == 0:
                            palette_display.create_rectangle(x, y, x+square_size, y+square_size, fill='#E0E0E0', outline='')
                        else:
                            palette_display.create_rectangle(x, y, x+square_size, y+square_size, fill='white', outline='')
            else:
                # Draw color bars with equal width
                bar_width = 150 / len(colors)
                for i, color in enumerate(colors):
                    x1 = i * bar_width
                    x2 = (i + 1) * bar_width
                    palette_display.create_rectangle(x1, 0, x2, 30, fill=color, outline='')
        
        update_palette_display()
        
        # Control buttons
        btn_frame = ttk.Frame(dialog, padding=5)
        btn_frame.pack(fill='x')
        
        # Button references for state management
        btn_refs = {}
        
        def update_buttons():
            """Update button states based on current state"""
            has_image = state['image_path'] is not None
            palette = self.saved_palettes[state['current_palette_idx']]
            has_colors = len(palette.get('colors', [])) > 0
            
            # Enable/disable buttons
            btn_refs['view_original']['state'] = 'normal' if (has_image and has_colors) else 'disabled'
            btn_refs['save']['state'] = 'normal' if has_image else 'disabled'
        
        def load_image():
            file_path = filedialog.askopenfilename(
                title=self.lang.get('dialog_select_image_recolor'),
                filetypes=[
                    (self.lang.get('image_files'), '*.png *.jpg *.jpeg *.bmp *.gif'),
                    (self.lang.get('all_files'), '*.*'),
                ]
            )
            
            if file_path:
                try:
                    state['image_path'] = file_path
                    state['original_image'] = Image.open(file_path)
                    update_buttons()
                    update_preview()
                    self.log_action(f"Loaded image: {os.path.basename(file_path)}")
                except Exception as e:
                    messagebox.showerror(self.lang.get('error'), self.lang.get('msg_recolor_load_image_failed').format(error=str(e)))
        
        def view_original():
            if not state['image_path']:
                messagebox.showwarning(self.lang.get('warning'), self.lang.get('msg_load_image_first'))
                return
            
            palette = self.saved_palettes[state['current_palette_idx']]
            if not palette.get('colors') or len(palette['colors']) == 0:
                messagebox.showwarning(self.lang.get('warning'), self.lang.get('msg_empty_palette_cannot_apply'))
                return
            
            try:
                # Apply palette to get recolored image
                cache_key = (state['image_path'], state['current_palette_idx'])
                recolored = state['recolored_cache'].get(cache_key)
                if recolored is None:
                    recolored = recolorer.apply_palette_to_image(state['image_path'], palette['colors'])
                    state['recolored_cache'][cache_key] = recolored
                
                # Create window with exact recolored image size (no padding)
                orig_window = tk.Toplevel(dialog)
                orig_window.title(self.lang.get('recolor_view_original'))
                
                img_width, img_height = recolored.size
                orig_window.geometry(f'{img_width}x{img_height}')
                orig_window.resizable(False, False)
                
                canvas = tk.Canvas(orig_window, width=img_width, height=img_height, highlightthickness=0)
                canvas.pack()
                
                photo = ImageTk.PhotoImage(recolored)
                canvas.create_image(0, 0, image=photo, anchor='nw')
                canvas.image = photo
            except Exception as e:
                messagebox.showerror(self.lang.get('error'), self.lang.get('msg_recolor_display_failed').format(error=str(e)))
        
        def apply_and_update():
            update_preview()
        
        def save_image():
            if not state['image_path']:
                messagebox.showwarning(self.lang.get('warning'), self.lang.get('msg_load_image_first'))
                return
            
            output_path = filedialog.asksaveasfilename(
                title=self.lang.get('dialog_save_recolored'),
                defaultextension='.png',
                filetypes=[
                    (self.lang.get('png_image'), '*.png'),
                    (self.lang.get('jpeg_image'), '*.jpg'),
                    (self.lang.get('all_files'), '*.*'),
                ]
            )
            
            if output_path:
                try:
                    palette = self.saved_palettes[state['current_palette_idx']]

                    cache_key = (state['image_path'], state['current_palette_idx'])
                    recolored = state['recolored_cache'].get(cache_key)
                    if recolored is None:
                        recolored = recolorer.apply_palette_to_image(state['image_path'], palette['colors'])
                        state['recolored_cache'][cache_key] = recolored
                    recolored.save(output_path)
                    messagebox.showinfo(self.lang.get('saved_title'), self.lang.get('msg_recolor_save_success').format(path=output_path))
                    self.log_action(f"Saved recolored image: {os.path.basename(output_path)}")
                except Exception as e:
                    messagebox.showerror(self.lang.get('save_error_title'), self.lang.get('msg_recolor_save_failed').format(error=str(e)))
        
        ttk.Button(btn_frame, text=self.lang.get('recolor_load_image'), command=load_image).pack(side='left', padx=2)
        btn_refs['view_original'] = ttk.Button(btn_frame, text=self.lang.get('recolor_view_original'), command=view_original, state='disabled')
        btn_refs['view_original'].pack(side='left', padx=2)
        btn_refs['save'] = ttk.Button(btn_frame, text=self.lang.get('button_save'), command=save_image, state='disabled')
        btn_refs['save'].pack(side='left', padx=10)
        ttk.Button(btn_frame, text=self.lang.get('button_close'), command=dialog.destroy).pack(side='right', padx=2)
        
        # Preview canvas (larger size for better centering, black background)
        preview_frame = ttk.LabelFrame(dialog, text=self.lang.get('recolor_preview'), padding=10)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create a container frame for centering
        canvas_container = tk.Frame(preview_frame, bg='#f0f0f0')
        canvas_container.pack(fill='both', expand=True)
        
        preview_canvas = tk.Canvas(canvas_container, width=520, height=380, bg='black', highlightthickness=1, highlightbackground='gray')
        preview_canvas.place(relx=0.5, rely=0.5, anchor='center')
        
        def update_preview():
            if not state['image_path']:
                return
            
            try:
                palette = self.saved_palettes[state['current_palette_idx']]
                
                # Validate palette has colors
                if not palette.get('colors') or len(palette['colors']) == 0:
                    preview_canvas.delete('all')
                    preview_canvas.create_text(260, 190, text=self.lang.get('recolor_empty_palette'), fill='white', font=('Arial', 12))
                    return
                
                # Preview: recolor a downscaled copy for speed
                preview_img = None
                try:
                    if state.get('original_image') is not None:
                        preview_img = state['original_image'].copy()
                except Exception:
                    preview_img = None

                if preview_img is None:
                    preview_img = Image.open(state['image_path'])

                preview_img.thumbnail((520, 380), Image.Resampling.LANCZOS)
                img_copy = recolorer.apply_palette_to_pil_image(preview_img, palette['colors'])
                
                # Update canvas (centered at canvas center: 260, 190)
                preview_canvas.delete('all')
                state['preview_photo'] = ImageTk.PhotoImage(img_copy)
                preview_canvas.create_image(260, 190, image=state['preview_photo'], anchor='center')
                
                # Update palette display
                update_palette_display()
                
            except Exception as e:
                messagebox.showerror(self.lang.get('error'), self.lang.get('msg_recolor_preview_failed').format(error=str(e)))
        
        # Initialize dialog state
        dialog.after(100, lambda: [
            palette_combo.current(0),
            update_palette_display(),
            update_buttons()
        ])
    
    def open_custom_harmony(self):
        """Open custom color harmony editor."""
        try:
            from custom_harmony import CustomHarmonyManager
            
            # 현재 선택된 색상을 베이스로 사용
            current_color = self.hex_entry.get() or '#FF0000'
            
            manager = CustomHarmonyManager(self.file_handler)
            CustomHarmonyDialog(self, manager, self.generator, current_color, self.lang)
            
        except ImportError:
            messagebox.showerror(self.lang.get('error'), self.lang.get('custom_harmony_module_missing'))
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), self.lang.get('custom_harmony_open_failed').format(error=str(e)))
    
    def open_ai_settings(self):
        """Open AI settings dialog."""
        try:
            from ai_color_recommender import AISettings, AIColorRecommender
            
            # Load current settings
            settings = AISettings.load_settings(self.file_handler)
            
            # Create dialog
            dialog = tk.Toplevel(self)
            dialog.title(self.lang.get('dialog_ai_settings'))
            dialog.geometry('500x420')
            dialog.transient(self)
            dialog.grab_set()
            
            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill='both', expand=True)
            
            # API Key
            ttk.Label(main_frame, text=self.lang.get('ai_api_key_label'), font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
            api_key_var = tk.StringVar(value=settings.get('api_key', ''))
            api_entry = ttk.Entry(main_frame, textvariable=api_key_var, width=50, show='*')
            api_entry.pack(fill='x', pady=(0, 5))
            
            ttk.Label(main_frame, text=self.lang.get('ai_api_help'), 
                     font=('Arial', 8)).pack(anchor='w', pady=(0, 15))
            
            # Number of colors
            ttk.Label(main_frame, text=self.lang.get('ai_colors_per_palette'), font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
            num_colors_var = tk.IntVar(value=settings.get('num_colors', 5))
            num_colors_spinbox = ttk.Spinbox(main_frame, from_=3, to=10, textvariable=num_colors_var, width=10)
            num_colors_spinbox.pack(anchor='w', pady=(0, 15))
            
            # Keywords
            ttk.Label(main_frame, text=self.lang.get('ai_keywords_label'), font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
            keywords_var = tk.StringVar(value=settings.get('keywords', ''))
            ttk.Entry(main_frame, textvariable=keywords_var, width=50).pack(fill='x', pady=(0, 5))
            ttk.Label(main_frame, text=self.lang.get('ai_keywords_example'), font=('Arial', 8)).pack(anchor='w', pady=(0, 15))
            
            # Test button
            test_result_var = tk.StringVar(value='')
            test_label = ttk.Label(main_frame, textvariable=test_result_var, foreground='blue')
            test_label.pack(pady=5)
            
            def test_api():
                api_key = api_key_var.get().strip()
                if not api_key:
                    test_result_var.set(self.lang.get('ai_api_invalid_key'))
                    test_label.config(foreground='red')
                    return
                
                try:
                    recommender = AIColorRecommender(api_key, lang=self.lang)
                    success, message = recommender.test_api_key()
                    if success:
                        test_result_var.set('✓ ' + self.lang.get('ai_api_test_success'))
                        test_label.config(foreground='green')
                    else:
                        # Check for specific errors
                        if 'quota' in message.lower() or '429' in message:
                            error_text = self.lang.get('ai_quota_exceeded')
                        elif 'invalid' in message.lower() or '401' in message or '403' in message:
                            error_text = self.lang.get('ai_api_invalid_key')
                        elif 'network' in message.lower() or 'connection' in message.lower():
                            error_text = self.lang.get('ai_api_network_error')
                        else:
                            error_text = self.lang.get('ai_api_test_failed').format(error=message)
                        
                        test_result_var.set('✗ ' + error_text)
                        test_label.config(foreground='red')
                except Exception as e:
                    error_str = str(e)
                    if 'quota' in error_str.lower() or '429' in error_str:
                        error_text = self.lang.get('ai_quota_exceeded')
                    elif 'network' in error_str.lower() or 'connection' in error_str.lower():
                        error_text = self.lang.get('ai_api_network_error')
                    else:
                        error_text = self.lang.get('ai_api_test_failed').format(error=error_str)
                    
                    test_result_var.set(f'✗ {error_text}')
                    test_label.config(foreground='red')
            
            # Buttons
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(pady=20, side='bottom')
            
            ttk.Button(btn_frame, text=self.lang.get('ai_test_api'), command=test_api).pack(side='left', padx=5)
            
            def save_settings():
                api_key = api_key_var.get().strip()
                num_colors = num_colors_var.get()
                keywords = keywords_var.get().strip()
                
                if AISettings.save_settings(self.file_handler, api_key, num_colors, keywords):
                    # Initialize AI recommender
                    if api_key:
                        try:
                            self.ai_recommender = AIColorRecommender(api_key, lang=self.lang)
                            messagebox.showinfo(self.lang.get('settings_saved_title'), self.lang.get('settings_saved').split('\n')[0])
                        except Exception as e:
                            messagebox.showerror(self.lang.get('ai_error_title'), self.lang.get('msg_ai_init_failed').format(error=str(e)))
                    else:
                        messagebox.showinfo(self.lang.get('settings_saved_title'), self.lang.get('settings_saved').split('\n')[0])
                    dialog.destroy()
                else:
                    messagebox.showerror(self.lang.get('settings_save_failed_title'), self.lang.get('settings_save_failed'))
            
            ttk.Button(btn_frame, text=self.lang.get('button_save'), command=save_settings).pack(side='left', padx=5)
            ttk.Button(btn_frame, text=self.lang.get('button_cancel'), command=dialog.destroy).pack(side='left', padx=5)
            
        except ImportError:
            messagebox.showerror(self.lang.get('error'), self.lang.get('ai_module_missing'))
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), self.lang.get('ai_settings_open_failed').format(error=str(e)))
    
    def open_preset_palettes(self):
        """Open preset palettes browser."""
        try:
            from preset_generator import PresetPaletteGenerator
            
            def use_preset_palette(colors, name):
                """Callback when preset palette is selected."""
                palette_data = {
                    'name': name,
                    'colors': colors,
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.saved_palettes.append(palette_data)
                self.render_saved_list()
                self.mark_modified()
                self.log_action(f"Added preset palette: {name}")
                messagebox.showinfo(
                    self.lang.get('preset_added_title'),
                    self.lang.get('preset_added_msg').format(name=name),
                )
            
            PresetPaletteBrowserDialog(self, use_preset_palette, PresetPaletteGenerator, self.file_handler, self.lang)
            
        except ImportError:
            messagebox.showerror(self.lang.get('error'), self.lang.get('preset_module_missing'))
        except Exception as e:
            messagebox.showerror(self.lang.get('error'), self.lang.get('preset_open_failed').format(error=str(e)))


class CustomHarmonyDialog:
    """Custom harmony editor dialog (UI lives in main.py; logic lives in custom_harmony.py)."""

    def __init__(self, parent, manager, generator, base_color='#FF0000', lang_manager=None):
        self.parent = parent
        self.manager = manager
        self.generator = generator
        self.base_color = base_color
        self.lang = lang_manager if lang_manager else LanguageManager('ko')
        self.current_harmony_idx = None
        self.colors = []

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(self.lang.get('dialog_custom_harmony'))
        self.dialog.geometry('1000x650')
        self.dialog.transient(parent)

        self.create_ui()
        self.load_harmony_list()

    def create_ui(self):
        left_frame = ttk.Frame(self.dialog, padding=10)
        left_frame.pack(side='left', fill='both', expand=False)

        ttk.Label(left_frame, text=self.lang.get('saved_harmonies'), font=('Arial', 10, 'bold')).pack(anchor='w')

        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill='both', expand=True, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        self.harmony_listbox = tk.Listbox(list_frame, width=25, yscrollcommand=scrollbar.set)
        self.harmony_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.harmony_listbox.yview)

        self.harmony_listbox.bind('<<ListboxSelect>>', self.on_harmony_select)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text=self.lang.get('new_harmony'), command=self.new_harmony).pack(side='left', padx=2)
        self.btn_delete_harmony = ttk.Button(
            btn_frame,
            text=self.lang.get('delete_harmony'),
            command=self.delete_harmony,
            state='disabled',
        )
        self.btn_delete_harmony.pack(side='left', padx=2)

        right_frame = ttk.Frame(self.dialog, padding=10)
        right_frame.pack(side='right', fill='both', expand=True)

        name_frame = ttk.Frame(right_frame)
        name_frame.pack(fill='x', pady=5)
        ttk.Label(name_frame, text=self.lang.get('harmony_name')).pack(side='left')
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var, width=30).pack(side='left', padx=5)

        ttk.Label(right_frame, text=self.lang.get('edit_color'), font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))

        colors_frame = ttk.LabelFrame(right_frame, text=self.lang.get('colors'), padding=10)
        colors_frame.pack(fill='both', expand=True, pady=5)

        colors_list_frame = ttk.Frame(colors_frame)
        colors_list_frame.pack(fill='both', expand=True)

        self.colors_listbox = tk.Listbox(colors_list_frame, height=6)
        self.colors_listbox.pack(side='left', fill='both', expand=True)
        self.colors_listbox.bind('<<ListboxSelect>>', self.on_color_select)

        colors_scroll = ttk.Scrollbar(colors_list_frame, orient='vertical', command=self.colors_listbox.yview)
        colors_scroll.pack(side='right', fill='y')
        self.colors_listbox.config(yscrollcommand=colors_scroll.set)

        colors_btn_frame = ttk.Frame(colors_frame)
        colors_btn_frame.pack(fill='x', pady=5)
        ttk.Button(colors_btn_frame, text=self.lang.get('add_hsv_color'), command=self.add_hsv_color).pack(side='left', padx=2)
        ttk.Button(colors_btn_frame, text=self.lang.get('add_fixed_color'), command=self.add_fixed_color).pack(side='left', padx=2)

        self.btn_edit_color = ttk.Button(colors_btn_frame, text=self.lang.get('edit'), command=self.edit_color, state='disabled')
        self.btn_edit_color.pack(side='left', padx=2)
        self.btn_delete_color = ttk.Button(colors_btn_frame, text=self.lang.get('delete_harmony'), command=self.delete_color, state='disabled')
        self.btn_delete_color.pack(side='left', padx=2)
        ttk.Button(colors_btn_frame, text=self.lang.get('move_up'), command=lambda: self.move_color(-1)).pack(side='left', padx=2)
        ttk.Button(colors_btn_frame, text=self.lang.get('move_down'), command=lambda: self.move_color(1)).pack(side='left', padx=2)

        preview_frame = ttk.LabelFrame(right_frame, text=self.lang.get('preview'), padding=0)
        preview_frame.pack(fill='x', pady=5)

        self.preview_canvas = tk.Canvas(preview_frame, height=80, bg='white', highlightthickness=0, bd=0)
        self.preview_canvas.pack(fill='both', expand=True, padx=0, pady=0)

        bottom_frame = ttk.Frame(right_frame)
        bottom_frame.pack(fill='x', pady=10)
        ttk.Button(bottom_frame, text=self.lang.get('button_save'), command=self.save_current_harmony).pack(side='left', padx=5)
        ttk.Button(bottom_frame, text=self.lang.get('button_close'), command=self.dialog.destroy).pack(side='right', padx=5)

    def load_harmony_list(self):
        self.harmony_listbox.delete(0, tk.END)
        for harmony in self.manager.harmonies:
            self.harmony_listbox.insert(tk.END, harmony.get('name', self.lang.get('unnamed')))

    def on_harmony_select(self, _event):
        selection = self.harmony_listbox.curselection()
        if not selection:
            self.btn_delete_harmony.config(state='disabled')
            return

        idx = selection[0]
        self.current_harmony_idx = idx
        harmony = self.manager.harmonies[idx]

        self.name_var.set(harmony.get('name', ''))
        self.colors = harmony.get('colors', []).copy()
        self.update_colors_display()
        self.update_preview()
        self.btn_delete_harmony.config(state='normal')

    def on_color_select(self, _event):
        selection = self.colors_listbox.curselection()
        state = 'normal' if selection else 'disabled'
        self.btn_edit_color.config(state=state)
        self.btn_delete_color.config(state=state)

    def new_harmony(self):
        self.current_harmony_idx = None
        self.name_var.set(self.lang.get('new_harmony'))
        self.colors = []
        self.update_colors_display()
        self.update_preview()
        self.btn_delete_harmony.config(state='disabled')

    def delete_harmony(self):
        selection = self.harmony_listbox.curselection()
        if not selection:
            messagebox.showwarning(self.lang.get('warning'), self.lang.get('custom_harmony_select_delete'))
            return

        idx = selection[0]
        if messagebox.askyesno(self.lang.get('confirm'), self.lang.get('custom_harmony_confirm_delete')):
            self.manager.delete_harmony(idx)
            self.load_harmony_list()
            self.new_harmony()

    def add_hsv_color(self):
        self._open_hsv_dialog()

    def add_fixed_color(self):
        color = colorchooser.askcolor(title=self.lang.get('add_fixed_color'))
        if color and color[1]:
            self.colors.append({'type': 'fixed', 'color': color[1]})
            self.update_colors_display()
            self.update_preview()

    def edit_color(self):
        selection = self.colors_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        color_data = self.colors[idx]
        if color_data.get('type') == 'hsv':
            self._open_hsv_dialog(idx, color_data)
            return

        color = colorchooser.askcolor(color=color_data.get('color', '#FFFFFF'), title=self.lang.get('edit'))
        if color and color[1]:
            self.colors[idx] = {'type': 'fixed', 'color': color[1]}
            self.update_colors_display()
            self.update_preview()

    def delete_color(self):
        selection = self.colors_listbox.curselection()
        if selection:
            self.colors.pop(selection[0])
            self.update_colors_display()
            self.update_preview()

    def move_color(self, direction):
        selection = self.colors_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        new_idx = idx + direction
        if 0 <= new_idx < len(self.colors):
            self.colors[idx], self.colors[new_idx] = self.colors[new_idx], self.colors[idx]
            self.update_colors_display()
            self.colors_listbox.selection_clear(0, tk.END)
            self.colors_listbox.selection_set(new_idx)
            self.update_preview()

    def _create_slider(self, parent, label_text, var, min_val, max_val, unit):
        ttk.Label(parent, text=label_text, font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=(0, 15))

        ttk.Scale(row, from_=min_val, to=max_val, orient='horizontal', variable=var).pack(side='left', fill='x', expand=True)
        value_label = ttk.Label(row, width=8)
        value_label.pack(side='right', padx=5)

        def refresh(*_args):
            if unit == '°':
                value_label.config(text=f"{var.get():.0f}{unit}")
            else:
                value_label.config(text=f"{var.get():+.0f}{unit}")

        var.trace('w', refresh)
        refresh()

    def _update_hsv_preview(self, canvas, h_offset, s_offset, v_offset):
        try:
            base_rgb = self.generator.hex_to_rgb(self.base_color)
            base_h, base_s, base_v = colorsys.rgb_to_hsv(base_rgb[0] / 255, base_rgb[1] / 255, base_rgb[2] / 255)

            new_h = (base_h + h_offset / 360) % 1.0
            new_s = max(0, min(1, base_s + s_offset / 100))
            new_v = max(0, min(1, base_v + v_offset / 100))

            rgb = colorsys.hsv_to_rgb(new_h, new_s, new_v)
            hex_color = self.generator.rgb_to_hex(tuple(int(c * 255) for c in rgb))

            canvas.delete('all')
            canvas_width = canvas.winfo_width() or 450
            canvas.create_rectangle(0, 0, canvas_width, 50, fill=hex_color, outline='')
        except Exception:
            pass

    def _open_hsv_dialog(self, edit_index=None, existing_data=None):
        is_edit = edit_index is not None
        dlg = tk.Toplevel(self.dialog)
        dlg.title(self.lang.get('edit') if is_edit else self.lang.get('add_hsv_color'))
        dlg.geometry('500x400')
        dlg.transient(self.dialog)
        dlg.grab_set()

        main = ttk.Frame(dlg, padding=20)
        main.pack(fill='both', expand=False)

        h_val = (existing_data or {}).get('h_offset', 0)
        s_val = (existing_data or {}).get('s_offset', 0)
        v_val = (existing_data or {}).get('v_offset', 0)

        h_var = tk.DoubleVar(value=h_val)
        s_var = tk.DoubleVar(value=s_val)
        v_var = tk.DoubleVar(value=v_val)

        self._create_slider(main, self.lang.get('hue'), h_var, -180, 180, '°')
        self._create_slider(main, self.lang.get('saturation'), s_var, -100, 100, '%')
        self._create_slider(main, self.lang.get('value'), v_var, -100, 100, '%')

        ttk.Label(main, text=self.lang.get('preview'), font=('Arial', 9)).pack(anchor='w', pady=(10, 5))
        preview = tk.Canvas(main, height=50, bg='white', highlightthickness=1, highlightbackground='gray')
        preview.pack(fill='x', pady=(0, 15))

        def update_preview(*_args):
            self._update_hsv_preview(preview, h_var.get(), s_var.get(), v_var.get())

        for var in (h_var, s_var, v_var):
            var.trace('w', update_preview)
        update_preview()

        btns = ttk.Frame(main)
        btns.pack(side='bottom', pady=(20, 0))

        def confirm():
            color_data = {'type': 'hsv', 'h_offset': h_var.get(), 's_offset': s_var.get(), 'v_offset': v_var.get()}
            if is_edit:
                self.colors[edit_index] = color_data
            else:
                self.colors.append(color_data)
            self.update_colors_display()
            self.update_preview()
            dlg.destroy()

        ttk.Button(btns, text=self.lang.get('ok'), command=confirm, width=10).pack(side='left', padx=5)
        ttk.Button(btns, text=self.lang.get('button_cancel'), command=dlg.destroy, width=10).pack(side='left', padx=5)

    def update_colors_display(self):
        self.colors_listbox.delete(0, tk.END)
        for i, color_data in enumerate(self.colors):
            if color_data.get('type') == 'hsv':
                h = color_data.get('h_offset', 0)
                s = color_data.get('s_offset', 0)
                v = color_data.get('v_offset', 0)
                text = self.lang.get('custom_harmony_hsv_item').format(i=i + 1, h=h, s=s, v=v)
            else:
                hex_color = color_data.get('color', '#FFFFFF')
                text = self.lang.get('custom_harmony_fixed_item').format(i=i + 1, hex=hex_color)
            self.colors_listbox.insert(tk.END, text)

    def update_preview(self):
        self.preview_canvas.delete('all')
        if not self.colors:
            return

        try:
            from custom_harmony import CustomHarmonyManager

            temp_harmony = {'name': 'Preview', 'colors': self.colors}
            temp_manager = CustomHarmonyManager(self.manager.file_handler)
            temp_manager.harmonies = [temp_harmony]
            colors = temp_manager.apply_harmony(self.base_color, 0)

            if not colors:
                return

            self.preview_canvas.update_idletasks()
            canvas_width = self.preview_canvas.winfo_width() or 800
            box_width = canvas_width / len(colors)
            for i, color in enumerate(colors):
                x1 = i * box_width
                x2 = (i + 1) * box_width
                self.preview_canvas.create_rectangle(x1, 0, x2, 80, fill=color, outline='')
        except Exception:
            pass

    def save_current_harmony(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning(self.lang.get('warning'), self.lang.get('custom_harmony_name_required'))
            return
        if not self.colors:
            messagebox.showwarning(self.lang.get('warning'), self.lang.get('custom_harmony_color_required'))
            return

        harmony_data = {'name': name, 'colors': self.colors}
        if self.current_harmony_idx is not None:
            self.manager.update_harmony(self.current_harmony_idx, harmony_data)
        else:
            self.manager.add_harmony(harmony_data)

        self.load_harmony_list()
        messagebox.showinfo(self.lang.get('done'), self.lang.get('custom_harmony_saved'))


class PresetPaletteBrowserDialog:
    """Preset palette browser dialog (UI lives in main.py)."""

    def __init__(self, parent, callback, preset_generator_cls, file_handler, lang_manager=None):
        self.callback = callback
        self.file_handler = file_handler
        self.lang = lang_manager or LanguageManager('en')
        self.preset_generator_cls = preset_generator_cls

        self.all_palettes = []
        self.filtered_palettes = []
        self.current_tag_filter = None
        self.color_search_filter = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(self.lang.get('dialog_preset_palettes'))
        self.dialog.geometry('680x600')
        self.dialog.transient(parent)

        self._load_palettes()
        self._create_widgets()
        self._update_palette_list()

    def _load_palettes(self):
        try:
            self.all_palettes = self.preset_generator_cls.load_palettes(self.file_handler, 'preset_palettes.dat')
        except Exception:
            self.all_palettes = []

        self.current_tag_filter = self._all_text()

    def _all_text(self):
        return self.lang.get('preset_all')

    def _create_widgets(self):
        toolbar = ttk.Frame(self.dialog)
        toolbar.pack(fill='x', padx=10, pady=10)

        ttk.Label(toolbar, text=self.lang.get('preset_filter')).pack(side='left', padx=5)

        self.tag_var = tk.StringVar(value=self._all_text())
        tags = self._get_all_tags()
        tag_combo = ttk.Combobox(toolbar, textvariable=self.tag_var, values=tags, width=20, state='readonly')
        tag_combo.pack(side='left', padx=5)
        tag_combo.bind('<<ComboboxSelected>>', lambda _e: self._filter_by_tag())

        ttk.Button(
            toolbar,
            text=self.lang.get('preset_search_color'),
            command=self._search_by_color,
        ).pack(side='left', padx=10)

        ttk.Button(
            toolbar,
            text=self.lang.get('preset_reset_filter'),
            command=self._clear_filters,
        ).pack(side='left', padx=5)

        self.info_label = ttk.Label(toolbar)
        self.info_label.pack(side='right', padx=5)

        content_frame = ttk.Frame(self.dialog)
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(content_frame, bg='white', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(content_frame, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind('<Configure>', lambda _e: self._update_scroll_region())
        self._window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw', width=640)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')

        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind('<Enter>', lambda _e: self.canvas.bind_all('<MouseWheel>', self._on_mousewheel))
        self.canvas.bind('<Leave>', lambda _e: self.canvas.unbind_all('<MouseWheel>'))

        btn_bar = ttk.Frame(self.dialog)
        btn_bar.pack(fill='x', padx=10, pady=10)
        ttk.Button(btn_bar, text=self.lang.get('button_close'), command=self.dialog.destroy).pack(
            side='right', padx=5
        )

    def _on_canvas_configure(self, event):
        try:
            self.canvas.itemconfigure(self._window_id, width=event.width)
        except Exception:
            pass

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def _update_scroll_region(self):
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _get_all_tags(self):
        tags = {self._all_text()}
        for palette in self.all_palettes:
            tags.update(palette.get('tags', []))
        return sorted(list(tags))

    def _filter_by_tag(self):
        self.current_tag_filter = self.tag_var.get()
        self._update_palette_list()

    def _search_by_color(self):
        color = colorchooser.askcolor(title=self.lang.get('preset_pick_search_color'))
        if color and color[0]:
            self.color_search_filter = color[0]
            self._update_palette_list()

    def _clear_filters(self):
        self.tag_var.set(self._all_text())
        self.current_tag_filter = self._all_text()
        self.color_search_filter = None
        self._update_palette_list()

    @staticmethod
    def _color_similarity(rgb1, rgb2):
        r1, g1, b1 = rgb1
        r2, g2, b2 = rgb2
        distance = ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
        max_distance = (255 ** 2 * 3) ** 0.5
        return (1 - distance / max_distance) * 100

    @staticmethod
    def _hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def _update_palette_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        all_text = self._all_text()
        self.filtered_palettes = []
        for palette in self.all_palettes:
            if self.current_tag_filter and self.current_tag_filter != all_text:
                if self.current_tag_filter not in palette.get('tags', []):
                    continue

            if self.color_search_filter:
                found_similar = False
                for hex_color in palette.get('colors', []):
                    rgb = self._hex_to_rgb(hex_color)
                    if self._color_similarity(self.color_search_filter, rgb) >= 95:
                        found_similar = True
                        break
                if not found_similar:
                    continue

            self.filtered_palettes.append(palette)

        self.info_label.config(
            text=self.lang.get('preset_count').format(current=len(self.filtered_palettes), total=len(self.all_palettes))
        )

        for palette in self.filtered_palettes[:100]:
            self._create_palette_widget(palette)

        self._update_scroll_region()

    def _create_palette_widget(self, palette):
        frame = ttk.Frame(self.scrollable_frame, relief='solid', borderwidth=1)
        frame.pack(fill='x', padx=5, pady=3)

        header = ttk.Frame(frame)
        header.pack(fill='x', padx=5, pady=3)

        ttk.Label(header, text=palette.get('name', ''), font=('Segoe UI', 9, 'bold')).pack(side='left')

        tags_text = ', '.join(palette.get('tags', []))
        ttk.Label(
            header,
            text=self.lang.get('preset_tags_format').format(tags=tags_text),
            font=('Arial', 7),
            foreground='gray',
        ).pack(side='left', padx=5)

        ttk.Button(
            header,
            text=self.lang.get('preset_use'),
            command=lambda p=palette: self._use_palette(p),
        ).pack(side='right')

        colors_frame = tk.Frame(frame, height=40)
        colors_frame.pack(fill='x', padx=5, pady=3)
        colors_frame.pack_propagate(False)

        for color in palette.get('colors', []):
            swatch = tk.Canvas(colors_frame, width=110, height=35, bg=color, highlightthickness=1, highlightbackground='gray')
            swatch.pack(side='left', padx=2)
            swatch.create_text(55, 17, text=color, fill='white' if self._is_dark(color) else 'black', font=('Arial', 8))

    def _is_dark(self, hex_color):
        rgb = self._hex_to_rgb(hex_color)
        luminance = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
        return luminance < 128

    def _use_palette(self, palette):
        if self.callback:
            self.callback(palette.get('colors', []), palette.get('name', ''))
        self.dialog.destroy()


class ColorAdjusterDialog:
    """Palette-level color adjuster dialog (UI lives in main.py)."""

    def __init__(self, parent, generator, palette_colors, callback, lang_manager=None):
        self.generator = generator
        self.original_colors = palette_colors.copy()
        self.current_colors = palette_colors.copy()
        self.callback = callback

        self.lang = lang_manager or getattr(parent, 'lang', None) or LanguageManager('en')

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(self.lang.get('color_adjuster_title'))
        self.dialog.geometry("450x420")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        preview_frame = ttk.LabelFrame(self.dialog, text=self.lang.get('preview'), padding=10)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.preview_canvas = tk.Canvas(preview_frame, height=120, bg='white')
        self.preview_canvas.pack(fill='both', expand=True, anchor='center')

        control_frame = ttk.Frame(self.dialog, padding=10)
        control_frame.pack(fill='both', expand=True, padx=10)

        ttk.Label(control_frame, text=f"{self.lang.get('brightness')}:").grid(row=0, column=0, sticky='w', pady=5)
        self.brightness_var = tk.DoubleVar(value=0)
        ttk.Scale(
            control_frame,
            from_=-0.5,
            to=0.5,
            variable=self.brightness_var,
            orient='horizontal',
            command=lambda _v: self.update_preview(),
        ).grid(row=0, column=1, sticky='ew', padx=5, pady=5)

        ttk.Label(control_frame, text=f"{self.lang.get('saturation')}:").grid(row=1, column=0, sticky='w', pady=5)
        self.saturation_var = tk.DoubleVar(value=0)
        ttk.Scale(
            control_frame,
            from_=-0.5,
            to=0.5,
            variable=self.saturation_var,
            orient='horizontal',
            command=lambda _v: self.update_preview(),
        ).grid(row=1, column=1, sticky='ew', padx=5, pady=5)

        ttk.Label(control_frame, text=f"{self.lang.get('hue')}:").grid(row=2, column=0, sticky='w', pady=5)
        self.hue_var = tk.DoubleVar(value=0)
        ttk.Scale(
            control_frame,
            from_=-180,
            to=180,
            variable=self.hue_var,
            orient='horizontal',
            command=lambda _v: self.update_preview(),
        ).grid(row=2, column=1, sticky='ew', padx=5, pady=5)

        ttk.Label(control_frame, text=f"{self.lang.get('warmth')}:").grid(row=3, column=0, sticky='w', pady=5)
        self.warmth_var = tk.DoubleVar(value=0)
        ttk.Scale(
            control_frame,
            from_=-30,
            to=30,
            variable=self.warmth_var,
            orient='horizontal',
            command=lambda _v: self.update_preview(),
        ).grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        ttk.Label(control_frame, text=self.lang.get('warmth_hint'), font=('Arial', 8)).grid(row=3, column=2, sticky='w')

        ttk.Label(control_frame, text=f"{self.lang.get('contrast')}:").grid(row=4, column=0, sticky='w', pady=5)
        self.contrast_var = tk.DoubleVar(value=0)
        ttk.Scale(
            control_frame,
            from_=-0.3,
            to=0.3,
            variable=self.contrast_var,
            orient='horizontal',
            command=lambda _v: self.update_preview(),
        ).grid(row=4, column=1, sticky='ew', padx=5, pady=5)

        control_frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text=self.lang.get('reset'), command=self.reset).pack(side='left', padx=5)
        ttk.Button(btn_frame, text=self.lang.get('apply'), command=self.apply).pack(side='left', padx=5)
        ttk.Button(btn_frame, text=self.lang.get('cancel'), command=self.dialog.destroy).pack(side='left', padx=5)

        self.update_preview()

    def update_preview(self):
        brightness = self.brightness_var.get()
        saturation = self.saturation_var.get()
        hue = self.hue_var.get()
        warmth = self.warmth_var.get()
        contrast = self.contrast_var.get()

        self.current_colors = []
        for rgb in self.original_colors:
            adjusted = self.generator.adjust_hue(rgb, hue)
            if warmth != 0 and apply_warmth is not None:
                adjusted = apply_warmth(adjusted, warmth)
            adjusted = self.generator.adjust_saturation(adjusted, saturation)
            adjusted = self.generator.adjust_brightness(adjusted, brightness)
            if contrast != 0 and apply_contrast is not None:
                adjusted = apply_contrast(adjusted, contrast)
            self.current_colors.append(adjusted)

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

    def reset(self):
        self.brightness_var.set(0)
        self.saturation_var.set(0)
        self.hue_var.set(0)
        self.warmth_var.set(0)
        self.contrast_var.set(0)
        self.update_preview()

    def apply(self):
        self.callback(self.current_colors)
        self.dialog.destroy()


class SingleColorAdjusterDialog:
    """Single-color HSV adjuster dialog (UI lives in main.py)."""

    def __init__(self, parent, generator, initial_color_hex, callback, lang_manager=None):
        self.generator = generator
        self.initial_hex = initial_color_hex
        self.callback = callback
        self.lang = lang_manager or getattr(parent, 'lang', None) or LanguageManager('en')

        initial_rgb = generator.hex_to_rgb(initial_color_hex)
        r, g, b = initial_rgb
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(self.lang.get('hsv_dialog_title'))
        self.dialog.geometry("450x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        preview_frame = ttk.LabelFrame(self.dialog, text=self.lang.get('preview'), padding=10)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.preview_canvas = tk.Canvas(preview_frame, height=100, bg='white')
        self.preview_canvas.pack(fill='both', expand=True)

        control_frame = ttk.Frame(self.dialog, padding=10)
        control_frame.pack(fill='both', expand=True, padx=10)

        ttk.Label(control_frame, text=f"{self.lang.get('hue')}:").grid(row=0, column=0, sticky='w', pady=5)
        self.hue_var = tk.DoubleVar(value=h * 360)
        ttk.Scale(
            control_frame,
            from_=0,
            to=360,
            variable=self.hue_var,
            orient='horizontal',
            command=lambda _v: self.update_preview(),
        ).grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        self.hue_label = ttk.Label(control_frame, text=f"{int(h * 360)}°")
        self.hue_label.grid(row=0, column=2, sticky='w', padx=5)

        ttk.Label(control_frame, text=f"{self.lang.get('saturation')}:").grid(row=1, column=0, sticky='w', pady=5)
        self.saturation_var = tk.DoubleVar(value=s * 100)
        ttk.Scale(
            control_frame,
            from_=0,
            to=100,
            variable=self.saturation_var,
            orient='horizontal',
            command=lambda _v: self.update_preview(),
        ).grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self.sat_label = ttk.Label(control_frame, text=f"{int(s * 100)}%")
        self.sat_label.grid(row=1, column=2, sticky='w', padx=5)

        ttk.Label(control_frame, text=f"{self.lang.get('value')}:").grid(row=2, column=0, sticky='w', pady=5)
        self.value_var = tk.DoubleVar(value=v * 100)
        ttk.Scale(
            control_frame,
            from_=0,
            to=100,
            variable=self.value_var,
            orient='horizontal',
            command=lambda _v: self.update_preview(),
        ).grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        self.val_label = ttk.Label(control_frame, text=f"{int(v * 100)}%")
        self.val_label.grid(row=2, column=2, sticky='w', padx=5)

        control_frame.columnconfigure(1, weight=1)

        info_frame = ttk.Frame(self.dialog, padding=10)
        info_frame.pack(fill='x', padx=10)

        self.rgb_label = ttk.Label(info_frame, text=self.lang.get('label_rgb').format(value=initial_rgb))
        self.rgb_label.pack(anchor='w')
        self.hex_label = ttk.Label(info_frame, text=self.lang.get('label_hex').format(value=initial_color_hex))
        self.hex_label.pack(anchor='w')

        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text=self.lang.get('reset'), command=self.reset).pack(side='left', padx=5)
        ttk.Button(btn_frame, text=self.lang.get('apply'), command=self.apply).pack(side='left', padx=5)
        ttk.Button(btn_frame, text=self.lang.get('cancel'), command=self.dialog.destroy).pack(side='left', padx=5)

        self.update_preview()

    def update_preview(self):
        h = self.hue_var.get() / 360.0
        s = self.saturation_var.get() / 100.0
        v = self.value_var.get() / 100.0

        self.hue_label.config(text=f"{int(h * 360)}°")
        self.sat_label.config(text=f"{int(s * 100)}%")
        self.val_label.config(text=f"{int(v * 100)}%")

        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        rgb = (int(r * 255), int(g * 255), int(b * 255))
        hex_color = self.generator.rgb_to_hex(rgb)

        self.rgb_label.config(text=self.lang.get('label_rgb').format(value=rgb))
        self.hex_label.config(text=self.lang.get('label_hex').format(value=hex_color))

        self.preview_canvas.delete('all')
        width = self.preview_canvas.winfo_width()
        if width < 10:
            width = 430
        self.preview_canvas.create_rectangle(0, 0, width, 100, fill=hex_color, outline='')
        self.current_hex = hex_color

    def reset(self):
        initial_rgb = self.generator.hex_to_rgb(self.initial_hex)
        r, g, b = initial_rgb
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self.hue_var.set(h * 360)
        self.saturation_var.set(s * 100)
        self.value_var.set(v * 100)
        self.update_preview()

    def apply(self):
        self.callback(self.current_hex)
        self.dialog.destroy()

if __name__ == "__main__":
    app = PaletteApp()
    app.mainloop()