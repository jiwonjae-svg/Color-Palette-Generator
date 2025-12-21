# Color Palette Generator

A professional desktop application (Python + Tkinter) for generating, managing, and exporting color palettes with advanced features.

![Application Icon](icon.ico)

## 🎨 Overview

- Generate palettes from HEX colors, random colors, images, or screen-picked colors
- Support for multiple color harmony schemes (complementary, analogous, triadic, monochromatic, and more)
- **Smart palette management** with metadata tracking and visual preview
- **Custom harmony editor** with image color extraction
- Export palettes as PNG/TXT or share as .mps files
- Optional AI palette generation via Google Gemini
- Full Korean/English UI support (i18n)
- Professional icon system across all windows

## ✨ Key Features

### 🎯 Color Input & Extraction
- **HEX Input**: Direct color code entry with validation
- **Color Picker**: Visual color selection with HSV controls
- **Image Extraction**: K-means clustering for dominant colors
- **Screen Picker**: Pick colors from anywhere on your screen
- **Smart Color Analysis**: Extract colors and convert to HSV-based functions

### 🎨 Palette Generation
- **Color Harmony**: 10+ harmony schemes based on color theory
  - Complementary, Analogous, Triadic, Monochromatic
  - Split-Complementary, Square, Tetradic
  - Warm, Cool, and custom variations
- **Custom Harmony Editor**:
  - Create custom color combination rules
  - Add HSV offset colors (hue ±180°, saturation ±100%, value ±100%)
  - Add fixed colors
  - **🆕 Extract from Image**: Automatically analyze image colors based on luminance and create HSV functions
  - Save and reuse custom harmonies
- **Preset Browser**: Browse and use curated professional palettes

### 💾 Smart Palette Management
- **Metadata System**:
  - Track palette name, colors, file path, and timestamp
  - **🆕 Custom Load Dialog**: Visual preview of saved palettes
  - Automatic cleanup of moved/deleted files
  - Sort by date, filter by colors
- **Palette Operations**:
  - Add, remove, copy, rename, edit, reorder
  - Bulk export (all palettes to single file)
  - Individual palette export (.mps format)
- **Recent Colors**:
  - Encrypted storage of recently used colors
  - Configurable limit (1-100 colors)
  - Horizontal scrolling strip

### 📤 Export & Sharing
- **PNG Export**: 
  - Individual palette images
  - Bulk export with all palettes
  - Customizable dimensions
- **TXT Export**: 
  - Color codes (HEX, RGB)
  - Palette metadata
- **MPS Format**: 
  - Custom palette file format
  - Encrypted and portable
- **Image Recoloring**: 
  - Apply any palette to images
  - Live preview before saving
  - Support for PNG, JPG, BMP

### 🤖 AI Features (Optional)
- **AI Palette Generation**: Powered by Google Gemini
  - Generate palettes from text descriptions
  - Keyword-based generation
  - Multiple variations at once
  - Named palettes with creative titles
- **Smart Suggestions**: Context-aware color recommendations

### 🎭 User Interface
- **Multi-language**: Korean/English with easy switching
- **Theme Support**: Light/dark mode compatible
- **🆕 Unified Icons**: Professional icon across all windows and dialogs
- **Responsive Design**: All dialogs properly sized and positioned
- **Accessibility**: High contrast support, keyboard navigation

## 📋 Requirements

- **Python**: 3.10+ (tested on 3.14.2)
- **Platform**: Windows 10/11 (primary), macOS/Linux (untested)
- **Built-in**: tkinter
- **Required packages**:
  - `Pillow` (image processing)
  - `cryptography` (secure data storage)
  - `numpy` (color calculations)
- **Optional packages**:
  - `google-generativeai` (AI palette generation)

## 🚀 Installation

### Basic Installation
```bash
pip install pillow cryptography numpy
```

### With AI Features
```bash
pip install pillow cryptography numpy google-generativeai
```

### From Requirements File
```bash
pip install -r requirements.txt
```

## 💻 Running the Application

### From Source
```bash
python main.py
```

### As Executable (Windows)
1. Build with PyInstaller:
   ```bash
   pyinstaller ColorPaletteGenerator.spec
   ```
2. Run `dist/ColorPaletteGenerator.exe`

## 🤖 AI (Gemini) Setup (Optional)

1. Open **Settings → AI Settings** in the app
2. Get your API key:
   - Visit: https://aistudio.google.com/app/apikey
   - Create a new API key
3. Paste the key in the settings dialog
4. Test the connection
5. Configure:
   - Number of colors per palette (1-10)
   - Keywords for palette generation

**Note**: If `google-generativeai` is not installed, AI features will be hidden until you install the package.

## 📁 Data & Storage

All application data is stored in the `data/` folder with encryption:

### Configuration Files
- `config.dat`: Main settings (encrypted)
  - Language preference
  - Window size/position
  - Recent colors list
  - Auto-save settings
