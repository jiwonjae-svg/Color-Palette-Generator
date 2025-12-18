"""
AI 색상 추천 모듈
Google Gemini API를 사용하여 색상 팔레트 생성
"""

import os
import json
import re
from typing import List, Tuple, Optional

from language_manager import LanguageManager


class AIColorRecommender:
    """AI 기반 색상 추천 클래스"""
    
    def __init__(self, api_key: Optional[str] = None, lang: Optional[LanguageManager] = None):
        self.api_key = api_key
        self.model = None
        self.lang = lang or LanguageManager('en')
        
        if api_key:
            self.initialize_model()

    def _t(self, key: str, **kwargs) -> str:
        text = self.lang.get(key)
        return text.format(**kwargs) if kwargs else text
    
    def initialize_model(self):
        """Gemini 모델 초기화"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
            return True
        except ImportError:
            raise ImportError(self._t('ai_recommender_missing_library', install_cmd='pip install google-generativeai'))
        except Exception as e:
            raise Exception(self._t('ai_recommender_init_failed', error=str(e)))
    
    def set_api_key(self, api_key: str) -> bool:
        """API 키 설정"""
        self.api_key = api_key
        try:
            self.initialize_model()
            return True
        except Exception:
            return False
    
    def generate_palettes(self, num_palettes: int = 5, keywords: str = "", num_colors: int = 5) -> List[dict]:
        """
        AI로 색상 팔레트 생성
        
        Args:
            num_palettes: 생성할 팔레트 개수
            keywords: 키워드 (예: "ocean, calm, blue")
            num_colors: 팔레트당 색상 개수
        
        Returns:
            팔레트 리스트 (각 팔레트는 {'name': str, 'colors': List[str]} 딕셔너리)
        """
        if not self.model:
            raise Exception(self._t('ai_recommender_api_key_not_set'))
        
        # 프롬프트 생성 (이름 포함)
        if keywords.strip():
            prompt = self._t(
                'ai_recommender_prompt_with_keywords',
                num_palettes=num_palettes,
                num_colors=num_colors,
                keywords=keywords,
            )
        else:
            prompt = self._t(
                'ai_recommender_prompt_without_keywords',
                num_palettes=num_palettes,
                num_colors=num_colors,
            )
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # 응답 파싱
            palettes = self._parse_response(text, num_colors)
            return palettes[:num_palettes]  # 요청한 개수만큼 반환
            
        except Exception as e:
            raise Exception(self._t('ai_recommender_generation_failed', error=str(e)))
    
    def _parse_response(self, text: str, expected_colors: int) -> List[dict]:
        """AI 응답 파싱 - 팔레트 이름과 색상 추출"""
        palettes = []
        
        # HEX 색상 코드 패턴
        hex_pattern = r'#[0-9A-Fa-f]{6}'
        
        # 줄 단위로 처리
        lines = text.split('\n')
        for line in lines:
            # "PaletteName: #HEX,#HEX,..." 형식 파싱
            if ':' in line:
                parts = line.split(':', 1)
                name = parts[0].strip()
                colors = re.findall(hex_pattern, parts[1])
                
                if colors and len(colors) >= expected_colors and name:
                    # 대문자로 통일
                    colors = [c.upper() for c in colors[:expected_colors]]
                    palettes.append({
                        'name': name,
                        'colors': colors
                    })
            else:
                # 이름 없이 색상만 있는 경우 (하위 호환성)
                colors = re.findall(hex_pattern, line)
                if colors and len(colors) >= expected_colors:
                    # 대문자로 통일
                    colors = [c.upper() for c in colors[:expected_colors]]
                    palettes.append({
                        'name': self.lang.get('palette_numbered').format(i=len(palettes) + 1),
                        'colors': colors
                    })
        
        return palettes
    
    def test_api_key(self) -> Tuple[bool, str]:
        """API 키 테스트"""
        if not self.api_key:
            return False, self._t('ai_recommender_api_key_not_set')
        
        try:
            self.initialize_model()
            # 간단한 테스트 요청
            response = self.model.generate_content(self._t('ai_recommender_test_prompt'))
            if response and response.text:
                return True, self._t('ai_recommender_test_success')
            else:
                return False, self._t('ai_recommender_test_no_response')
        except Exception as e:
            return False, self._t('ai_recommender_test_failed', error=str(e))


class AISettings:
    """AI 설정 관리"""
    
    @classmethod
    def save_settings(cls, file_handler, api_key: str, num_colors: int = 5, keywords: str = "") -> bool:
        """설정 저장 (FileHandler 사용)"""
        try:
            data = {
                'api_key': api_key,
                'num_colors': num_colors,
                'keywords': keywords
            }
            return file_handler.save_data_file('ai_config.dat', data)
        except Exception:
            return False
    
    @classmethod
    def load_settings(cls, file_handler) -> dict:
        """설정 불러오기 (FileHandler 사용)"""
        return file_handler.load_data_file('ai_config.dat', default={
            'api_key': '',
            'num_colors': 5,
            'keywords': ''
        })

