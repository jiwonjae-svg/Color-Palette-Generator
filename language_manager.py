"""
다국어 지원 모듈
한국어/영어 UI 텍스트 관리
"""

class LanguageManager:
    """언어 관리 클래스"""
    
    # 한국어 텍스트
    KOREAN = {
        # 메뉴
        'menu_file': '파일',
        'menu_edit': '편집',
        'menu_view': '보기',
        'menu_settings': '설정',
        'menu_help': '도움말',
        
        # 파일 메뉴
        'file_new': '새로 만들기...',
        'file_open': '열기...',
        'file_save': '저장...',
        'file_save_as': '다른 이름으로 저장...',
        'file_import': '가져오기',
        'file_export': '내보내기',
        'file_exit': '종료',
        
        # 편집 메뉴
        'edit_copy': '복사',
        'edit_paste': '붙여넣기',
        'edit_clear': '지우기',
        
        # 설정 메뉴
        'settings_title': '설정...',
        'settings_language': '언어',
        'settings_theme': '테마',
        'settings_api': 'AI 설정...',
        
        # 테마
        'theme_light': '라이트 테마',
        'theme_dark': '다크 테마',
        
        # 메인 UI
        'title': '색상 팔레트 생성기',
        'color_input': '색상 입력',
        'pick_color': '색상 선택',
        'from_screen': '화면에서 추출',
        'from_image': '이미지에서',
        'upload_image': '이미지 업로드',
        'generate_palette': '팔레트 생성',
        'clear_all': '모두 지우기',
        'select_image': '이미지 선택...',
        'no_file_selected': '선택된 파일 없음',
        'extract_from_screen': '화면에서 추출',
        'generate': '생성',
        'random_color': '랜덤 색상',
        'harmony_options': '조화 옵션',
        'untitled': '제목없음',
        'open_recent': '최근 파일 열기',
        'reset_to_defaults': '기본값으로 초기화',
        'tools': '도구',
        'apply_palette_to_image': '이미지에 팔레트 적용...',
        'custom_color_harmonies': '커스텀 색상 조화...',
        'preset_palettes': '프리셋 팔레트...',
        
        # 색상 조합
        'complementary': '보색',
        'analogous': '유사색',
        'triadic': '삼각 조화색',
        'monochromatic': '단색 조화',
        'split_complementary': '스플릿 보색',
        'square': '스퀘어',
        'tetradic': '테트라딕',
        'double_complementary': '더블 보색',
        
        # AI 팔레트
        'ai_palette': 'AI 팔레트',
        'ai_generate': '생성',
        'ai_clear': '지우기',
        'ai_keywords': '키워드 (선택사항)',
        'ai_num_palettes': '팔레트 개수',
        'ai_num_colors': '색상 개수',
        'ai_generating': 'AI 팔레트 생성 중...',
        'ai_no_palettes': 'AI 팔레트가 없습니다. 생성 버튼을 눌러 생성하세요.',
        
        # 저장된 팔레트
        'saved_palettes': '저장된 팔레트',
        'save_current': '현재 팔레트 저장',
        'rename': '이름 바꾸기',
        'edit_palette': '팔레트 편집',
        'save_palette': '팔레트 저장',
        'delete_palette': '팔레트 삭제',
        'export_txt': 'TXT로 내보내기',
        'export_png': 'PNG로 내보내기',
        'view_rgb': 'RGB로 보기',
        'view_value': '밸류로 보기',
        
        # 팔레트 편집기
        'palette_editor': '팔레트 편집',
        'add_color': '색상 추가',
        'edit_color': '색상 수정',
        'delete_color': '색상 삭제',
        'hsv_adjust': 'HSV 조정',
        'confirm': '확인',
        'cancel': '취소',
        'reset': '초기화',
        'apply': '적용',
        
        # HSV 조정
        'hsv_dialog_title': '색상 조정 (HSV)',
        'hue': '색조 (Hue)',
        'saturation': '채도 (Saturation)',
        'value': '명도 (Value)',
        'brightness': '밝기',
        'contrast': '대비',
        'warmth': '색온도',
        'preview': '미리보기',
        
        # 메시지
        'error': '오류',
        'warning': '경고',
        'info': '정보',
        'success': '성공',
        'confirm_delete': '정말 삭제하시겠습니까?',
        'save_success': '저장되었습니다.',
        'load_success': '불러왔습니다.',
        'invalid_color': '잘못된 색상 코드입니다.',
        'api_error': 'API 오류가 발생했습니다.',
        'no_color': '색상이 없습니다.',

        # main.py 공통 메시지 (이미지/저장/불러오기)
        'save_error_title': '저장 오류',
        'load_error_title': '불러오기 오류',
        'saved_title': '저장 완료',
        'loaded_title': '불러오기 완료',
        'msg_file_not_found': '파일을 찾을 수 없습니다.',
        'msg_large_file_title': '큰 파일',
        'msg_large_file_prompt': '파일 크기가 {size_mb}MB입니다. 계속하시겠습니까?',
        'msg_thumbnail_failed': '이미지 미리보기를 생성할 수 없습니다.',
        'msg_image_load_failed': '이미지 로드 실패: {error}',
        'msg_no_save_path': '저장 경로가 지정되지 않았습니다.',
        'msg_workspace_saved': '워크스페이스를 저장했습니다: {path}',
        'msg_workspace_loaded': '워크스페이스를 불러왔습니다: {path}',
        'msg_permission_denied_write': '파일에 쓰기 권한이 없습니다.',
        'msg_disk_error': '디스크 오류: {error}',
        'msg_save_failed': '저장 실패: {error}',
        'msg_load_failed': '불러오기 실패: {error}',

        'msg_color_picker_failed': '색상 선택기 오류: {error}',
        'msg_screen_picker_failed': '화면 추출 오류: {error}',
        'msg_capture_failed': '화면 캡처 실패: {error}',
        'msg_save_screenshot_failed': '스크린샷 영역 저장 실패: {error}',

        'save_prompt_title': '저장',
        'msg_save_changes_prompt': '현재 작업을 저장하시겠습니까?',
        'msg_generate_palette_first': '저장하기 전에 먼저 팔레트를 생성하세요.',
        'msg_save_txt_failed': 'TXT 저장 실패: {error}',
        'msg_save_png_failed': 'PNG 저장 실패: {error}',
        'msg_saved_txt_summary': '{count}개의 TXT 파일을 저장했습니다: {dest_dir}',
        'msg_saved_png_summary': '{count}개의 PNG 파일을 저장했습니다: {dest_dir}',
        'msg_select_harmony_required': '최소 하나의 색상 조화를 선택하세요.',
        'no_recent_files': '(최근 파일 없음)',
        'msg_file_not_found_path': '파일을 찾을 수 없습니다: {path}',

        'input_error_title': '입력 오류',
        'ai_error_title': 'AI 오류',
        'ai_generating_title': 'AI 팔레트 생성 중...',
        'ai_palette_name': 'AI 팔레트 {i}',

        'msg_ai_api_key_required': 'AI 설정에서 API 키를 입력하세요.',
        'msg_ai_init_failed': 'AI 초기화 실패: {error}',
        'msg_palette_generation_failed': '팔레트 생성 실패: {error}',
        'msg_display_palettes_failed': '팔레트 표시 실패: {error}',

        'msg_invalid_hex_prompt': '올바른 HEX 코드를 입력하세요 (예: #3498db).',
        'msg_select_image_first': '이미지 파일을 선택하세요.',
        'msg_image_file_not_found': '이미지 파일을 찾을 수 없습니다.',
        'msg_extract_colors_failed': '이미지에서 색상을 추출할 수 없습니다.',

        'msg_export_png_failed': 'PNG 내보내기 실패: {error}',

        'export_title': '내보내기',
        'my_palette_file': '내 팔레트',
        'text_file': '텍스트 파일',
        'export_txt_palette_label': '팔레트: {name}',
        'export_txt_color_count_label': '색상 개수: {count}',
        'msg_export_txt_failed': 'TXT 내보내기 실패: {error}',

        'custom_harmony_default_name': '커스텀 조합',

        'reset_settings_title': '설정 초기화',
        'reset_done_title': '초기화 완료',
        'msg_reset_settings_confirm': '모든 설정을 기본값으로 복원하시겠습니까?',
        'msg_settings_reset_done': '설정이 기본값으로 복원되었습니다.\n재시작하여 변경사항을 적용하세요.',
        'msg_no_saved_palettes': '저장된 팔레트가 없습니다.\n먼저 팔레트를 생성하고 저장하세요.',

        'png_image': 'PNG 이미지',
        'jpeg_image': 'JPEG 이미지',
        'msg_load_image_first': '먼저 이미지를 불러오세요.',
        'msg_empty_palette_cannot_apply': '빈 팔레트는 적용할 수 없습니다.',
        'msg_recolor_load_image_failed': '이미지 불러오기 실패: {error}',
        'msg_recolor_display_failed': '이미지 표시 실패: {error}',
        'msg_recolor_save_success': '팔레트가 적용된 이미지를 저장했습니다:\n{path}',
        'msg_recolor_save_failed': '저장 실패: {error}',
        'msg_recolor_preview_failed': '미리보기 생성 실패: {error}',
        'msg_image_loaded': '이미지가 로드되었습니다: {filename}',

        'msg_palette_has_no_colors': '팔레트에 색상이 없습니다.',
        'msg_no_valid_colors': '유효한 색상이 없습니다.',
        'msg_color_adjust_unavailable': '색상 조정 기능을 사용할 수 없습니다.',
        'msg_color_adjust_failed': '색상 조정 실패: {error}',

        # 공통 표시/포맷
        'ellipsis': '...',
        'rgb_unknown': '(?, ?, ?)',
        'label_numbered_rgb': '{i}. RGB: {value}',
        'tooltip_recent_color_info': 'RGB: {rgb}\nHEX: {hex}\n흑백값: {lum}',
        'custom_harmony_numbered': '커스텀 {i}',

        # 설정 UI
        'settings_window_size_separator': 'x',

        # 프리셋 팔레트
        'preset_tags_format': '({tags})',

        # 내보내기(TXT/PNG) 파일 내용
        'export_txt_file_header': '팔레트 내보내기: {timestamp}',
        'export_txt_palette_title': '팔레트 {i}',
        'export_txt_line_base': '기본: {hex} | RGB: {rgb}',
        'export_txt_line_complementary': '보색: {hex} | RGB: {rgb}',
        'export_txt_section_analogous': '유사색:',
        'export_txt_section_triadic': '삼각 조화색:',
        'export_txt_section_monochromatic': '단색 조화:',
        'export_txt_color_line': '{hex} | RGB: {rgb}',
        'export_txt_indexed_color_line': '{i}. {hex} | RGB: {rgb}',

        'export_png_palette_title': '팔레트 {i}',
        'export_png_label_base': '기본',
        'export_png_label_complementary': '보색',
        'export_png_label_analogous': '유사색',
        'export_png_label_triadic': '삼각',
        'export_png_label_monochromatic': '단색',
        'export_png_label_numbered': '{label} {i}',
        
        # 버튼
        'ok': '확인',
        'yes': '예',
        'no': '아니오',
        
        # 기타
        'base_color': '기본 색상',
        'representative_color': '대표 색상',
        'palette_name': '팔레트 이름',
        'new_name': '새 이름',
        'enter_name': '이름을 입력하세요',
        
        # 팔레트 목록 버튼 툴팁
        'tooltip_add_palette': '팔레트 추가',
        'tooltip_delete_palette': '팔레트 제거',
        'tooltip_copy_palette': '팔레트 복사',
        'tooltip_load_palette': '팔레트 불러오기',
        'tooltip_adjust_color': '색상 조정',
        
        # 파일 다이얼로그
        'dialog_select_image': '이미지 선택',
        'dialog_save_pgf': 'PGF로 저장...',
        'dialog_save_as': '다른 이름으로 저장...',
        'dialog_open_pgf': 'PGF 열기...',
        'dialog_select_image_recolor': '이미지 선택',
        'dialog_save_recolored': '팔레트 적용 이미지 저장',
        
        # 색상 선택 다이얼로그
        'harmonies_title': '색상 조화 선택',
        'select_harmonies': '표시할 색상 조화를 선택하세요:',
        'custom_harmonies': '커스텀 색상 조화:',
        'pick_color_title': '색상 선택',
        'add_color_title': '색상 추가',
        'edit_color_title': '색상 수정',
        
        # 색상 박스 툴팁
        'tooltip_color_box': '왼쪽 클릭: 팔레트에 추가\n오른쪽 클릭: 기본 색상으로 설정',
        
        # 팔레트 편집 버튼
        'sort_by_hue': '색조 정렬',
        'sort_by_saturation': '채도 정렬',
        'sort_by_luminance': '밸류 정렬',
        'sort_reverse': '역순 정렬',
        'show_values': '값 보기',
        
        # 로딩/상태 메시지
        'screenshot_label': '**스크린샷**',
        'no_image_label': '이미지가 없습니다.',
        'empty_palette': '빈 팔레트입니다',
        'generating_ai': 'AI 팔레트 생성 중...',
        
        # 설정 다이얼로그 섹션
        'settings_language_section': '언어 설정',
        'settings_theme_section': '테마 설정',
        'settings_autosave_section': '자동 저장 설정',
        'settings_extraction_section': '색상 추출 설정',
        'settings_ui_section': 'UI 설정',
        
        # 설정 옵션
        'language_label': '언어:',
        'theme_label': '테마:',
        'autosave_enable': '자동 저장 사용',
        'autosave_interval': '자동 저장 간격 (초):',
        'max_colors': '최대 색상 수:',
        'filter_background': '배경색 필터링 (흰색/검은색 제외)',
        'window_size': '창 크기:',
        'recent_files_count': '최근 파일 수:',
        
        # 이미지 재색상 다이얼로그
        'select_palette_label': '팔레트 선택:',
        'load_image_btn': '이미지 불러오기',
        'view_original_btn': '원본 크기로 보기',
        'save_btn': '저장',
        'close_btn': '닫기',
        'preview_label': '미리보기',
        
        # AI 설정 다이얼로그
        'ai_api_key_label': 'Gemini API 키:',
        'ai_api_help': 'API 키는 https://aistudio.google.com/app/apikey 에서 발급받을 수 있습니다.',
        'ai_colors_per_palette': '팔레트당 색상 개수:',
        'ai_keywords_label': '키워드 (쉼표로 구분):',
        'ai_keywords_example': '예: ocean, calm, blue',
        'ai_test_api': 'API 키 테스트',
        
        # 일반
        'image_files': '이미지 파일',
        'all_files': '모든 파일',
        
        # 다이얼로그 제목
        'dialog_settings': '설정',
        'dialog_palette_editor': '팔레트 편집',
        'dialog_ai_settings': 'AI 설정',
        'dialog_select_harmonies': '색상 조화 선택',
        'dialog_apply_palette': '팔레트 적용',
        'dialog_custom_harmony': '커스텀 색상 조화',
        'dialog_preset_palettes': '프리셋 팔레트',
        'dialog_rename_palette': '팔레트 이름 변경',

        # 공통
        'unnamed': '이름없음',
        'done': '완료',

        # 모듈/다이얼로그 오류
        'custom_harmony_module_missing': '커스텀 조합 모듈을 찾을 수 없습니다.',
        'custom_harmony_open_failed': '커스텀 조합 열기 실패: {error}',
        'preset_module_missing': '프리셋 팔레트 모듈을 찾을 수 없습니다.',
        'preset_open_failed': '프리셋 팔레트 열기 실패: {error}',

        # 프리셋 팔레트
        'preset_added_title': '팔레트 추가됨',
        'preset_added_msg': '"{name}" 팔레트를 저장된 팔레트에 추가했습니다.',
        'preset_pick_search_color': '검색할 색상 선택',

        # 커스텀 조합
        'custom_harmony_select_delete': '삭제할 조합을 선택하세요.',
        'custom_harmony_confirm_delete': '정말 삭제하시겠습니까?',
        'custom_harmony_name_required': '조합 이름을 입력하세요.',
        'custom_harmony_color_required': '최소 하나의 색상을 추가하세요.',
        'custom_harmony_saved': '조합이 저장되었습니다.',
        'custom_harmony_hsv_item': '{i}. HSV (H:{h:+.0f}°, S:{s:+.0f}%, V:{v:+.0f}%)',
        'custom_harmony_fixed_item': '{i}. 고정 색상: {hex}',
        
        # 설정 창 메시지
        'settings_saved': '설정이 저장되었습니다.\n언어 변경은 재시작 후 적용됩니다.',
        'settings_save_failed': '설정 저장에 실패했습니다.',
        'settings_saved_title': '저장 완료',
        'settings_save_failed_title': '저장 실패',
        
        # AI 오류 메시지
        'ai_quota_exceeded': 'API 사용량 한계에 도달했습니다.\n잠시 후 다시 시도하거나 API 키를 확인해주세요.',
        'ai_api_test_success': 'API 키가 정상적으로 작동합니다!',
        'ai_api_test_failed': 'API 키 테스트 실패: {error}',
        'ai_api_invalid_key': 'API 키가 유효하지 않습니다.',
        'ai_api_network_error': '네트워크 오류가 발생했습니다. 인터넷 연결을 확인해주세요.',
        'ai_generation_failed': 'AI 팔레트 생성에 실패했습니다: {error}',

        # ai_color_recommender.py
        'ai_recommender_missing_library': "google-generativeai 라이브러리가 설치되지 않았습니다.\n'{install_cmd}'를 실행하세요.",
        'ai_recommender_init_failed': 'Gemini 모델 초기화 실패: {error}',
        'ai_recommender_api_key_not_set': 'API 키가 설정되지 않았습니다.',
        'ai_recommender_generation_failed': 'AI 팔레트 생성 실패: {error}',
        'ai_recommender_test_prompt': "Say 'OK' if you can read this.",
        'ai_recommender_test_success': 'API 키가 정상적으로 작동합니다.',
        'ai_recommender_test_no_response': '응답을 받을 수 없습니다.',
        'ai_recommender_test_failed': 'API 키 테스트 실패: {error}',
        'ai_recommender_prompt_with_keywords': """Create {num_palettes} color palettes ({num_colors} colors each) based on: {keywords}
    Format: PaletteName: #HEX,#HEX,#HEX,#HEX,#HEX
    Example: Ocean Breeze: #0077BE,#00A8E8,#48CAE4,#90E0EF,#ADE8F4
    Give each palette a creative 2-3 word name. Output only palette lines.""",
        'ai_recommender_prompt_without_keywords': """Create {num_palettes} diverse color palettes ({num_colors} colors each).
    Format: PaletteName: #HEX,#HEX,#HEX,#HEX,#HEX
    Example: Sunset Warm: #FF6B35,#F7931E,#FDC830,#F37335,#C0392B
    Give each palette a creative 2-3 word name. Output only palette lines.""",
        
        # 팔레트 편집기 메시지
        'palette_editor_title': '팔레트 편집 - {name}',
        'color_added': '색상이 추가되었습니다.',
        'color_edited': '색상이 수정되었습니다.',
        'select_color_first': '먼저 색상을 선택해주세요.',
        
        # 컨텍스트 메뉴
        'context_rename': '이름 바꾸기',
        'context_edit_palette': '팔레트 편집',
        'context_save_palette': '팔레트 저장',
        'context_export_txt': 'TXT로 내보내기',
        'context_export_png': 'PNG로 내보내기',
        'context_toggle_view': 'RGB로 보기',
        
        # 설정 다이얼로그
        'settings_language_section': '언어 설정',
        'settings_autosave_section': '자동 저장 설정',
        'settings_extraction_section': '색상 추출 설정',
        'settings_ui_section': 'UI 설정',
        'settings_autosave_enable': '자동 저장 사용',
        'settings_autosave_interval': '자동 저장 간격 (초):',
        'settings_max_colors': '최대 색상 수:',
        'settings_filter_background': '배경색 필터링 (흰색/검은색 제외)',
        'settings_window_size': '창 크기:',
        'settings_recent_files': '최근 파일 수:',
        'settings_recent_colors': '최근 사용 색상 최대 수:',
        'button_save': '저장',
        'button_cancel': '취소',
        'button_close': '닫기',
        
        # 이미지 재색상화 다이얼로그
        'recolor_select_palette': '팔레트 선택:',
        'recolor_load_image': '이미지 불러오기',
        'recolor_view_original': '원본 크기로 보기',
        'recolor_preview': '미리보기',
        'recolor_empty_palette': '빈 팔레트입니다',
        
        # 프리셋 팔레트 다이얼로그
        'preset_filter': '필터:',
        'preset_all': '모두',
        'preset_search_color': '색상으로 검색',
        'preset_reset_filter': '필터 초기화',
        'preset_count': '{current} / {total} 팔레트',
        'preset_use': '사용',
        
        # 색상 조화 레이블
        'base_color_label': '기본 색상',
        'complementary_label': '보색',
        'analogous_label': '유사색',
        'triadic_label': '삼각 조화색',
        'color_box_tooltip': '좌클릭: 팔레트에 추가\n우클릭: 기본 색상으로 설정',
        
        # 최근 색상
        'recent_colors_title': '최근 사용 색상',
        'recent_colors_clear': '기록 지우기',
        'recent_colors_empty': '최근 사용한 색상이 없습니다',
        
        # 팔레트 선택
        'selection_required': '선택 필요',
        'select_palette_first': '먼저 오른쪽에서 저장된 팔레트를 선택하세요.',
        'select_palette_to_adjust': '조정할 팔레트를 선택하세요.',
        'saved_palette_default_name': '저장된 팔레트',
        'palette_numbered': '팔레트{i}',
        'copy_suffix': ' (복사)',
        'new_palette_numbered': '새 팔레트{i}',
        'unknown': '알 수 없음',
        'tooltip_palette_color_info': '{hex}\nRGB: {rgb}\n흑백값: {lum}/255',
        'msg_set_base_color_failed': '베이스 색상 설정 실패:\n{error}',

        'color_adjuster_title': '색상 조정',
        'warmth_hint': '(차가움 ← → 따뜻함)',
        'label_rgb': 'RGB: {value}',
        'label_hex': 'HEX: {value}',
        'dialog_open_mps': '팔레트 파일 열기',
        'saved_palettes_list': '저장된 팔레트 목록',
        'browse_other_file': '다른 파일 찾기',
        'load': '불러오기',
        'msg_file_not_found': '파일을 찾을 수 없습니다.',
        'ai_module_missing': 'AI 추천 모듈을 찾을 수 없습니다.',
        'ai_settings_open_failed': 'AI 설정 열기 실패: {error}',
        
        # 접근성 검사기
        'accessibility_title': '접근성 검사',
        'accessibility_check': '대비율 검사',
        'accessibility_wcag_aa': 'WCAG AA 기준',
        'accessibility_wcag_aaa': 'WCAG AAA 기준',
        'accessibility_ratio': '대비율: {ratio}:1',
        'accessibility_pass': '통과',
        'accessibility_fail': '실패',
        
        # 그라디언트 생성기
        'gradient_title': '그라디언트 생성',
        'gradient_steps': '단계 수:',
        'gradient_generate': '생성',
        'gradient_color_from': '시작 색상',
        'gradient_color_to': '끝 색상',
        
        # 커스텀 조화 편집기
        'saved_harmonies': '저장된 조합',
        'new_harmony': '새 조합',
        'delete_harmony': '삭제',
        'harmony_name': '조합 이름:',
        'color_list': '색상 목록',
        'colors': '색상',
        'fixed_color': '고정 색상',
        'add_hsv_color': 'HSV 색상 추가',
        'edit_hsv_color': 'HSV 색상 수정',
        'add_fixed_color': '고정 색상 추가',
        'extract_from_image': '이미지에서 추출',
        'msg_colors_extracted': '{count}개의 색상이 추출되었습니다.',
        'edit': '수정',
        'move_up': '위로',
        'move_down': '아래로',
        'new_harmony': '새 조합',
        'harmony_name': '조합 이름',
        'edit_color': '색상 수정',
        'preview': '미리보기',
    }    
    # 영어 텍스트
    ENGLISH = {
        # 메뉴
        'menu_file': 'File',
        'menu_edit': 'Edit',
        'menu_view': 'View',
        'menu_settings': 'Settings',
        'menu_help': 'Help',
        
        # 파일 메뉴
        'file_new': 'New...',
        'file_open': 'Open...',
        'file_save': 'Save...',
        'file_save_as': 'Save As...',
        'file_import': 'Import',
        'file_export': 'Export',
        'file_exit': 'Exit',
        
        # 편집 메뉴
        'edit_copy': 'Copy',
        'edit_paste': 'Paste',
        'edit_clear': 'Clear',
        
        # 설정 메뉴
        'settings_title': 'Settings...',
        'settings_language': 'Language',
        'settings_theme': 'Theme',
        'settings_api': 'AI Settings...',
        
        # 테마
        'theme_light': 'Light Theme',
        'theme_dark': 'Dark Theme',
        
        # 메인 UI
        'title': 'Color Palette Generator',
        'color_input': 'Color Input',
        'pick_color': 'Pick Color',
        'from_screen': 'From Screen',
        'from_image': 'From Image',
        'upload_image': 'Upload Image',
        'generate_palette': 'Generate Palette',
        'clear_all': 'Clear All',
        'select_image': 'Select Image...',
        'no_file_selected': 'No file selected',
        'extract_from_screen': 'Extract from Screen',
        'generate': 'Generate',
        'random_color': 'Random Color',
        'harmony_options': 'Harmony Options',
        'untitled': 'Untitled',
        'open_recent': 'Open Recent',
        'reset_to_defaults': 'Reset to Defaults',
        'tools': 'Tools',
        'apply_palette_to_image': 'Apply Palette to Image...',
        'custom_color_harmonies': 'Custom Color Harmonies...',
        'preset_palettes': 'Preset Palettes...',
        
        # 색상 조합
        'complementary': 'Complementary',
        'analogous': 'Analogous',
        'triadic': 'Triadic',
        'monochromatic': 'Monochromatic',
        'split_complementary': 'Split Complementary',
        'square': 'Square',
        'tetradic': 'Tetradic',
        'double_complementary': 'Double Complementary',
        
        # AI 팔레트
        'ai_palette': 'AI Palette',
        'ai_generate': 'Generate',
        'ai_clear': 'Clear',
        'ai_keywords': 'Keywords (optional)',
        'ai_num_palettes': 'Number of Palettes',
        'ai_num_colors': 'Colors per Palette',
        'ai_generating': 'Generating AI palettes...',
        'ai_no_palettes': 'No AI palettes. Click Generate to create.',
        
        # 저장된 팔레트
        'saved_palettes': 'Saved Palettes',
        'save_current': 'Save Current Palette',
        'rename': 'Rename',
        'edit_palette': 'Edit Palette',
        'save_palette': 'Save Palette',
        'delete_palette': 'Delete Palette',
        'export_txt': 'Export as TXT',
        'export_png': 'Export as PNG',
        'view_rgb': 'View as RGB',
        'view_value': 'View as Value',
        
        # 팔레트 편집기
        'palette_editor': 'Palette Editor',
        'add_color': 'Add Color',
        'edit_color': 'Edit Color',
        'delete_color': 'Delete Color',
        'hsv_adjust': 'HSV Adjust',
        'confirm': 'OK',
        'cancel': 'Cancel',
        'reset': 'Reset',
        'apply': 'Apply',
        
        # HSV 조정
        'hsv_dialog_title': 'Adjust Color (HSV)',
        'hue': 'Hue',
        'saturation': 'Saturation',
        'value': 'Value',
        'brightness': 'Brightness',
        'contrast': 'Contrast',
        'warmth': 'Warmth',
        'preview': 'Preview',
        
        # 메시지
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Information',
        'success': 'Success',
        'confirm_delete': 'Are you sure you want to delete?',
        'save_success': 'Saved successfully.',
        'load_success': 'Loaded successfully.',
        'invalid_color': 'Invalid color code.',
        'api_error': 'API error occurred.',
        'no_color': 'No colors available.',

        # main.py common messages (image/save/load)
        'save_error_title': 'Save Error',
        'load_error_title': 'Load Error',
        'saved_title': 'Saved',
        'loaded_title': 'Loaded',
        'msg_file_not_found': 'File not found.',
        'msg_large_file_title': 'Large File',
        'msg_large_file_prompt': 'The file size is {size_mb}MB. Continue?',
        'msg_thumbnail_failed': 'Unable to create image preview.',
        'msg_image_load_failed': 'Failed to load image: {error}',
        'msg_no_save_path': 'No save path specified.',
        'msg_workspace_saved': 'Workspace saved to {path}',
        'msg_workspace_loaded': 'Workspace loaded from {path}',
        'msg_permission_denied_write': 'Permission denied.',
        'msg_disk_error': 'Disk error: {error}',
        'msg_save_failed': 'Failed to save: {error}',
        'msg_load_failed': 'Failed to load: {error}',

        'msg_color_picker_failed': 'Color picker error: {error}',
        'msg_screen_picker_failed': 'Screen picker error: {error}',
        'msg_capture_failed': 'Failed to capture screen: {error}',
        'msg_save_screenshot_failed': 'Failed to save screenshot region: {error}',

        'save_prompt_title': 'Save',
        'msg_save_changes_prompt': 'Do you want to save your current work?',
        'msg_generate_palette_first': 'Generate a palette first before saving.',
        'msg_save_txt_failed': 'Failed to save TXT: {error}',
        'msg_save_png_failed': 'Failed to save PNG: {error}',
        'msg_saved_txt_summary': 'Saved {count} TXT file(s) to {dest_dir}',
        'msg_saved_png_summary': 'Saved {count} PNG file(s) to {dest_dir}',
        'msg_select_harmony_required': 'Please select at least one color harmony.',
        'no_recent_files': '(No recent files)',
        'msg_file_not_found_path': 'File not found: {path}',

        'input_error_title': 'Input Error',
        'ai_error_title': 'AI Error',
        'ai_generating_title': 'Generating AI Palettes',
        'ai_palette_name': 'AI Palette {i}',

        'msg_ai_api_key_required': 'Please enter API key in AI Settings.',
        'msg_ai_init_failed': 'AI initialization failed: {error}',
        'msg_palette_generation_failed': 'Palette generation failed: {error}',
        'msg_display_palettes_failed': 'Failed to display palettes: {error}',

        'msg_invalid_hex_prompt': 'Please enter a valid HEX code (e.g., #3498db).',
        'msg_select_image_first': 'Please select an image file.',
        'msg_image_file_not_found': 'Image file not found.',
        'msg_extract_colors_failed': 'Unable to extract colors from the image.',

        'msg_export_png_failed': 'PNG export failed: {error}',

        'export_title': 'Export',
        'my_palette_file': 'My Palette',
        'text_file': 'Text File',
        'export_txt_palette_label': 'Palette: {name}',
        'export_txt_color_count_label': 'Color count: {count}',
        'msg_export_txt_failed': 'TXT export failed: {error}',

        'custom_harmony_default_name': 'Custom Harmony',

        'reset_settings_title': 'Reset Settings',
        'reset_done_title': 'Reset Complete',
        'msg_reset_settings_confirm': 'Restore all settings to defaults?',
        'msg_settings_reset_done': 'Settings have been restored to defaults.\nRestart to apply changes.',
        'msg_no_saved_palettes': 'No saved palettes.\nGenerate and save a palette first.',

        'png_image': 'PNG Image',
        'jpeg_image': 'JPEG Image',
        'msg_load_image_first': 'Load an image first.',
        'msg_empty_palette_cannot_apply': 'Cannot apply an empty palette.',
        'msg_recolor_load_image_failed': 'Failed to load image: {error}',
        'msg_recolor_display_failed': 'Failed to display image: {error}',
        'msg_recolor_save_success': 'Saved recolored image:\n{path}',
        'msg_recolor_save_failed': 'Failed to save: {error}',
        'msg_recolor_preview_failed': 'Failed to generate preview: {error}',
        'msg_image_loaded': 'Image loaded: {filename}',

        'msg_palette_has_no_colors': 'No colors in the palette.',
        'msg_no_valid_colors': 'No valid colors.',
        'msg_color_adjust_unavailable': 'Color adjustment is not available.',
        'msg_color_adjust_failed': 'Color adjustment failed: {error}',

        # Common display/format
        'ellipsis': '...',
        'rgb_unknown': '(?, ?, ?)',
        'label_numbered_rgb': '{i}. RGB: {value}',
        'tooltip_recent_color_info': 'RGB: {rgb}\nHEX: {hex}\nLuminance: {lum}',
        'custom_harmony_numbered': 'Custom {i}',

        # Settings UI
        'settings_window_size_separator': 'x',

        # Preset palettes
        'preset_tags_format': '({tags})',

        # Export (TXT/PNG) file content
        'export_txt_file_header': 'Palettes exported: {timestamp}',
        'export_txt_palette_title': 'Palette {i}',
        'export_txt_line_base': 'Base: {hex} | RGB: {rgb}',
        'export_txt_line_complementary': 'Complementary: {hex} | RGB: {rgb}',
        'export_txt_section_analogous': 'Analogous:',
        'export_txt_section_triadic': 'Triadic:',
        'export_txt_section_monochromatic': 'Monochromatic:',
        'export_txt_color_line': '{hex} | RGB: {rgb}',
        'export_txt_indexed_color_line': '{i}. {hex} | RGB: {rgb}',

        'export_png_palette_title': 'Palette {i}',
        'export_png_label_base': 'Base',
        'export_png_label_complementary': 'Complementary',
        'export_png_label_analogous': 'Analogous',
        'export_png_label_triadic': 'Triadic',
        'export_png_label_monochromatic': 'Monochromatic',
        'export_png_label_numbered': '{label} {i}',
        
        # 버튼
        'ok': 'OK',
        'yes': 'Yes',
        'no': 'No',
        
        # 기타
        'base_color': 'Base Color',
        'representative_color': 'Representative Color',
        'palette_name': 'Palette Name',
        'new_name': 'New Name',
        'enter_name': 'Enter name',
        
        # 팔레트 목록 버튼 툴팁
        'tooltip_add_palette': 'Add Palette',
        'tooltip_delete_palette': 'Remove Palette',
        'tooltip_copy_palette': 'Copy Palette',
        'tooltip_load_palette': 'Load Palette',
        'tooltip_adjust_color': 'Adjust Color',
        
        # 파일 다이얼로그
        'dialog_select_image': 'Select Image',
        'dialog_save_pgf': 'Save PGF...',
        'dialog_save_as': 'Save As...',
        'dialog_open_pgf': 'Open PGF...',
        'dialog_select_image_recolor': 'Select Image',
        'dialog_save_recolored': 'Save Recolored Image',
        
        # 색상 선택 다이얼로그
        'harmonies_title': 'Select Color Harmonies',
        'select_harmonies': 'Select color harmonies to display:',
        'custom_harmonies': 'Custom Harmonies:',
        'pick_color_title': 'Pick Color',
        'add_color_title': 'Add Color',
        'edit_color_title': 'Edit Color',
        
        # 색상 박스 툴팁
        'tooltip_color_box': 'Left click: Add to palette\nRight click: Set as base color',
        
        # 팔레트 편집 버튼
        'sort_by_hue': 'Sort by Hue',
        'sort_by_saturation': 'Sort by Saturation',
        'sort_by_luminance': 'Sort by Luminance',
        'sort_reverse': 'Reverse Order',
        'show_values': 'Show Values',
        
        # 로딩/상태 메시지
        'screenshot_label': '**Screenshot**',
        'no_image_label': 'No image',
        'empty_palette': 'Empty Palette',
        'generating_ai': 'Generating AI palettes...',
        
        # 설정 다이얼로그 섹션
        'settings_language_section': 'Language Settings',
        'settings_theme_section': 'Theme Settings',
        'settings_autosave_section': 'Auto-save Settings',
        'settings_extraction_section': 'Color Extraction Settings',
        'settings_ui_section': 'UI Settings',
        
        # 설정 옵션
        'language_label': 'Language:',
        'theme_label': 'Theme:',
        'autosave_enable': 'Enable Auto-save',
        'autosave_interval': 'Auto-save Interval (seconds):',
        'max_colors': 'Max Colors:',
        'filter_background': 'Filter Background (exclude white/black)',
        'window_size': 'Window Size:',
        'recent_files_count': 'Recent Files Count:',
        
        # 이미지 재색상 다이얼로그
        'select_palette_label': 'Select Palette:',
        'load_image_btn': 'Load Image',
        'view_original_btn': 'View Original Size',
        'save_btn': 'Save',
        'close_btn': 'Close',
        'preview_label': 'Preview',
        
        # AI 설정 다이얼로그
        'ai_api_key_label': 'Gemini API Key:',
        'ai_api_help': 'Get your API key from https://aistudio.google.com/app/apikey',
        'ai_colors_per_palette': 'Colors per Palette:',
        'ai_keywords_label': 'Keywords (comma separated):',
        'ai_keywords_example': 'Example: ocean, calm, blue',
        'ai_test_api': 'Test API Key',
        
        # 일반
        'image_files': 'Image files',
        'all_files': 'All files',
        
        # 다이얼로그 제목
        'dialog_settings': 'Settings',
        'dialog_palette_editor': 'Palette Editor',
        'dialog_ai_settings': 'AI Settings',
        'dialog_select_harmonies': 'Select Color Harmonies',
        'dialog_apply_palette': 'Apply Palette',
        'dialog_custom_harmony': 'Custom Color Harmony',
        'dialog_preset_palettes': 'Preset Palettes',
        'dialog_rename_palette': 'Rename Palette',

        # Common
        'unnamed': 'Unnamed',
        'done': 'Done',

        # Module/Dialog errors
        'custom_harmony_module_missing': 'Custom harmony module not found.',
        'custom_harmony_open_failed': 'Failed to open custom harmony: {error}',
        'preset_module_missing': 'Preset palette module not found.',
        'preset_open_failed': 'Failed to open preset palettes: {error}',

        # Preset palettes
        'preset_added_title': 'Palette Added',
        'preset_added_msg': '"{name}" has been added to saved palettes.',
        'preset_pick_search_color': 'Pick a color to search',

        # Custom harmony
        'custom_harmony_select_delete': 'Please select a harmony to delete.',
        'custom_harmony_confirm_delete': 'Are you sure you want to delete?',
        'custom_harmony_name_required': 'Please enter a harmony name.',
        'custom_harmony_color_required': 'Please add at least one color.',
        'custom_harmony_saved': 'Harmony saved.',
        'custom_harmony_hsv_item': '{i}. HSV (H:{h:+.0f}°, S:{s:+.0f}%, V:{v:+.0f}%)',
        'custom_harmony_fixed_item': '{i}. Fixed Color: {hex}',
        
        # 설정 창 메시지
        'settings_saved': 'Settings saved successfully.\nLanguage changes will be applied after restart.',
        'settings_save_failed': 'Failed to save settings.',
        'settings_saved_title': 'Saved',
        'settings_save_failed_title': 'Save Failed',
        
        # AI 오류 메시지
        'ai_quota_exceeded': 'API quota exceeded.\nPlease try again later or check your API key.',
        'ai_api_test_success': 'API key is working correctly!',
        'ai_api_test_failed': 'API key test failed: {error}',
        'ai_api_invalid_key': 'Invalid API key.',
        'ai_api_network_error': 'Network error occurred. Please check your internet connection.',
        'ai_generation_failed': 'AI palette generation failed: {error}',
        
        # 팔레트 편집기 메시지
        'palette_editor_title': 'Palette Editor - {name}',
        'color_added': 'Color added.',
        'color_edited': 'Color edited.',
        'select_color_first': 'Please select a color first.',
        
        # 컨텍스트 메뉴
        'context_rename': 'Rename',
        'context_edit_palette': 'Edit Palette',
        'context_save_palette': 'Save Palette',
        'context_export_txt': 'Export as TXT',
        'context_export_png': 'Export as PNG',
        'context_toggle_view': 'View as RGB',
        
        # 설정 다이얼로그
        'settings_language_section': 'Language Settings',
        'settings_autosave_section': 'Auto-save Settings',
        'settings_extraction_section': 'Color Extraction Settings',
        'settings_ui_section': 'UI Settings',
        'settings_autosave_enable': 'Enable auto-save',
        'settings_autosave_interval': 'Auto-save interval (seconds):',
        'settings_max_colors': 'Max colors:',
        'settings_filter_background': 'Filter background colors (exclude white/black)',
        'settings_window_size': 'Window size:',
        'settings_recent_files': 'Recent files:',
        'settings_recent_colors': 'Max recent colors:',
        'button_save': 'Save',
        'button_cancel': 'Cancel',
        'button_close': 'Close',
        
        # 이미지 재색상화 다이얼로그
        'recolor_select_palette': 'Select Palette:',
        'recolor_load_image': 'Load Image',
        'recolor_view_original': 'View Original Size',
        'recolor_preview': 'Preview',
        'recolor_empty_palette': 'Empty palette',
        
        # 프리셋 팔레트 다이얼로그
        'preset_filter': 'Filter:',
        'preset_all': 'All',
        'preset_search_color': 'Search by Color',
        'preset_reset_filter': 'Reset Filter',
        'preset_count': '{current} / {total} palettes',
        'preset_use': 'Use',
        
        # 색상 조화 레이블
        'base_color_label': 'Base Color',
        'complementary_label': 'Complementary',
        'analogous_label': 'Analogous',
        'triadic_label': 'Triadic',
        'color_box_tooltip': 'Left click: Add to palette\nRight click: Set as base color',
        
        # 최근 색상
        'recent_colors_title': 'Recent Colors',
        'recent_colors_clear': 'Clear History',
        'recent_colors_empty': 'No recent colors',
        
        # 팔레트 선택
        'selection_required': 'Selection Required',
        'select_palette_first': 'Please select a saved palette on the right first.',
        'select_palette_to_adjust': 'Please select a palette to adjust.',
        'saved_palette_default_name': 'Saved Palette',
        'palette_numbered': 'Palette {i}',
        'copy_suffix': ' (Copy)',
        'new_palette_numbered': 'New Palette {i}',
        'unknown': 'Unknown',
        'tooltip_palette_color_info': '{hex}\nRGB: {rgb}\nGrayscale: {lum}/255',
        'msg_set_base_color_failed': 'Failed to set base color:\n{error}',

        'color_adjuster_title': 'Color Adjustment',
        'warmth_hint': '(Cool ← → Warm)',
        'label_rgb': 'RGB: {value}',
        'label_hex': 'HEX: {value}',
        'dialog_open_mps': 'Open Palette File',
        'saved_palettes_list': 'Saved Palettes List',
        'browse_other_file': 'Browse Other File',
        'load': 'Load',
        'msg_file_not_found': 'File not found.',
        'ai_module_missing': 'AI recommendation module not found.',

        # ai_color_recommender.py
        'ai_recommender_missing_library': "google-generativeai library is not installed.\nRun '{install_cmd}'.",
        'ai_recommender_init_failed': 'Failed to initialize Gemini model: {error}',
        'ai_recommender_api_key_not_set': 'API key is not set.',
        'ai_recommender_generation_failed': 'Failed to generate AI palettes: {error}',
        'ai_recommender_test_prompt': "Say 'OK' if you can read this.",
        'ai_recommender_test_success': 'API key works correctly.',
        'ai_recommender_test_no_response': 'No response received.',
        'ai_recommender_test_failed': 'API key test failed: {error}',
        'ai_recommender_prompt_with_keywords': """Create {num_palettes} color palettes ({num_colors} colors each) based on: {keywords}
    Format: PaletteName: #HEX,#HEX,#HEX,#HEX,#HEX
    Example: Ocean Breeze: #0077BE,#00A8E8,#48CAE4,#90E0EF,#ADE8F4
    Give each palette a creative 2-3 word name. Output only palette lines.""",
        'ai_recommender_prompt_without_keywords': """Create {num_palettes} diverse color palettes ({num_colors} colors each).
    Format: PaletteName: #HEX,#HEX,#HEX,#HEX,#HEX
    Example: Sunset Warm: #FF6B35,#F7931E,#FDC830,#F37335,#C0392B
    Give each palette a creative 2-3 word name. Output only palette lines.""",
        'ai_settings_open_failed': 'Failed to open AI settings: {error}',
        
        # 접근성 검사기
        'accessibility_title': 'Accessibility Check',
        'accessibility_check': 'Check Contrast',
        'accessibility_wcag_aa': 'WCAG AA Standard',
        'accessibility_wcag_aaa': 'WCAG AAA Standard',
        'accessibility_ratio': 'Contrast ratio: {ratio}:1',
        'accessibility_pass': 'Pass',
        'accessibility_fail': 'Fail',
        
        # 그라디언트 생성기
        'gradient_title': 'Generate Gradient',
        'gradient_steps': 'Number of steps:',
        'gradient_generate': 'Generate',
        'gradient_color_from': 'From Color',
        'gradient_color_to': 'To Color',

        # 커스텀 조화 편집기
        'saved_harmonies': 'Saved Harmonies',
        'new_harmony': 'New Harmony',
        'delete_harmony': 'Delete',
        'harmony_name': 'Harmony Name:',
        'color_list': 'Color List',
        'colors': 'Colors',
        'fixed_color': 'Fixed Color',
        'add_hsv_color': 'Add HSV Color',
        'edit_hsv_color': 'Edit HSV Color',
        'add_fixed_color': 'Add Fixed Color',
        'extract_from_image': 'Extract from Image',
        'msg_colors_extracted': '{count} colors extracted.',
        'edit': 'Edit',
        'move_up': 'Move Up',
        'move_down': 'Move Down',
        'new_harmony': 'New Harmony',
        'harmony_name': 'Harmony Name',
        'edit_color': 'Edit Color',
        'preview': 'Preview',
    }
    
    def __init__(self, language='ko'):
        """
        Args:
            language: 'ko' (한국어) 또는 'en' (영어)
        """
        self.language = language
        self.texts = self.KOREAN if language == 'ko' else self.ENGLISH
    
    def get(self, key, default=None):
        """텍스트 가져오기"""
        return self.texts.get(key, default or key)
    
    def set_language(self, language):
        """언어 변경"""
        self.language = language
        self.texts = self.KOREAN if language == 'ko' else self.ENGLISH
    
    def get_current_language(self):
        """현재 언어 반환"""
        return self.language
