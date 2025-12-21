"""
File Handler Module
Handles PGF file save/load, encryption, and recent files management
"""

import os
import json
import base64
import logging
import datetime
from cryptography.fernet import Fernet

EMBEDDED_KEY = b'VkZURWYzbUtiSFJ0Z2oyWHFwQjRwbjlSVldyakFrOWJPTUhjbGlDZmJZdz0='


class FileHandler:
    """File operations with encryption"""
    
    def __init__(self):
        self._fernet_key = base64.b64decode(EMBEDDED_KEY)
        os.makedirs('data', exist_ok=True)
    
    def _encrypt_aes(self, data_string):
        """AES encryption"""
        try:
            fernet = Fernet(self._fernet_key)
            return fernet.encrypt(data_string.encode('utf-8'))
        except Exception as e:
            logging.error(f"Encryption error: {e}")
            raise
    
    def _decrypt_aes(self, encrypted_data):
        """AES decryption"""
        try:
            fernet = Fernet(self._fernet_key)
            return fernet.decrypt(encrypted_data).decode('utf-8')
        except Exception as e:
            logging.error(f"Decryption error: {e}")
            raise
    
    def save_to_file(self, path, workspace_data):
        """Save workspace to encrypted file"""
        try:
            if not path:
                raise ValueError("No save path specified")
            
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            data_json = json.dumps(workspace_data, ensure_ascii=False)
            encrypted = self._encrypt_aes(data_json)
            
            temp_path = path + '.tmp'
            try:
                with open(temp_path, 'wb') as f:
                    f.write(encrypted)
                
                if os.path.exists(path):
                    backup_path = path + '.bak'
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(path, backup_path)
                
                os.rename(temp_path, path)
                
                backup_path = path + '.bak'
                if os.path.exists(backup_path):
                    try:
                        os.remove(backup_path)
                    except Exception:
                        pass
                        
            except Exception as write_error:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                raise write_error
            
            logging.info(f"Saved workspace: {path}")
            return True
            
        except PermissionError:
            logging.error(f"Save failed: Permission denied for {path}")
            return False
        except OSError as e:
            logging.error(f"Save failed: OS error - {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Save failed: {str(e)}")
            return False
    
    def load_from_file(self, path):
        """Load workspace from encrypted file"""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")
            
            with open(path, 'rb') as f:
                file_data = f.read()
            
            try:
                data_json = self._decrypt_aes(file_data)
            except Exception:
                try:
                    data_json = base64.b64decode(file_data).decode('utf-8')
                    logging.info("Loaded old format file (base64)")
                except Exception:
                    raise ValueError("Unrecognized file format")
            
            workspace_data = json.loads(data_json)
            logging.info(f"Loaded workspace: {path}")
            return workspace_data
            
        except FileNotFoundError as e:
            logging.error(str(e))
            return None
        except json.JSONDecodeError:
            logging.error(f"JSON decode error for {path}")
            return None
        except Exception as e:
            logging.error(f"Load failed: {str(e)}")
            return None
    
    def get_recent_files_path(self):
        """Recent files list path in data folder"""
        return os.path.join('data', 'recent_files.dat')
    
    def load_recent_files(self):
        """Load recent files list"""
        return self.load_data_file('recent_files.dat', default=[])
    
    def save_recent_files(self, recent_files):
        """Save recent files list"""
        self.save_data_file('recent_files.dat', recent_files)
    
    def add_recent_file(self, file_path, recent_files, max_recent=10):
        """Add file to recent files list"""
        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        if len(recent_files) > max_recent:
            recent_files = recent_files[:max_recent]
        return recent_files
    
    def save_data_file(self, filename, data, data_dir='data'):
        """Save data to encrypted .dat file"""
        try:
            os.makedirs(data_dir, exist_ok=True)
            
            filepath = os.path.join(data_dir, filename)
            if not filepath.endswith('.dat'):
                filepath += '.dat'
            
            data_json = json.dumps(data, ensure_ascii=False)
            encrypted = self._encrypt_aes(data_json)
            
            with open(filepath, 'wb') as f:
                f.write(encrypted)
            
            logging.info(f"Saved data file: {filepath}")
            return True
        except Exception as e:
            logging.error(f"Save data file error: {e}")
            return False
    
    def load_data_file(self, filename, data_dir='data', default=None):
        """Load data from encrypted .dat file"""
        try:
            filepath = os.path.join(data_dir, filename)
            if not filepath.endswith('.dat'):
                filepath += '.dat'
            
            if not os.path.exists(filepath):
                json_path = filepath.replace('.dat', '.json')
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.save_data_file(filename, data, data_dir)
                    logging.info(f"Migrated JSON to DAT: {json_path} -> {filepath}")
                    return data
                return default
            
            with open(filepath, 'rb') as f:
                encrypted_data = f.read()
            
            data_json = self._decrypt_aes(encrypted_data)
            data = json.loads(data_json)
            
            logging.info(f"Loaded data file: {filepath}")
            return data
        except Exception as e:
            logging.error(f"Load data file error: {e}")
            try:
                json_path = os.path.join(data_dir, filename.replace('.dat', '.json'))
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except Exception:
                pass
            return default

    def load_palette_metadata(self):
        """Load palette metadata (list of saved palettes with paths and info)"""
        return self.load_data_file('palette_metadata.dat', default=[])
    
    def save_palette_metadata(self, metadata):
        """Save palette metadata"""
        return self.save_data_file('palette_metadata.dat', metadata)
    
    def add_palette_metadata(self, name, colors, file_path):
        """Add palette metadata entry"""
        metadata = self.load_palette_metadata()
        
        # Remove existing entry with same path
        metadata = [m for m in metadata if m.get('path') != file_path]
        
        # Add new entry
        entry = {
            'name': name,
            'colors': colors,
            'path': file_path,
            'timestamp': datetime.datetime.now().isoformat()
        }
        metadata.insert(0, entry)
        
        # Limit to 100 entries
        if len(metadata) > 100:
            metadata = metadata[:100]
        
        return self.save_palette_metadata(metadata)
    
    def remove_palette_metadata(self, file_path):
        """Remove palette metadata entry by file path"""
        metadata = self.load_palette_metadata()
        metadata = [m for m in metadata if m.get('path') != file_path]
        return self.save_palette_metadata(metadata)
    
    def clean_palette_metadata(self):
        """Remove metadata entries for non-existent files"""
        metadata = self.load_palette_metadata()
        cleaned = [m for m in metadata if os.path.exists(m.get('path', ''))]
        if len(cleaned) != len(metadata):
            self.save_palette_metadata(cleaned)
        return cleaned
