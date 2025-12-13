"""
Configuration Manager Module
앱 설정을 JSON 파일로 저장/로드하는 모듈
"""

import os
import json
import logging


class ConfigManager:
    """설정 관리 클래스"""
    
    DEFAULT_CONFIG = {
        # Auto-save settings
        'auto_save_enabled': True,
        'auto_save_interval': 300,  # seconds
        
        # K-means settings
        'kmeans_max_colors': 5,
        'kmeans_filter_background': True,
        'kmeans_max_iterations': 12,
        
        # UI settings
        'window_width': 700,
        'window_height': 520,
        'theme': 'default',
        
        # Color extraction settings
        'background_luminance_high': 240,
        'background_luminance_low': 15,
        'saturation_threshold': 0.15,
        
        # File settings
        'max_recent_files': 10,
        
        # Export settings
        'default_export_format': 'png',
        
        # Screen picker settings
        'screen_picker_size': 100
    }
    
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self):
        """설정 파일 로드 (없으면 기본 설정 사용)"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # Merge with defaults (in case new options were added)
                config = self.DEFAULT_CONFIG.copy()
                config.update(loaded_config)
                logging.info("Config loaded successfully")
                return config
            except Exception as e:
                logging.error(f"Config load error: {e}. Using defaults.")
                return self.DEFAULT_CONFIG.copy()
        else:
            logging.info("Config file not found. Using defaults.")
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """현재 설정을 파일에 저장"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logging.info("Config saved successfully")
            return True
        except Exception as e:
            logging.error(f"Config save error: {e}")
            return False
    
    def get(self, key, default=None):
        """설정 값 가져오기"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """설정 값 변경"""
        self.config[key] = value
    
    def reset_to_defaults(self):
        """기본 설정으로 재설정"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()
        logging.info("Config reset to defaults")
