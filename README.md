# Dataset Pre-Processor (Streamlit)

A beautiful, fast, and flexible **image dataset processor** built with Streamlit.

- 🧼 **Background Remove** (powered by `rembg`)
- 🧩 **Pad to Square** (auto or custom size)
- 🎨 **Custom Background Color** *(available only for Background Remove & Do All)*
- 🌞 **Brightness Enhance**
- 📐 **Resize** (keep aspect: pad/crop, or stretch)
- 🗂️ **Native Folder Picker** on local runs (Tkinter)
- 📦 **ZIP input/output** for remote/cloud use
- 🖼️ Optional **Before/After slider** preview
- ✨ Modern UI with theme accents, glass cards, and helpful logs

> **Note:** The native folder dialog opens only when you run Streamlit **on your local machine**. On a server/cloud, use the ZIP options.

---

## Table of Contents

- [Demo](#demo)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Run the App](#run-the-app)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Supported Formats & Saving](#supported-formats--saving)
- [Troubleshooting](#troubleshooting)
- [Customization](#customization)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Demo

- **Hero UI, glass cards, and theme accents**
- **Preview tab** shows first few images from the selected dataset
- **Run Log & Errors tabs** keep you informed during processing
- **Before/After** slider (first processed image)

> Add screenshots or GIFs here (recommended).

---

## Features

### Operations

- **Background Remove**
  - Background: **Transparent**, **White**, or **Custom color** *(with opacity %)*
  - **Uniform padding (px)**
  - **Pad to square**: Auto (fit longest side) or **Custom size (px)** with **Do not upscale**
- **Resize**
  - Modes: **keep_aspect_pad**, **keep_aspect_crop**, **stretch**
  - Width/Height (px)
  - *(No color picker in Resize-only mode)*
- **Brightness Enhance**
  - Slider: **0.2 → 2.5** (1.0 = original)
- **Do All**
  - Pipeline: Background Remove → Brightness → Resize  
  - If **Pad to square** is ON, **Resize** is disabled (to avoid conflicts)

### Input / Output

- **Input**
  - 📁 **Browse local folder** (native OS dialog via Tkinter; local runs only)
  - 📦 **Upload ZIP** (great for remote/cloud deployments)
- **Output**
  - 📂 **Browse local folder**
  - ⬇️ **Download as ZIP**

### UI/UX

- Sidebar workflow, main content for controls & preview
- Theme accent picker (Purple / Blue / Emerald / Rose)
- Glass cards, gradient hero header, helpful metrics and progress

---

## Requirements

- **Python** 3.9+
- **Tkinter** (for the native folder dialog on local runs)
  - Windows/macOS: usually included
  - Ubuntu/Debian: `sudo apt-get install -y python3-tk`

`requirements.txt`:
```txt
streamlit>=1.36.0
pillow>=10.3.0
rembg>=2.0.57
numpy>=1.26.0
streamlit-image-comparison>=0.0.4
```

The app gracefully falls back if `streamlit-image-comparison` isn’t available.

---

## Installation

```bash
git clone <your-repo-url>
cd <your-repo-folder>

# (optional) create & activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Run the App

```bash
streamlit run app.py
```

- A browser tab will open automatically (default: `http://localhost:8501`).
- On local runs, use the **📁 Choose input folder** / **📂 Choose output folder** buttons.
- On servers/cloud, use **Upload ZIP** and **Download as ZIP**.

---

## Usage

1. **Select Operation** (sidebar)
   - **Background Remove**
   - **Resize**
   - **Brightness Enhance**
   - **Do all (Background Remove, Resize, Brightness Enhance)**
2. **Choose Input**
   - **Browse local folder** *(local runs)* or **Upload ZIP**
3. **Choose Output**
   - **Browse local folder** or **Download as ZIP**
4. **Configure Options** (main area)
   - **Background & Canvas** (shown for **Background Remove**/**Do All**)
     - Background: **Transparent / White / Custom color** (+ **Opacity %**)
     - **Uniform padding**
     - **Pad to square** (Auto/Custom size; optional no-upscale)
   - **Brightness** (for **Brightness**/**Do All**)
   - **Resize** (for **Resize**/**Do All**; disabled if Square is ON)
5. Click **🚀 Run Processing**.
6. View **Preview**, **Run Log**, and **Errors** tabs.

> **Rule:** The **color picker** only appears in **Background Remove** and **Do All** (by design).

---

## How It Works

- Images are discovered recursively in the chosen input folder (or unzipped input).
- For background removal, the app uses `rembg` and Pillow to:
  - Remove background → apply padding → optionally center in a square canvas → composite onto the selected background (transparent/white/custom color).
- For **Do All**, the pipeline is:
  1) Background Remove  
  2) Brightness Enhance  
  3) Resize *(skipped if square is ON)*

---

## Supported Formats & Saving

**Input:** `.jpg .jpeg .png .webp .bmp .tiff .tif`  
**Output:**
- If the result has **alpha** (transparency), it saves as **PNG/WebP**.
- If fully **opaque**, it saves as **JPG/PNG** (JPG by default).

> Want all outputs to be PNG or JPG? Open an issue/PR to add a global format override.

---

## Troubleshooting

- **No folder dialog on remote host:**  
  Native dialogs can’t open on servers/cloud. Use **ZIP** input/output instead.
- **Tkinter not found (Linux):**  
  `sudo apt-get install -y python3-tk`
- **Processing seems slow for huge datasets:**  
  Run locally if possible, split the dataset into batches, or open an issue to add **parallel processing**.
- **Transparency vs JPG:**  
  Transparent backgrounds require PNG/WebP. To force opaque output, choose **White** or a fully opaque **Custom color**.

---

## Customization

- **Theme Accent:** change in the sidebar (Purple / Blue / Emerald / Rose)
- **Add ons (ideas):**
  - Contrast & Sharpness sliders
  - Background blur for mockups
  - “Skip existing files” toggle
  - Parallel/multi-core processing

Open an issue if you want these pre-wired.

---

## Project Structure

```
.
├── app.py               # Streamlit app
├── requirements.txt     # Dependencies
└── README.md            # This file
```

---

## Roadmap

- [ ] Optional **contrast** & **sharpness** sliders  
- [ ] **Parallel processing** for large datasets  
- [ ] **Background blur** effect  
- [ ] **Gallery** of multiple before/after pairs

---

## Contributing

PRs welcome! Please:
1. Open an issue to discuss major changes.
2. Keep styles consistent with the current UI design.
3. Test on at least one local OS (Windows/macOS/Linux).

---

## License

**MIT** — see `LICENSE`.

---

## Acknowledgements

- Background removal by the fantastic [`rembg`](https://github.com/danielgatis/rembg)
- Streamlit for a great developer experience
- `streamlit-image-comparison` for the before/after slider
