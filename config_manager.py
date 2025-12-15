"""
Configuration Manager Module
Manages application settings using encrypted DAT files in data/ folder
"""

import logging


class ConfigManager:
    """Application configuration manager using file_handler for encrypted storage"""
    
    DEFAULT_CONFIG = {
        'auto_save_enabled': True,
        'auto_save_interval': 300,
        'kmeans_max_colors': 5,
        'kmeans_filter_background': True,
        'kmeans_max_iterations': 12,
        'window_width': 700,
        'window_height': 520,
        'theme': 'default',
        'background_luminance_high': 240,
        'background_luminance_low': 15,
        'saturation_threshold': 0.15,
        'max_recent_files': 10,
        'default_export_format': 'png',
        'screen_picker_size': 100
    }
    
    def __init__(self, file_handler):
        """Initialize with file_handler for encryption"""
        self.file_handler = file_handler
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from data/config.dat"""
        self.config = self.file_handler.load_data_file('config.dat', default=self.DEFAULT_CONFIG.copy())
        return self.config

    def save_config(self):
        """Save configuration to data/config.dat"""
        try:
            self.file_handler.save_data_file('config.dat', self.config)
            logging.info("Config saved successfully")
            return True
        except Exception as e:
            logging.error(f"Config save error: {e}")
            return False
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
    
    def reset_to_defaults(self):
        """Reset to default configuration"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()
        logging.info("Config reset to defaults")