- `ai_settings.dat`: AI configuration (encrypted)
  - API key (encrypted)
  - Generation parameters
- `custom_harmonies.dat`: Custom harmony rules (encrypted)
- `preset_palettes.dat`: Preset palette library (encrypted)
- `palette_metadata.dat`: **🆕 Saved palette metadata** (encrypted)
  - Palette names and paths
  - Color previews
  - Timestamps

### Security
- All data files use `cryptography.Fernet` for AES encryption
- Embedded encryption key for simplicity
- No plain text storage of sensitive data

## 🏗️ Project Structure

```
Color_Palette/
├── main.py                      # Main application and UI
├── color_generator.py           # Palette generation and color extraction
├── color_adjuster.py           # Color adjustment utilities
├── image_recolorer.py          # Image recoloring engine
├── ai_color_recommender.py     # Google Gemini integration
├── file_handler.py             # Encrypted file operations
├── config_manager.py           # Settings management
├── language_manager.py         # i18n strings (KO/EN)
├── custom_harmony.py           # Custom harmony logic
├── preset_generator.py         # Preset palette management
├── preset_browser.py           # Preset browser UI
├── palette_sharing.py          # Palette export/import
├── embedded_icon.py            # 🆕 Embedded icon data (base64)
├── icon.ico                    # 🆕 Application icon
├── ColorPaletteGenerator.spec  # PyInstaller build spec
├── data/                       # Application data (created at runtime)
│   ├── config.dat
│   ├── palette_metadata.dat    # 🆕
│   └── *.dat
└── Temp/                       # Temporary files
```

## 🔧 Development

### Building Executable
```bash
# First time: create icon
python convert_icon.py

# Embed icon data
python embed_icon.py

# Build executable
pyinstaller ColorPaletteGenerator.spec
```

Output: `dist/ColorPaletteGenerator.exe`

### Adding New Languages
1. Edit `language_manager.py`
2. Add language dictionary (e.g., `JAPANESE`)
3. Update `__init__` to support new language code

### Custom Harmony Development
1. Colors can be either HSV offsets or fixed colors
2. HSV offsets are relative to base color
3. System automatically calculates final colors

## 💡 Tips & Tricks

### Color Extraction
- **Image Quality**: Use high-quality images for better color extraction
- **Background Filtering**: Enable to ignore white/black backgrounds
- **Color Count**: 3-7 colors usually work best

### Custom Harmonies
- **🆕 Image Extraction**: Use the "Extract from Image" button to automatically create harmonies based on image colors
- **Base Color**: The brightest color (highest luminance) becomes the base
- **HSV Functions**: Other colors are converted to HSV offsets from the base
- **Test Often**: Preview your harmony with different base colors

### Palette Management
- **🆕 Smart Loading**: Use the visual palette selector when loading
- **Organization**: Use descriptive names for easy identification
- **Backup**: Export important palettes as .mps files
- **Cleanup**: Metadata is automatically cleaned when files are missing

### Performance
- **Recent Colors**: Limit to 20-30 for best performance
- **Auto-save**: Enable to prevent data loss
- **Image Size**: Resize large images before color extraction

### Keyboard Shortcuts
- `Ctrl+S`: Save workspace
- `Ctrl+O`: Open workspace
- `Ctrl+N`: New workspace
- `F5`: Refresh/regenerate palettes

## 🐛 Troubleshooting

### Icon Not Showing
- Ensure `embedded_icon.py` exists
- Fallback: Icon will try to load from `icon.ico`
- Rebuild: Run `python embed_icon.py`

### AI Features Missing
- Install: `pip install google-generativeai`
- Check API key in Settings → AI Settings
- Verify internet connection

### Palette Load Issues
- Check if .mps files still exist at original location
- Use "Browse Other File" if file was moved
- Metadata is automatically cleaned

### Language Not Changing
- Restart the application after language change
- Check `data/config.dat` exists and is writable

### Windows Defender Alert
- This is normal for PyInstaller executables
- Add exception if needed
- Or use Python source directly

## 📝 Recent Updates

### Latest Version
- ✅ **Palette Metadata System**: Track and display saved palettes with visual previews
- ✅ **Custom Load Dialog**: Beautiful palette selector with color previews
- ✅ **Image-Based Harmony**: Extract colors from images and create HSV functions
- ✅ **Icon System**: Professional icons across all windows
- ✅ **Icon Embedding**: Base64-embedded icon, no external files needed
- ✅ **Auto Cleanup**: Automatically remove metadata for missing files

### Previous Updates
- Custom harmony editor with HSV controls
- Preset palette browser
- Image recoloring with preview
- AI palette generation
- Multi-language support

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For bug reports, feature requests, or questions, please open an issue on GitHub.

---

**Enjoy creating beautiful color palettes! 🎨**
