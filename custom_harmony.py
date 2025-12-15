"""
커스텀 색상 조합 관리 모듈 (리메이크)
HSV 슬라이더와 고정 색상만 사용하는 간단한 시스템
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import colorsys


class CustomHarmonyManager:
    """커스텀 색상 조합 관리 클래스"""
    
    def __init__(self, file_handler):
        self.file_handler = file_handler
        self.harmonies = self.load_harmonies()
    
    def load_harmonies(self):
        """저장된 조합 불러오기 (FileHandler 사용)"""
        return self.file_handler.load_data_file('custom_harmonies.dat', default=[])
    
    def save_harmonies(self):
        """조합 저장하기 (FileHandler 사용)"""
        return self.file_handler.save_data_file('custom_harmonies.dat', self.harmonies)
    
    def add_harmony(self, harmony_data):
        """새 조합 추가"""
        self.harmonies.append(harmony_data)
        return self.save_harmonies()
    
    def update_harmony(self, index, harmony_data):
        """조합 업데이트"""
        if 0 <= index < len(self.harmonies):
            self.harmonies[index] = harmony_data
            return self.save_harmonies()
        return False
    
    def delete_harmony(self, index):
        """조합 삭제"""
        if 0 <= index < len(self.harmonies):
            self.harmonies.pop(index)
            return self.save_harmonies()
        return False
    
    def apply_harmony(self, base_color_hex, harmony_index):
        """조합 규칙을 적용하여 색상 목록 생성"""
        if not (0 <= harmony_index < len(self.harmonies)):
            return []
        
        harmony = self.harmonies[harmony_index]
        colors_data = harmony.get('colors', [])
        
        # HEX to RGB
        base_rgb = self.hex_to_rgb(base_color_hex)
        base_h, base_s, base_v = colorsys.rgb_to_hsv(base_rgb[0]/255, base_rgb[1]/255, base_rgb[2]/255)
        
        colors = []
        for color_data in colors_data:
            color_type = color_data.get('type')
            
            if color_type == 'hsv':
                # HSV 슬라이더 값 적용
                h_offset = color_data.get('h_offset', 0) / 360  # -180~180도를 0~1로 변환
                s_offset = color_data.get('s_offset', 0) / 100  # -100~100%를 -1~1로 변환
                v_offset = color_data.get('v_offset', 0) / 100  # -100~100%를 -1~1로 변환
                
                new_h = (base_h + h_offset) % 1.0
                new_s = max(0, min(1, base_s + s_offset))
                new_v = max(0, min(1, base_v + v_offset))
                
                rgb = colorsys.hsv_to_rgb(new_h, new_s, new_v)
                colors.append(self.rgb_to_hex(tuple(int(c * 255) for c in rgb)))
            
            elif color_type == 'fixed':
                # 고정 색상
                fixed_color = color_data.get('color', '#FFFFFF')
                colors.append(fixed_color)
        
        return colors
    
    @staticmethod
    def hex_to_rgb(hex_color):
        """HEX를 RGB로 변환"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(rgb):
        """RGB를 HEX로 변환"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)


class CustomHarmonyDialog:
    """커스텀 색상 조합 편집 다이얼로그"""
    
    def __init__(self, parent, manager, generator, base_color='#FF0000'):
        self.parent = parent
        self.manager = manager
        self.generator = generator
        self.base_color = base_color
        self.current_harmony_idx = None
        self.colors = []
        
        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title('커스텀 색상 조합')
        self.dialog.geometry('1000x650')
        self.dialog.transient(parent)
        
        self.create_ui()
        self.load_harmony_list()
    
    def create_ui(self):
        """UI 생성"""
        # 좌측: 저장된 조합 목록
        left_frame = ttk.Frame(self.dialog, padding=10)
        left_frame.pack(side='left', fill='both', expand=False)
        
        ttk.Label(left_frame, text='저장된 조합', font=('Arial', 10, 'bold')).pack(anchor='w')
        
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
        ttk.Button(btn_frame, text='새 조합', command=self.new_harmony).pack(side='left', padx=2)
        self.btn_delete_harmony = ttk.Button(btn_frame, text='삭제', command=self.delete_harmony, state='disabled')
        self.btn_delete_harmony.pack(side='left', padx=2)
        
        # 우측: 편집 영역
        right_frame = ttk.Frame(self.dialog, padding=10)
        right_frame.pack(side='right', fill='both', expand=True)
        
        # 조합 이름
        name_frame = ttk.Frame(right_frame)
        name_frame.pack(fill='x', pady=5)
        ttk.Label(name_frame, text='조합 이름:').pack(side='left')
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var, width=30).pack(side='left', padx=5)
        
        # 색상 편집
        ttk.Label(right_frame, text='색상 목록', font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        
        colors_frame = ttk.LabelFrame(right_frame, text='색상', padding=10)
        colors_frame.pack(fill='both', expand=True, pady=5)
        
        # 색상 리스트
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
        ttk.Button(colors_btn_frame, text='HSV 색상 추가', command=self.add_hsv_color).pack(side='left', padx=2)
        ttk.Button(colors_btn_frame, text='고정 색상 추가', command=self.add_fixed_color).pack(side='left', padx=2)
        self.btn_edit_color = ttk.Button(colors_btn_frame, text='수정', command=self.edit_color, state='disabled')
        self.btn_edit_color.pack(side='left', padx=2)
        self.btn_delete_color = ttk.Button(colors_btn_frame, text='삭제', command=self.delete_color, state='disabled')
        self.btn_delete_color.pack(side='left', padx=2)
        ttk.Button(colors_btn_frame, text='위로', command=lambda: self.move_color(-1)).pack(side='left', padx=2)
        ttk.Button(colors_btn_frame, text='아래로', command=lambda: self.move_color(1)).pack(side='left', padx=2)
        
        # 미리보기
        preview_frame = ttk.LabelFrame(right_frame, text='미리보기', padding=0)
        preview_frame.pack(fill='x', pady=5)
        
        self.preview_canvas = tk.Canvas(preview_frame, height=80, bg='white', highlightthickness=0, bd=0)
        self.preview_canvas.pack(fill='both', expand=True, padx=0, pady=0)
        
        # 하단 버튼
        bottom_frame = ttk.Frame(right_frame)
        bottom_frame.pack(fill='x', pady=10)
        ttk.Button(bottom_frame, text='저장', command=self.save_current_harmony).pack(side='left', padx=5)
        ttk.Button(bottom_frame, text='닫기', command=self.dialog.destroy).pack(side='right', padx=5)
    
    def load_harmony_list(self):
        """조합 목록 로드"""
        self.harmony_listbox.delete(0, tk.END)
        for harmony in self.manager.harmonies:
            self.harmony_listbox.insert(tk.END, harmony.get('name', 'Unnamed'))
    
    def on_harmony_select(self, event):
        """조합 선택"""
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
    
    def on_color_select(self, event):
        """색상 선택"""
        selection = self.colors_listbox.curselection()
        if not selection:
            self.btn_edit_color.config(state='disabled')
            self.btn_delete_color.config(state='disabled')
            return
        
        self.btn_edit_color.config(state='normal')
        self.btn_delete_color.config(state='normal')
    
    def new_harmony(self):
        """새 조합 생성"""
        self.current_harmony_idx = None
        self.name_var.set('새 조합')
        self.colors = []
        self.update_colors_display()
        self.update_preview()
    
    def delete_harmony(self):
        """조합 삭제"""
        selection = self.harmony_listbox.curselection()
        if not selection:
            messagebox.showwarning('경고', '삭제할 조합을 선택하세요.')
            return
        
        idx = selection[0]
        if messagebox.askyesno('확인', '정말 삭제하시겠습니까?'):
            self.manager.delete_harmony(idx)
            self.load_harmony_list()
            self.new_harmony()
    
    def add_hsv_color(self):
        """HSV 색상 추가"""
        self._open_hsv_dialog()
    
    def add_fixed_color(self):
        """고정 색상 추가"""
        color = colorchooser.askcolor(title="색상 선택")
        if color[1]:  # HEX 값
            self.colors.append({'type': 'fixed', 'color': color[1]})
            self.update_colors_display()
            self.update_preview()
    
    def edit_color(self):
        """색상 수정"""
        selection = self.colors_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        color_data = self.colors[idx]
        
        if color_data['type'] == 'hsv':
            self._open_hsv_dialog(idx, color_data)
        else:  # fixed
            color = colorchooser.askcolor(
                color=color_data.get('color', '#FFFFFF'),
                title="색상 선택"
            )
            if color[1]:
                self.colors[idx] = {'type': 'fixed', 'color': color[1]}
                self.update_colors_display()
                self.update_preview()
    
    def delete_color(self):
        """색상 삭제"""
        selection = self.colors_listbox.curselection()
        if selection:
            idx = selection[0]
            self.colors.pop(idx)
            self.update_colors_display()
            self.update_preview()
    
    def move_color(self, direction):
        """색상 순서 변경"""
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
    
    def _open_hsv_dialog(self, edit_index=None, existing_data=None):
        """HSV 슬라이더 다이얼로그"""
        is_edit = edit_index is not None
        
        dialog = tk.Toplevel(self.dialog)
        dialog.title('HSV 색상 수정' if is_edit else 'HSV 색상 추가')
        dialog.geometry('450x350')
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # 기존 값 가져오기
        if existing_data:
            h_val = existing_data.get('h_offset', 0)
            s_val = existing_data.get('s_offset', 0)
            v_val = existing_data.get('v_offset', 0)
        else:
            h_val = 0
            s_val = 0
            v_val = 0
        
        # Hue 슬라이더
        ttk.Label(main_frame, text='색조 (Hue) 오프셋:', font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        h_frame = ttk.Frame(main_frame)
        h_frame.pack(fill='x', pady=(0, 15))
        
        h_var = tk.DoubleVar(value=h_val)
        h_slider = ttk.Scale(h_frame, from_=-180, to=180, orient='horizontal', variable=h_var)
        h_slider.pack(side='left', fill='x', expand=True)
        h_label = ttk.Label(h_frame, text=f'{h_val:.0f}°', width=8)
        h_label.pack(side='right', padx=5)
        
        def update_h_label(*args):
            h_label.config(text=f'{h_var.get():.0f}°')
        h_var.trace('w', update_h_label)
        
        # Saturation 슬라이더
        ttk.Label(main_frame, text='채도 (Saturation) 오프셋:', font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        s_frame = ttk.Frame(main_frame)
        s_frame.pack(fill='x', pady=(0, 15))
        
        s_var = tk.DoubleVar(value=s_val)
        s_slider = ttk.Scale(s_frame, from_=-100, to=100, orient='horizontal', variable=s_var)
        s_slider.pack(side='left', fill='x', expand=True)
        s_label = ttk.Label(s_frame, text=f'{s_val:+.0f}%', width=8)
        s_label.pack(side='right', padx=5)
        
        def update_s_label(*args):
            s_label.config(text=f'{s_var.get():+.0f}%')
        s_var.trace('w', update_s_label)
        
        # Value/Brightness 슬라이더
        ttk.Label(main_frame, text='명도 (Value/Brightness) 오프셋:', font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        v_frame = ttk.Frame(main_frame)
        v_frame.pack(fill='x', pady=(0, 15))
        
        v_var = tk.DoubleVar(value=v_val)
        v_slider = ttk.Scale(v_frame, from_=-100, to=100, orient='horizontal', variable=v_var)
        v_slider.pack(side='left', fill='x', expand=True)
        v_label = ttk.Label(v_frame, text=f'{v_val:+.0f}%', width=8)
        v_label.pack(side='right', padx=5)
        
        def update_v_label(*args):
            v_label.config(text=f'{v_var.get():+.0f}%')
        v_var.trace('w', update_v_label)
        
        # 미리보기
        preview_label = ttk.Label(main_frame, text='미리보기:', font=('Arial', 9))
        preview_label.pack(anchor='w', pady=(10, 5))
        
        preview_canvas = tk.Canvas(main_frame, height=40, bg='white', highlightthickness=1, highlightbackground='gray')
        preview_canvas.pack(fill='x', pady=(0, 15))
        
        def update_preview(*args):
            try:
                # 베이스 색상 가져오기
                base_rgb = CustomHarmonyManager.hex_to_rgb(self.base_color)
                base_h, base_s, base_v = colorsys.rgb_to_hsv(base_rgb[0]/255, base_rgb[1]/255, base_rgb[2]/255)
                
                # HSV 오프셋 적용
                new_h = (base_h + h_var.get() / 360) % 1.0
                new_s = max(0, min(1, base_s + s_var.get() / 100))
                new_v = max(0, min(1, base_v + v_var.get() / 100))
                
                # RGB로 변환
                rgb = colorsys.hsv_to_rgb(new_h, new_s, new_v)
                hex_color = CustomHarmonyManager.rgb_to_hex(tuple(int(c * 255) for c in rgb))
                
                # 미리보기 업데이트
                preview_canvas.delete('all')
                preview_canvas.create_rectangle(0, 0, 450, 40, fill=hex_color, outline='')
            except Exception:
                pass
        
        h_var.trace('w', update_preview)
        s_var.trace('w', update_preview)
        v_var.trace('w', update_preview)
        update_preview()
        
        # 버튼
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        def confirm():
            color_data = {
                'type': 'hsv',
                'h_offset': h_var.get(),
                's_offset': s_var.get(),
                'v_offset': v_var.get()
            }
            
            if is_edit:
                self.colors[edit_index] = color_data
            else:
                self.colors.append(color_data)
            
            self.update_colors_display()
            self.update_preview()
            dialog.destroy()
        
        ttk.Button(btn_frame, text='확인', command=confirm).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='취소', command=dialog.destroy).pack(side='left', padx=5)
    
    def update_colors_display(self):
        """색상 목록 표시 업데이트"""
        self.colors_listbox.delete(0, tk.END)
        for i, color_data in enumerate(self.colors):
            if color_data['type'] == 'hsv':
                h = color_data.get('h_offset', 0)
                s = color_data.get('s_offset', 0)
                v = color_data.get('v_offset', 0)
                text = f"{i+1}. HSV (H:{h:+.0f}°, S:{s:+.0f}%, V:{v:+.0f}%)"
            else:  # fixed
                hex_color = color_data.get('color', '#FFFFFF')
                text = f"{i+1}. 고정 색상: {hex_color}"
            
            self.colors_listbox.insert(tk.END, text)
    
    def update_preview(self):
        """미리보기 업데이트"""
        self.preview_canvas.delete('all')
        
        # 임시 매니저로 미리보기 색상 생성
        temp_harmony = {'name': 'Preview', 'colors': self.colors}
        temp_manager = CustomHarmonyManager(self.manager.file_handler)
        temp_manager.harmonies = [temp_harmony]
        
        try:
            colors = temp_manager.apply_harmony(self.base_color, 0)
            
            if colors:
                # Update canvas to get actual width
                self.preview_canvas.update_idletasks()
                canvas_width = self.preview_canvas.winfo_width()
                if canvas_width <= 1:  # Canvas not yet rendered
                    canvas_width = 800
                
                box_width = canvas_width / len(colors)
                for i, color in enumerate(colors):
                    x1 = i * box_width
                    x2 = (i + 1) * box_width
                    self.preview_canvas.create_rectangle(x1, 0, x2, 80, fill=color, outline='')
        except Exception:
            pass
    
    def save_current_harmony(self):
        """현재 조합 저장"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning('경고', '조합 이름을 입력하세요.')
            return
        
        if not self.colors:
            messagebox.showwarning('경고', '최소 하나의 색상을 추가하세요.')
            return
        
        harmony_data = {
            'name': name,
            'colors': self.colors
        }
        
        if self.current_harmony_idx is not None:
            # 기존 조합 업데이트
            self.manager.update_harmony(self.current_harmony_idx, harmony_data)
        else:
            # 새 조합 추가
            self.manager.add_harmony(harmony_data)
        
        self.load_harmony_list()
        messagebox.showinfo('완료', '조합이 저장되었습니다.')
