"""
커스텀 색상 조합 관리 모듈
사용자가 직접 색상 조합 규칙을 만들고 저장할 수 있음
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import colorsys


class CustomHarmonyManager:
    """커스텀 색상 조합 관리 클래스"""
    
    def __init__(self, config_file='custom_harmonies.json'):
        self.config_file = config_file
        self.harmonies = self.load_harmonies()
    
    def load_harmonies(self):
        """저장된 조합 불러오기"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def save_harmonies(self):
        """조합 저장하기"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.harmonies, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
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
        rules = harmony.get('rules', [])
        
        # HEX to RGB
        base_rgb = self.hex_to_rgb(base_color_hex)
        h, s, v = colorsys.rgb_to_hsv(base_rgb[0]/255, base_rgb[1]/255, base_rgb[2]/255)
        
        colors = []
        for rule in rules:
            rule_type = rule.get('type')
            
            if rule_type == 'base':
                # 베이스 색상 그대로
                colors.append(base_color_hex)
            
            elif rule_type == 'hue_offset':
                # 색조 오프셋
                offset = rule.get('value', 0) / 360
                new_h = (h + offset) % 1.0
                rgb = colorsys.hsv_to_rgb(new_h, s, v)
                colors.append(self.rgb_to_hex(tuple(int(c * 255) for c in rgb)))
            
            elif rule_type == 'complementary':
                # 보색 (각도 지정 가능)
                angle = rule.get('angle', 180) / 360
                new_h = (h + angle) % 1.0
                rgb = colorsys.hsv_to_rgb(new_h, s, v)
                colors.append(self.rgb_to_hex(tuple(int(c * 255) for c in rgb)))
            
            elif rule_type == 'saturation':
                # 채도 조정
                offset = rule.get('value', 0) / 100
                new_s = max(0, min(1, s + offset))
                rgb = colorsys.hsv_to_rgb(h, new_s, v)
                colors.append(self.rgb_to_hex(tuple(int(c * 255) for c in rgb)))
            
            elif rule_type == 'brightness':
                # 명도 조정
                offset = rule.get('value', 0) / 100
                new_v = max(0, min(1, v + offset))
                rgb = colorsys.hsv_to_rgb(h, s, new_v)
                colors.append(self.rgb_to_hex(tuple(int(c * 255) for c in rgb)))
            
            elif rule_type == 'fixed':
                # 고정 색상
                fixed_color = rule.get('color', '#FFFFFF')
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
    
    RULE_TYPES = [
        ('베이스 색상', 'base'),
        ('색조 오프셋 (Hue)', 'hue_offset'),
        ('보색 (각도 지정)', 'complementary'),
        ('채도 조정', 'saturation'),
        ('명도 조정', 'brightness'),
        ('고정 색상', 'fixed')
    ]
    
    def __init__(self, parent, manager, generator, base_color='#FF0000'):
        self.parent = parent
        self.manager = manager
        self.generator = generator
        self.base_color = base_color
        self.current_harmony_idx = None
        self.rules = []
        
        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title('커스텀 색상 조합')
        self.dialog.geometry('900x600')
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
        ttk.Button(btn_frame, text='삭제', command=self.delete_harmony).pack(side='left', padx=2)
        
        # 우측: 편집 영역
        right_frame = ttk.Frame(self.dialog, padding=10)
        right_frame.pack(side='right', fill='both', expand=True)
        
        # 조합 이름
        name_frame = ttk.Frame(right_frame)
        name_frame.pack(fill='x', pady=5)
        ttk.Label(name_frame, text='조합 이름:').pack(side='left')
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var, width=30).pack(side='left', padx=5)
        
        # 규칙 편집
        ttk.Label(right_frame, text='색상 생성 규칙', font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        
        rules_frame = ttk.LabelFrame(right_frame, text='규칙 목록', padding=10)
        rules_frame.pack(fill='both', expand=True, pady=5)
        
        # 규칙 리스트
        self.rules_listbox = tk.Listbox(rules_frame, height=8)
        self.rules_listbox.pack(fill='both', expand=True)
        
        rules_btn_frame = ttk.Frame(rules_frame)
        rules_btn_frame.pack(fill='x', pady=5)
        ttk.Button(rules_btn_frame, text='규칙 추가', command=self.add_rule).pack(side='left', padx=2)
        ttk.Button(rules_btn_frame, text='규칙 수정', command=self.edit_rule).pack(side='left', padx=2)
        ttk.Button(rules_btn_frame, text='규칙 삭제', command=self.delete_rule).pack(side='left', padx=2)
        ttk.Button(rules_btn_frame, text='위로', command=lambda: self.move_rule(-1)).pack(side='left', padx=2)
        ttk.Button(rules_btn_frame, text='아래로', command=lambda: self.move_rule(1)).pack(side='left', padx=2)
        
        # 미리보기
        preview_frame = ttk.LabelFrame(right_frame, text='미리보기', padding=10)
        preview_frame.pack(fill='both', expand=True, pady=5)
        
        self.preview_canvas = tk.Canvas(preview_frame, height=60, bg='white')
        self.preview_canvas.pack(fill='both', expand=True)
        
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
            return
        
        idx = selection[0]
        self.current_harmony_idx = idx
        harmony = self.manager.harmonies[idx]
        
        self.name_var.set(harmony.get('name', ''))
        self.rules = harmony.get('rules', []).copy()
        self.update_rules_display()
        self.update_preview()
    
    def new_harmony(self):
        """새 조합 생성"""
        self.current_harmony_idx = None
        self.name_var.set('새 조합')
        self.rules = [{'type': 'base'}]
        self.update_rules_display()
        self.update_preview()
    
    def delete_harmony(self):
        """조합 삭제"""
        selection = self.harmony_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if messagebox.askyesno('확인', '정말 삭제하시겠습니까?'):
            self.manager.delete_harmony(idx)
            self.load_harmony_list()
            self.new_harmony()
    
    def add_rule(self):
        """규칙 추가 다이얼로그"""
        self._open_rule_dialog()
    
    def edit_rule(self):
        """규칙 수정 다이얼로그"""
        selection = self.rules_listbox.curselection()
        if not selection:
            messagebox.showwarning('선택 필요', '수정할 규칙을 선택하세요.')
            return
        
        idx = selection[0]
        self._open_rule_dialog(edit_index=idx, existing_rule=self.rules[idx])
    
    def _open_rule_dialog(self, edit_index=None, existing_rule=None):
        """규칙 추가/수정 다이얼로그"""
        is_edit = edit_index is not None
        rule_dialog = tk.Toplevel(self.dialog)
        rule_dialog.title('규칙 수정' if is_edit else '규칙 추가')
        rule_dialog.geometry('400x280')
        rule_dialog.transient(self.dialog)
        rule_dialog.grab_set()
        
        ttk.Label(rule_dialog, text='규칙 유형:').pack(pady=5)
        rule_type_var = tk.StringVar()
        rule_combo = ttk.Combobox(rule_dialog, textvariable=rule_type_var, 
                                  values=[name for name, _ in self.RULE_TYPES], state='readonly')
        rule_combo.pack(pady=5)
        
        # 기존 규칙이 있으면 값 설정
        if existing_rule:
            rule_type = existing_rule.get('type', 'base')
            for i, (name, rtype) in enumerate(self.RULE_TYPES):
                if rtype == rule_type:
                    rule_combo.current(i)
                    break
        else:
            rule_combo.current(0)
        
        # 값 입력 프레임
        value_frame = ttk.Frame(rule_dialog)
        value_frame.pack(pady=10)
        
        ttk.Label(value_frame, text='값:').pack(side='left')
        
        # 기존 값 설정
        default_value = '0'
        if existing_rule:
            if 'value' in existing_rule:
                default_value = str(existing_rule['value'])
            elif 'angle' in existing_rule:
                default_value = str(existing_rule['angle'])
        
        value_var = tk.StringVar(value=default_value)
        value_spinbox = ttk.Spinbox(value_frame, textvariable=value_var, from_=-360, to=360, 
                                    increment=1, width=15)
        value_spinbox.pack(side='left', padx=5)
        
        # 범위 레이블
        range_label_var = tk.StringVar(value='(-360 ~ 360)')
        range_label = ttk.Label(value_frame, textvariable=range_label_var, font=('Arial', 8))
        range_label.pack(side='left', padx=5)
        
        # 고정 색상용
        default_color = existing_rule.get('color', '#FFFFFF') if existing_rule else '#FFFFFF'
        color_var = tk.StringVar(value=default_color)
        color_frame = ttk.Frame(rule_dialog)
        
        ttk.Label(color_frame, text='색상 (HEX):').pack(side='left')
        color_entry = ttk.Entry(color_frame, textvariable=color_var, width=15)
        color_entry.pack(side='left', padx=5)
        
        def on_rule_type_change(event):
            rule_type = [t for n, t in self.RULE_TYPES if n == rule_type_var.get()][0]
            if rule_type == 'fixed':
                value_frame.pack_forget()
                color_frame.pack(pady=10)
            else:
                color_frame.pack_forget()
                value_frame.pack(pady=10)
                
                # Update range based on rule type
                if rule_type in ['saturation', 'brightness']:
                    value_spinbox.config(from_=-100, to=100)
                    range_label_var.set('(-100 ~ 100)')
                else:
                    value_spinbox.config(from_=-360, to=360)
                    range_label_var.set('(-360 ~ 360)')
        
        rule_combo.bind('<<ComboboxSelected>>', on_rule_type_change)
        
        # 초기 표시 설정
        if existing_rule and existing_rule.get('type') == 'fixed':
            value_frame.pack_forget()
            color_frame.pack(pady=10)
        
        def validate_hex_color(hex_str):
            """HEX 색상 코드 유효성 검사"""
            if not hex_str.startswith('#'):
                return False
            if len(hex_str) != 7:
                return False
            try:
                int(hex_str[1:], 16)
                return True
            except ValueError:
                return False
        
        def confirm_rule():
            try:
                rule_type = [t for n, t in self.RULE_TYPES if n == rule_type_var.get()][0]
                
                if rule_type == 'base':
                    rule = {'type': 'base'}
                elif rule_type == 'fixed':
                    color = color_var.get().strip()
                    if not validate_hex_color(color):
                        messagebox.showerror('입력 오류', '올바른 HEX 색상 코드를 입력하세요.\n예: #FF0000')
                        return
                    rule = {'type': 'fixed', 'color': color}
                elif rule_type == 'hue_offset':
                    try:
                        value = float(value_var.get())
                        if not -360 <= value <= 360:
                            raise ValueError()
                    except ValueError:
                        messagebox.showerror('입력 오류', '색조 오프셋은 -360 ~ 360 사이의 숫자여야 합니다.')
                        return
                    rule = {'type': 'hue_offset', 'value': value}
                elif rule_type == 'complementary':
                    try:
                        value = float(value_var.get())
                        if not -360 <= value <= 360:
                            raise ValueError()
                    except ValueError:
                        messagebox.showerror('입력 오류', '각도는 -360 ~ 360 사이의 숫자여야 합니다.')
                        return
                    rule = {'type': 'complementary', 'angle': value}
                elif rule_type == 'saturation':
                    try:
                        value = float(value_var.get())
                        if not -100 <= value <= 100:
                            raise ValueError()
                    except ValueError:
                        messagebox.showerror('입력 오류', '채도 조정값은 -100 ~ 100 사이의 숫자여야 합니다.')
                        return
                    rule = {'type': 'saturation', 'value': value}
                elif rule_type == 'brightness':
                    try:
                        value = float(value_var.get())
                        if not -100 <= value <= 100:
                            raise ValueError()
                    except ValueError:
                        messagebox.showerror('입력 오류', '명도 조정값은 -100 ~ 100 사이의 숫자여야 합니다.')
                        return
                    rule = {'type': 'brightness', 'value': value}
                else:
                    rule = {'type': 'base'}
                
                if is_edit:
                    self.rules[edit_index] = rule
                else:
                    self.rules.append(rule)
                    
                self.update_rules_display()
                self.update_preview()
                rule_dialog.destroy()
            except Exception as e:
                messagebox.showerror('오류', f'규칙 처리 중 오류 발생: {str(e)}')
        
        button_frame = ttk.Frame(rule_dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text='확인', command=confirm_rule).pack(side='left', padx=5)
        ttk.Button(button_frame, text='취소', command=rule_dialog.destroy).pack(side='left', padx=5)
    
    def delete_rule(self):
        """규칙 삭제"""
        selection = self.rules_listbox.curselection()
        if selection:
            idx = selection[0]
            self.rules.pop(idx)
            self.update_rules_display()
            self.update_preview()
    
    def move_rule(self, direction):
        """규칙 순서 변경"""
        selection = self.rules_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        new_idx = idx + direction
        
        if 0 <= new_idx < len(self.rules):
            self.rules[idx], self.rules[new_idx] = self.rules[new_idx], self.rules[idx]
            self.update_rules_display()
            self.rules_listbox.selection_clear(0, tk.END)
            self.rules_listbox.selection_set(new_idx)
            self.update_preview()
    
    def update_rules_display(self):
        """규칙 목록 표시 업데이트"""
        self.rules_listbox.delete(0, tk.END)
        for rule in self.rules:
            rule_type = rule.get('type')
            type_name = [n for n, t in self.RULE_TYPES if t == rule_type][0]
            
            if rule_type == 'base':
                text = type_name
            elif rule_type == 'fixed':
                text = f"{type_name}: {rule.get('color', '#FFF')}"
            elif rule_type == 'hue_offset':
                text = f"{type_name}: {rule.get('value', 0)}°"
            elif rule_type == 'complementary':
                text = f"{type_name}: {rule.get('angle', 180)}°"
            elif rule_type in ['saturation', 'brightness']:
                text = f"{type_name}: {rule.get('value', 0):+}%"
            else:
                text = type_name
            
            self.rules_listbox.insert(tk.END, text)
    
    def update_preview(self):
        """미리보기 업데이트"""
        self.preview_canvas.delete('all')
        
        # 임시 매니저로 미리보기 색상 생성
        temp_harmony = {'name': 'Preview', 'rules': self.rules}
        temp_manager = CustomHarmonyManager()
        temp_manager.harmonies = [temp_harmony]
        
        try:
            colors = temp_manager.apply_harmony(self.base_color, 0)
            
            if colors:
                # Update canvas to get actual width
                self.preview_canvas.update_idletasks()
                canvas_width = self.preview_canvas.winfo_width()
                if canvas_width <= 1:  # Canvas not yet rendered
                    canvas_width = 500
                
                box_width = canvas_width / len(colors)
                for i, color in enumerate(colors):
                    x1 = i * box_width
                    x2 = (i + 1) * box_width
                    self.preview_canvas.create_rectangle(x1, 0, x2, 60, fill=color, outline='')
        except Exception:
            pass
    
    def save_current_harmony(self):
        """현재 조합 저장"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning('경고', '조합 이름을 입력하세요.')
            return
        
        harmony_data = {
            'name': name,
            'rules': self.rules.copy()
        }
        
        if self.current_harmony_idx is not None:
            # 업데이트
            self.manager.update_harmony(self.current_harmony_idx, harmony_data)
        else:
            # 새로 추가
            self.manager.add_harmony(harmony_data)
        
        self.load_harmony_list()
        messagebox.showinfo('완료', '조합이 저장되었습니다.')
