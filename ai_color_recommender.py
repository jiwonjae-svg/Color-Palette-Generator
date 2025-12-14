"""
AI 색상 추천 모듈
Google Gemini API를 사용하여 색상 팔레트 생성
"""

import os
import json
import re
from typing import List, Tuple, Optional


class AIColorRecommender:
    """AI 기반 색상 추천 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model = None
        
        if api_key:
            self.initialize_model()
    
    def initialize_model(self):
        """Gemini 모델 초기화"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            return True
        except ImportError:
            raise ImportError("google-generativeai 라이브러리가 설치되지 않았습니다.\n'pip install google-generativeai'를 실행하세요.")
        except Exception as e:
            raise Exception(f"Gemini 모델 초기화 실패: {str(e)}")
    
    def set_api_key(self, api_key: str) -> bool:
        """API 키 설정"""
        self.api_key = api_key
        try:
            self.initialize_model()
            return True
        except Exception:
            return False
    
    def generate_palettes(self, num_palettes: int = 5, keywords: str = "", num_colors: int = 5) -> List[List[str]]:
        """
        AI로 색상 팔레트 생성
        
        Args:
            num_palettes: 생성할 팔레트 개수
            keywords: 키워드 (예: "ocean, calm, blue")
            num_colors: 팔레트당 색상 개수
        
        Returns:
            팔레트 리스트 (각 팔레트는 HEX 색상 코드 리스트)
        """
        if not self.model:
            raise Exception("API 키가 설정되지 않았습니다.")
        
        # 프롬프트 생성
        if keywords.strip():
            prompt = f"""Generate {num_palettes} harmonious color palettes, each with exactly {num_colors} colors.
Keywords: {keywords}

Return ONLY the hex color codes in this exact format, with no additional text or explanation:
#RRGGBB,#RRGGBB,#RRGGBB,#RRGGBB,#RRGGBB
#RRGGBB,#RRGGBB,#RRGGBB,#RRGGBB,#RRGGBB
...

Each line should be one palette. Make the palettes harmonious and suitable for the given keywords."""
        else:
            prompt = f"""Generate {num_palettes} diverse and harmonious color palettes, each with exactly {num_colors} colors.

Return ONLY the hex color codes in this exact format, with no additional text or explanation:
#RRGGBB,#RRGGBB,#RRGGBB,#RRGGBB,#RRGGBB
#RRGGBB,#RRGGBB,#RRGGBB,#RRGGBB,#RRGGBB
...

Each line should be one palette. Make the palettes diverse and harmonious."""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # 응답 파싱
            palettes = self._parse_response(text, num_colors)
            return palettes[:num_palettes]  # 요청한 개수만큼 반환
            
        except Exception as e:
            raise Exception(f"AI 팔레트 생성 실패: {str(e)}")
    
    def _parse_response(self, text: str, expected_colors: int) -> List[List[str]]:
        """AI 응답 파싱"""
        palettes = []
        
        # HEX 색상 코드 패턴
        hex_pattern = r'#[0-9A-Fa-f]{6}'
        
        # 줄 단위로 처리
        lines = text.split('\n')
        for line in lines:
            # HEX 코드 찾기
            colors = re.findall(hex_pattern, line)
            
            if colors and len(colors) >= expected_colors:
                # 대문자로 통일
                colors = [c.upper() for c in colors[:expected_colors]]
                palettes.append(colors)
        
        return palettes
    
    def test_api_key(self) -> Tuple[bool, str]:
        """API 키 테스트"""
        if not self.api_key:
            return False, "API 키가 설정되지 않았습니다."
        
        try:
            self.initialize_model()
            # 간단한 테스트 요청
            response = self.model.generate_content("Say 'OK' if you can read this.")
            if response and response.text:
                return True, "API 키가 정상적으로 작동합니다."
            else:
                return False, "응답을 받을 수 없습니다."
        except Exception as e:
            return False, f"API 키 테스트 실패: {str(e)}"


class AISettings:
    """AI 설정 관리"""
    
    CONFIG_FILE = 'ai_config.json'
    
    @classmethod
    def save_settings(cls, api_key: str, num_colors: int = 5, keywords: str = "") -> bool:
        """설정 저장"""
        try:
            data = {
                'api_key': api_key,
                'num_colors': num_colors,
                'keywords': keywords
            }
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False
    
    @classmethod
    def load_settings(cls) -> dict:
        """설정 불러오기"""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'api_key': '',
            'num_colors': 5,
            'keywords': ''
        }
