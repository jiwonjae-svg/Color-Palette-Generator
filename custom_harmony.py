"""
커스텀 색상 조합 관리 모듈 (리메이크)
HSV 슬라이더와 고정 색상만 사용하는 간단한 시스템
"""

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



