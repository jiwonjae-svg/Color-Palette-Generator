# Color Palette Generator (Tkinter)

A lightweight desktop app (Python + Tkinter) for generating, managing, and exporting color palettes.

- Generates palettes from a HEX color, a random color, an image, or a screen-picked color
- Supports multiple harmony schemes (complementary / analogous / triadic / monochromatic + more)
- Saves palettes locally and exports as PNG/TXT
- Includes optional AI palette generation via Google Gemini
- Korean/English UI (i18n)

## Features

- **Color input**: HEX input, color picker
- **Extract colors**:
  - From **image** (K-means style extraction)
  - From **screen** (screen picker)
- **Palette generation**: harmony-based palettes
- **Recent colors**:
  - Stored in encrypted config (see “Data & Storage”)
  - Max count configurable (1–100)
  - Single-row strip with horizontal scrolling
- **Saved palettes**: add/remove/copy/load
- **Export**:
  - **PNG** palette image
  - **TXT** palette info
- **Image recolor**: apply a saved palette to an image (preview + save)
- **AI palettes (optional)**: generate named palettes from keywords using Gemini

## Requirements

- Python **3.10+** (tested on Windows)
- Built-in: `tkinter`
- Third-party:
  - `Pillow`
  - `cryptography`
  - `numpy` (used by image recoloring)
  - Optional: `google-generativeai` (AI palette generation)

## Installation

```bash
pip install pillow cryptography numpy
# Optional (AI palettes)
pip install google-generativeai
```

## Run

```bash
python main.py
```

## AI (Gemini) Setup (Optional)

1. Open **Settings → AI Settings** in the app.
2. Create an API key at: https://aistudio.google.com/app/apikey
3. Paste the key and test it.

If `google-generativeai` is not installed, AI features will be unavailable until you install it.

## Data & Storage

The app stores settings and small app state in the `data/` folder:

- `data/config.dat`
  - Encrypted settings
  - Includes `recent_colors` and `max_recent_colors`
- Other `*.dat` files may be created for specific features (e.g., AI settings)

**Note:** The app uses `cryptography.Fernet` via the internal `FileHandler` module for encrypted persistence.

## Project Structure (high level)

- `main.py`: UI (Tkinter) and app orchestration
- `language_manager.py`: Korean/English strings
- `color_generator.py`: palette generation + image color extraction
- `image_recolorer.py`: recolor logic
- `ai_color_recommender.py`: Gemini integration (optional)
- `file_handler.py`: encrypted save/load helpers
- `config_manager.py`: settings management

## Tips

- **Recent Colors scroll**: move your mouse over the Recent Colors panel and use the mouse wheel to scroll horizontally.
- **Language**: language change may require restart to fully apply everywhere.

## License

Add your preferred license (e.g., MIT) before publishing.
