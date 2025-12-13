"""
File Handler Module
PGF 파일 저장/로드, 암호화, 최근 파일 관리를 담당하는 모듈
"""

import os
import json
import base64
import logging
from cryptography.fernet import Fernet
import hashlib
from tkinter import messagebox


class FileHandler:
    """파일 저장/로드 관리 클래스"""
    
    def __init__(self, saves_root='./saves'):
        self.saves_root = saves_root
        self._fernet_key = self._get_or_create_key()
        
    def _get_or_create_key(self):
        """AES 암호화 키 생성 또는 로드"""
        key_file = os.path.join(self.saves_root, '.key')
        try:
            os.makedirs(self.saves_root, exist_ok=True)
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    return f.read()
            else:
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                return key
        except Exception as e:
            logging.error(f"Key generation failed: {e}")
            # Generate ephemeral key
            return Fernet.generate_key()
    
    def _encrypt_aes(self, data_string):
        """AES 암호화"""
        try:
            fernet = Fernet(self._fernet_key)
            return fernet.encrypt(data_string.encode('utf-8'))
        except Exception as e:
            logging.error(f"Encryption error: {e}")
            raise
    
    def _decrypt_aes(self, encrypted_data):
        """AES 복호화"""
        try:
            fernet = Fernet(self._fernet_key)
            return fernet.decrypt(encrypted_data).decode('utf-8')
        except Exception as e:
            logging.error(f"Decryption error: {e}")
            raise
    
    def save_to_file(self, path, workspace_data):
        """워크스페이스를 파일에 저장"""
        try:
            # Validate path
            if not path:
                raise ValueError("저장 경로가 지정되지 않았습니다.")
            
            # Ensure directory exists
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
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
            
            logging.info(f"Saved workspace: {path}")
            return True
            
        except PermissionError:
            messagebox.showerror('Save Error', '파일에 쓰기 권한이 없습니다.')
            logging.error(f"Save failed: Permission denied for {path}")
            return False
        except OSError as e:
            messagebox.showerror('Save Error', f'디스크 오류: {str(e)}')
            logging.error(f"Save failed: OS error - {str(e)}")
            return False
        except Exception as e:
            messagebox.showerror('Save Error', f'저장 실패: {str(e)}')
            logging.error(f"Save failed: {str(e)}")
            return False
    
    def load_from_file(self, path):
        """파일에서 워크스페이스 로드"""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")
            
            with open(path, 'rb') as f:
                file_data = f.read()
            
            # Try AES decryption first, fallback to base64 for old files
            try:
                data_json = self._decrypt_aes(file_data)
            except Exception:
                # Try base64 decoding for backward compatibility
                try:
                    data_json = base64.b64decode(file_data).decode('utf-8')
                    logging.info("Loaded old format file (base64)")
                except Exception:
                    raise ValueError("파일 형식을 인식할 수 없습니다.")
            
            workspace_data = json.loads(data_json)
            logging.info(f"Loaded workspace: {path}")
            return workspace_data
            
        except FileNotFoundError as e:
            messagebox.showerror('Load Error', str(e))
            logging.error(str(e))
            return None
        except json.JSONDecodeError:
            messagebox.showerror('Load Error', 'JSON 파싱 실패. 파일이 손상되었습니다.')
            logging.error(f"JSON decode error for {path}")
            return None
        except Exception as e:
            messagebox.showerror('Load Error', f'로드 실패: {str(e)}')
            logging.error(f"Load failed: {str(e)}")
            return None
    
    def get_recent_files_path(self):
        """최근 파일 목록 경로"""
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Temp')
        os.makedirs(temp_dir, exist_ok=True)
        return os.path.join(temp_dir, 'recent_files.json')
    
    def load_recent_files(self):
        """최근 파일 목록 로드"""
        try:
            recent_path = self.get_recent_files_path()
            if os.path.exists(recent_path):
                with open(recent_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Load recent files error: {e}")
        return []
    
    def save_recent_files(self, recent_files):
        """최근 파일 목록 저장"""
        try:
            recent_path = self.get_recent_files_path()
            with open(recent_path, 'w', encoding='utf-8') as f:
                json.dump(recent_files, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Save recent files error: {e}")
    
    def add_recent_file(self, file_path, recent_files, max_recent=10):
        """최근 파일 목록에 추가"""
        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        if len(recent_files) > max_recent:
            recent_files = recent_files[:max_recent]
        return recent_files
