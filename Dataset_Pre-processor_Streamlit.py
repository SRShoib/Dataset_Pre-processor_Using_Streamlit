import os
import io
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional

import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
from rembg import remove
from datetime import datetime


# Optional before/after slider
try:
    from streamlit_image_comparison import image_comparison
    HAS_COMPARISON = True
except Exception:
    HAS_COMPARISON = False

# Native folder picker (local runs)
try:
    import tkinter as tk
    from tkinter import filedialog
except:
    tk = None
    filedialog = None



# =========================
# Styling (CSS)
# =========================
def inject_css(accent="#7c3aed", accent2="#a78bfa"):
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Poppins:wght@500;700&display=swap');
:root {{ --accent: {accent}; --accent-2: {accent2}; }}
html, body, [class*="css"]  {{ font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial; }}
.block-container {{ padding-top: .8rem!important; padding-bottom: 2.2rem!important; }}
.hero {{ border-radius: 18px; padding: 18px 22px;
  background: linear-gradient(120deg, color-mix(in srgb, var(--accent) 18%, transparent), color-mix(in srgb, var(--accent-2) 22%, transparent));
  border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  box-shadow: 0 10px 30px color-mix(in srgb, var(--accent) 20%, transparent);}}
.hero h1 {{ margin:0 0 6px 0; font-family:'Poppins', Inter; font-weight:700; letter-spacing:.2px; }}
.badges {{ display:flex; gap:.5rem; flex-wrap:wrap; }}
.badge {{ display:inline-flex; align-items:center; gap:.38rem; padding:.28rem .65rem; border-radius:999px;
  border: 1px solid color-mix(in srgb, var(--accent) 35%, transparent); background: color-mix(in srgb, var(--accent) 10%, transparent); font-size:.83rem; }}
.card {{ border-radius: 16px; padding: 14px 16px; background: color-mix(in srgb, white 70%, transparent);
  border: 1px solid rgba(0,0,0,.06); box-shadow: 0 12px 26px rgba(0,0,0,.07); margin-bottom: 20px; }}
[data-theme="dark"] .card {{ background: color-mix(in srgb, #15171c %, transparent); border:1px solid rgba(255,255,255,.08); box-shadow:0 14px 30px rgba(0,0,0,.45); }}
.stButton > button {{ border-radius: 12px!important; padding:.65rem .9rem!important; border:1px solid rgba(0,0,0,.06)!important; }}
.stButton > button[kind="primary"] {{ background: var(--accent)!important; border:0!important; }}
.stButton > button:hover {{ filter: brightness(1.02); }}
hr.divider {{ margin:.6rem 0 1.2rem 0; border:none; height:1px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 30%, transparent), transparent); }}
.caption-tight {{ opacity:.85; font-size:.9rem; }}
footer {{ visibility: hidden; }}
</style>
""",
        unsafe_allow_html=True,
    )


# =========================
# FS & Helpers
# =========================
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".JPG", ".JPEG", ".PNG", ".WEBP", ".BMP", ".TIFF", ".TIF"}

def list_images(root: Path) -> List[Path]:
    if not root.exists():
        return []
    try:
        return [p for p in root.rglob("*") if p.suffix.lower() in VALID_EXTS]
    except Exception:
        return []

def ensure_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def pick_directory_dialog() -> Optional[Path]:
    if tk is None:
        st.warning("Folder picker not available on Streamlit Cloud. Use ZIP upload instead.")
        return None
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory()
        root.destroy()
        if folder:
            return Path(folder)
    except Exception:
        pass
    return None

def unzip_to_temp(zf: io.BytesIO) -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="input_zip_"))
    with zipfile.ZipFile(zf) as z:
        z.extractall(tmpdir)
    return tmpdir

def zip_dir_to_bytes(dir_path: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in dir_path.rglob("*"):
            if p.is_file():
                z.write(p, arcname=str(p.relative_to(dir_path)))
    buf.seek(0)
    return buf.read()

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join([c*2 for c in h])
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return r, g, b


# =========================
# Image Ops
# =========================
def remove_bg_and_square(img: Image.Image, *,
                         bg_mode: str,
                         bg_rgba: Tuple[int, int, int, int],
                         pad: int,
                         square: bool,
                         square_size: Optional[int],
                         no_upscale: bool) -> Image.Image:
    """
    bg_mode: 'transparent' | 'white' | 'custom'
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    out = remove(img)

    if pad > 0:
        out = ImageOps.expand(out, border=pad, fill=(0, 0, 0, 0))

    if square:
        w, h = out.size
        if square_size and square_size > 0:
            target = int(square_size)
            scale = min(target / w, target / h)
            if scale < 1 or (scale > 1 and not no_upscale):
                use_scale = scale if (scale < 1 or not no_upscale) else 1.0
                new_w = max(1, int(round(w * use_scale)))
                new_h = max(1, int(round(h * use_scale)))
                if (new_w, new_h) != (w, h):
                    out = out.resize((new_w, new_h), Image.LANCZOS)
                    w, h = out.size
            canvas = Image.new("RGBA", (target, target), (0, 0, 0, 0))
            canvas.paste(out, ((target - w) // 2, (target - h) // 2), out)
            out = canvas
        else:
            side = max(w, h)
            canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            canvas.paste(out, ((side - w) // 2, (side - h) // 2), out)
            out = canvas

    # Composite onto chosen background
    if bg_mode == "white":
        bg = Image.new("RGBA", out.size, (255, 255, 255, 255))
        bg.alpha_composite(out)
        out = bg.convert("RGB")
    elif bg_mode == "custom":
        bg = Image.new("RGBA", out.size, bg_rgba)
        bg.alpha_composite(out)
        out = bg.convert("RGB") if bg_rgba[3] == 255 else bg

    return out


def apply_brightness(img: Image.Image, factor: float) -> Image.Image:
    if factor == 1.0:
        return img
    return ImageEnhance.Brightness(img).enhance(factor)


def resize_image(img: Image.Image, enable: bool, w: int, h: int,
                 mode: str, bg_mode: str, bg_rgba: Tuple[int, int, int, int]) -> Image.Image:
    if not enable or w <= 0 or h <= 0:
        return img
    if mode == "stretch":
        return img.resize((w, h), Image.LANCZOS)

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    src_w, src_h = img.size
    src_ratio, dst_ratio = src_w / src_h, w / h

    def make_canvas(size):
        if bg_mode == "transparent":
            return Image.new("RGBA", size, (0, 0, 0, 0))
        if bg_mode == "white":
            return Image.new("RGB", size, (255, 255, 255))
        if bg_rgba[3] == 255:
            return Image.new("RGB", size, bg_rgba[:3])
        return Image.new("RGBA", size, bg_rgba)

    if mode == "keep_aspect_pad":
        if src_ratio > dst_ratio:
            new_w, new_h = w, int(round(w / src_ratio))
        else:
            new_h, new_w = h, int(round(h * src_ratio))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        canvas = make_canvas((w, h))
        ox, oy = (w - new_w) // 2, (h - new_h) // 2
        canvas.paste(resized, (ox, oy), resized)
        return canvas

    if mode == "keep_aspect_crop":
        if src_ratio < dst_ratio:
            new_w, new_h = w, int(round(w / src_ratio))
        else:
            new_h, new_w = h, int(round(h * src_ratio))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        left, top = (new_w - w) // 2, (new_h - h) // 2
        cropped = resized.crop((left, top, left + w, top + h))
        if bg_mode == "white" or (bg_mode == "custom" and bg_rgba[3] == 255):
            return cropped.convert("RGB")
        return cropped

    return img


def save_image(out_img: Image.Image, out_path: Path):
    ensure_dir(out_path)
    if out_img.mode == "RGBA":
        if out_path.suffix.lower() not in {".png", ".webp"}:
            out_path = out_path.with_suffix(".png")
        out_img.save(out_path)
    else:
        if out_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            out_path = out_path.with_suffix(".jpg")
        out_img.save(out_path, quality=95)


def process_one(in_path: Path, in_root: Path, out_root: Path, *,
                operation: str,
                bg_mode: str,
                bg_rgba: Tuple[int, int, int, int],
                pad: int,
                square: bool,
                square_size: Optional[int],
                no_upscale: bool,
                brightness: float,
                enable_resize: bool,
                target_w: int,
                target_h: int,
                resize_mode: str) -> Tuple[Path, Path, bool, str]:
    try:
        rel = in_path.relative_to(in_root)
        out_path = (out_root / rel).with_suffix(rel.suffix)

        with Image.open(in_path) as im:
            base = im.convert("RGBA") if im.mode not in ("RGB", "RGBA") else im

            if operation == "bg_only":
                out = remove_bg_and_square(base, bg_mode=bg_mode, bg_rgba=bg_rgba,
                                           pad=pad, square=square, square_size=square_size, no_upscale=no_upscale)
            elif operation == "resize_only":
                out = resize_image(base, True, target_w, target_h, resize_mode, bg_mode, bg_rgba)
            elif operation == "brightness_only":
                out = apply_brightness(base, brightness)
            else:  # do_all
                out = remove_bg_and_square(base, bg_mode=bg_mode, bg_rgba=bg_rgba,
                                           pad=pad, square=square, square_size=square_size, no_upscale=no_upscale)
                out = apply_brightness(out, brightness)
                if enable_resize:
                    out = resize_image(out, True, target_w, target_h, resize_mode, bg_mode, bg_rgba)

        save_image(out, out_path)
        return in_path, out_path, True, ""
    except Exception as e:
        return in_path, Path(), False, str(e)


# =========================
# App
# =========================
st.set_page_config(page_title="Dataset Pre-processor", page_icon="🖼️", layout="wide")
inject_css()

# Theme accent
accent_choice = st.sidebar.selectbox("Theme accent", ["Purple", "Blue", "Emerald", "Rose"])
accent_map = {
    "Purple": ("#7c3aed", "#a78bfa"),
    "Blue": ("#2563eb", "#60a5fa"),
    "Emerald": ("#059669", "#34d399"),
    "Rose": ("#e11d48", "#fb7185"),
}
inject_css(*accent_map[accent_choice])

# Hero
st.markdown(
    """
<div class="hero">
  <h1>🖼️ Dataset Pre-processor</h1>
  <div class="badges">
    <span class="badge">Background Remove</span>
    <span class="badge">Resize</span>
    <span class="badge">Brightness</span>
    <span class="badge">Square</span>
    <span class="badge">ZIP in/out</span>
    <span class="badge">Custom BG Color</span>
  </div>
  <div class="caption-tight" style="margin-top:.35rem;">Clean datasets faster with a beautiful, focused UI.</div>
  <div class="caption-tight" style="margin-top:.35rem;">Only support: ".jpg, .jpeg, .png, .webp, .bmp, .tiff, .tif"</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div style="display:flex;justify-content:center;margin:.4rem 0 0.6rem 0;">
        <span class="badge">© {datetime.now().year} Developed by <b>Md. Mehedi Hasan Shoib</b></span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<hr class="divider"/>', unsafe_allow_html=True)

# Sidebar — global workflow
with st.sidebar:
    st.header("🎛️ Operation")
    operation = st.radio(
        "Select Operation",
        ["Background Remove", "Resize", "Brightness Enhance", "Do all (Background Remove, Resize, Brightness Enhance)"],
    )
    op_map = {
        "Background Remove": "bg_only",
        "Resize": "resize_only",
        "Brightness Enhance": "brightness_only",
        "Do all (Background Remove, Resize, Brightness Enhance)": "do_all",
    }
    operation_key = op_map[operation]

    st.subheader("📥 Input")
    input_method = st.radio(
        "Pick source",
        ["Browse local folder","Upload ZIP", "Import from Google Drive"],
        horizontal=True
    )
    selected_input_dir: Optional[Path] = None

    if input_method == "Browse local folder":
        if st.button("📁 Choose input folder"):
            chosen = pick_directory_dialog()
            if chosen:
                st.session_state["chosen_input_dir"] = str(chosen.resolve())
        if "chosen_input_dir" in st.session_state:
            selected_input_dir = Path(st.session_state["chosen_input_dir"])
            st.success(f"Input: {selected_input_dir}")
        st.caption("Use native folder dialog on local runs.")
    elif input_method == "Upload ZIP":
        up = st.file_uploader("Upload dataset ZIP", type=["zip"], key="zip_uploader")
        if up is not None:
            st.session_state["uploaded_zip"] = up.getvalue()
            st.success("ZIP uploaded.")
    
    elif input_method == "Import from Google Drive":
        st.info("Paste the **Google Drive link** (file or folder). Make sure it’s shared publicly or accessible via 'Anyone with the link'.")
        drive_url = st.text_input("🔗 Google Drive link")
        if drive_url:
            import requests, re, io, zipfile, tempfile
            from pathlib import Path
    
            # Detect file ID from Google Drive link
            match = re.search(r'/d/([a-zA-Z0-9_-]+)', drive_url)
            if not match:
                st.error("Invalid Google Drive link.")
            else:
                file_id = match.group(1)
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
                try:
                    st.write("Downloading from Google Drive...")
                    response = requests.get(download_url)
                    if response.status_code == 200:
                        tmpdir = Path(tempfile.mkdtemp(prefix="input_drive_"))
                        # Try unzip if it's a ZIP
                        try:
                            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                                z.extractall(tmpdir)
                                st.success(f"Dataset downloaded and extracted to: {tmpdir}")
                                st.session_state["chosen_input_dir"] = str(tmpdir)
                        except zipfile.BadZipFile:
                            st.error("This Google Drive file is not a ZIP. Please upload or link a ZIP dataset.")
                    else:
                        st.error("Failed to download file from Google Drive. Check permissions.")
                except Exception as e:
                    st.error(f"Download error: {e}")

    st.subheader("📤 Output")
    output_method = st.radio("Save to", ["Browse local folder", "Download as ZIP"], horizontal=True)
    selected_output_dir: Optional[Path] = None
    if output_method == "Browse local folder":
        if tk is None:
            st.warning("Folder picker not available on Streamlit Cloud. Use Download as ZIP  instead.")
        else:
            if st.button("📂 Choose output folder"):
                chosen = pick_directory_dialog()
                if chosen:
                    st.session_state["chosen_output_dir"] = str(chosen.resolve())
            if "chosen_output_dir" in st.session_state:
                selected_output_dir = Path(st.session_state["chosen_output_dir"])
                st.success(f"Output: {selected_output_dir}")
            st.caption("Pick or create a folder to store results.")

# ========= Show ONLY the relevant controls per operation =========

# Defaults (safe fallbacks if a section is hidden)
bg_mode, bg_rgba, pad, square, square_size, no_upscale = "transparent", (0,0,0,0), 0, False, 0, True
brightness = 1.0
enable_resize, target_w, target_h, resize_mode = False, 0, 0, "keep_aspect_pad"

# ---- Background Remove ONLY ----
if operation_key == "bg_only":
    st.subheader("⚙️ Background & Canvas")
    st.markdown('<div class="card">', unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)
    bg_choice = b1.selectbox("Background", ["transparent", "white", "custom color"], index=0)
    pad = b2.number_input("Uniform padding (px)", 0, 512, 0, 2)
    square = b3.toggle("Make it square", value=False, help="Disables Resize when ON!:(It will resize to square like (512x512))")

    bg_color_hex = "#ffffff"
    bg_alpha_pct = 100
    if bg_choice == "custom color":
        c1, c2 = st.columns([2, 1])
        bg_color_hex = c1.color_picker("Pick background color", value="#ffffff")
        bg_alpha_pct = c2.slider("Opacity (%)", 0, 100, 100, help="100% = opaque")

    if bg_choice == "transparent":
        bg_mode = "transparent"; bg_rgba = (0,0,0,0)
    elif bg_choice == "white":
        bg_mode = "white"; bg_rgba = (255,255,255,255)
    else:
        r,g,b = hex_to_rgb(bg_color_hex); a = int(round(bg_alpha_pct/100*255))
        bg_mode = "custom"; bg_rgba = (r,g,b,a)

    square_size = 0; no_upscale = True
    if square:
        sq_mode = st.radio("Square mode", ["Auto (fit longest side)", "Custom size (px)"], horizontal=True)
        if sq_mode == "Custom size (px)":
            s1, s2 = st.columns([2, 1])
            square_size_val = s1.number_input("Square size (px)", 32, 8192, 512)
            no_upscale = s2.checkbox("Do not upscale", True)
            square_size = int(square_size_val)
    st.markdown('</div>', unsafe_allow_html=True)

# ---- Resize ONLY ----
elif operation_key == "resize_only":
    st.subheader("📐 Resize")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    enable_resize = r1.checkbox("Enable", True)
    target_w = r2.number_input("Width (px)", 1, 8192, 512, disabled=not enable_resize)
    target_h = r3.number_input("Height (px)", 1, 8192, 512, disabled=not enable_resize)
    resize_mode = r4.selectbox("Mode", ["keep_aspect_pad","keep_aspect_crop","stretch"], disabled=not enable_resize)
    st.caption("Background & Canvas is hidden for Resize-only.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---- Brightness ONLY ----
elif operation_key == "brightness_only":
    st.subheader("✨ Brightness")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    brightness = st.slider("Brightness factor", 0.2, 2.5, 1.0, 0.05)
    st.caption("Background & Resize sections are hidden for Brightness-only.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---- DO ALL (show all three) ----
else:  # do_all
    # Background & Canvas
    st.subheader("⚙️ Background & Canvas")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    bg_choice = b1.selectbox("Background", ["transparent", "white", "custom color"], index=0)
    pad = b2.number_input("Uniform padding (px)", 0, 512, 0, 2)
    square = b3.toggle("Pad to square", value=False, help="Disables Resize when ON!:(It will resize to square like (512x512)")

    bg_color_hex = "#ffffff"
    bg_alpha_pct = 100
    if bg_choice == "custom color":
        c1, c2 = st.columns([2, 1])
        bg_color_hex = c1.color_picker("Pick background color", value="#ffffff")
        bg_alpha_pct = c2.slider("Opacity (%)", 0, 100, 100, help="100% = opaque")

    if bg_choice == "transparent":
        bg_mode = "transparent"; bg_rgba = (0,0,0,0)
    elif bg_choice == "white":
        bg_mode = "white"; bg_rgba = (255,255,255,255)
    else:
        r,g,b = hex_to_rgb(bg_color_hex); a = int(round(bg_alpha_pct/100*255))
        bg_mode = "custom"; bg_rgba = (r,g,b,a)

    square_size = 0; no_upscale = True
    if square:
        sq_mode = st.radio("Square mode", ["Auto (fit longest side)", "Custom size (px)"], horizontal=True)
        if sq_mode == "Custom size (px)":
            s1, s2 = st.columns([2, 1])
            square_size_val = s1.number_input("Square size (px)", 32, 8192, 512)
            no_upscale = s2.checkbox("Do not upscale", True)
            square_size = int(square_size_val)
    st.markdown('</div>', unsafe_allow_html=True)

    # Brightness
    st.subheader("✨ Brightness")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    brightness = st.slider("Brightness factor", 0.2, 2.5, 1.0, 0.05)
    st.markdown('</div>', unsafe_allow_html=True)

    # Resize (auto-disabled if square)
    st.subheader("📐 Resize")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    square_blocks_resize = square  # in do_all, Square controls Resize
    r_disabled = square_blocks_resize
    r1, r2, r3, r4 = st.columns(4)
    enable_resize = r1.checkbox("Enable", True, disabled=r_disabled)
    target_w = r2.number_input("Width (px)", 1, 8192, 512, disabled=(r_disabled or not enable_resize))
    target_h = r3.number_input("Height (px)", 1, 8192, 512, disabled=(r_disabled or not enable_resize))
    resize_mode = r4.selectbox("Mode", ["keep_aspect_pad","keep_aspect_crop","stretch"], disabled=(r_disabled or not enable_resize))
    if square_blocks_resize:
        enable_resize = False
        st.info("Square is ON → Resize disabled.")
    st.markdown('</div>', unsafe_allow_html=True)

# ===== Tabs =====
tabs = st.tabs(["🖼️ Preview", "📜 Run Log", "⚠️ Errors"])
first_pair = {"src": None, "dst": None}

with tabs[0]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if "chosen_input_dir" in st.session_state:
        input_dir = Path(st.session_state["chosen_input_dir"])
        imgs = list_images(input_dir)
        st.caption(f"Found **{len(imgs)}** image(s) in `{input_dir}`.")
        if imgs:
            cols = st.columns(min(4, len(imgs[:8])))
            for i, p in enumerate(imgs[:8]):
                try:
                    with Image.open(p) as im:
                        cols[i % len(cols)].image(im, caption=str(p.relative_to(input_dir)), use_container_width=True)
                except Exception:
                    cols[i % len(cols)].warning(f"Preview failed: {p.name}")
    else:
        st.info("Choose an input folder (or upload ZIP) to see previews.")
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    run_log = st.empty()
with tabs[2]:
    err_box = st.container()

st.markdown('<hr class="divider"/>', unsafe_allow_html=True)
go = st.button("🚀 Run Processing", type="primary", use_container_width=True)

if go:
    # Resolve input
    cleanup_dirs = []
    if "chosen_input_dir" in st.session_state:
        in_root = Path(st.session_state["chosen_input_dir"])
    else:
        zip_bytes = st.session_state.get("uploaded_zip")
        if not zip_bytes:
            st.error("Please select an input folder or upload a ZIP before running.")
            st.stop()
        in_root = unzip_to_temp(io.BytesIO(zip_bytes))
        cleanup_dirs.append(in_root)

    # Resolve output
    if "chosen_output_dir" in st.session_state and st.session_state["chosen_output_dir"]:
        out_root = Path(st.session_state["chosen_output_dir"])
        out_mode = "folder"
    else:
        out_root = Path(tempfile.mkdtemp(prefix="processed_out_"))
        cleanup_dirs.append(out_root)
        out_mode = "zip"

    images = list_images(in_root)
    if not images:
        st.warning("No supported images found (jpg, jpeg, png, webp, bmp, tiff).")
        for d in cleanup_dirs:
            shutil.rmtree(d, ignore_errors=True)
        st.stop()

    # KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Images", len(images))
    k2.metric("Operation", operation.split(" (")[0])
    k3.metric("Output", "ZIP" if out_mode == "zip" else "Folder")

    progress = st.progress(0)
    successes, failures = 0, []
    run_log.write("Starting…")

    for idx, img_path in enumerate(images, start=1):
        _, outp, ok, err = process_one(
            img_path, in_root, out_root,
            operation=op_map[operation],
            bg_mode=bg_mode,
            bg_rgba=bg_rgba,
            pad=pad,
            square=square if (operation_key in ("bg_only","do_all")) else False,
            square_size=(int(square_size) if ((operation_key in ("bg_only","do_all")) and square and square_size > 0) else None),
            no_upscale=(no_upscale if ((operation_key in ("bg_only","do_all")) and square) else True),
            brightness=(brightness if (operation_key in ("brightness_only","do_all")) else 1.0),
            enable_resize=(enable_resize if (operation_key in ("resize_only","do_all")) else False),
            target_w=(target_w if (operation_key in ("resize_only","do_all")) else 0),
            target_h=(target_h if (operation_key in ("resize_only","do_all")) else 0),
            resize_mode=(resize_mode if (operation_key in ("resize_only","do_all")) else "keep_aspect_pad"),
        )
        if ok:
            successes += 1
            if first_pair["src"] is None and first_pair["dst"] is None:
                dst_guess = outp if outp.exists() else (outp.with_suffix(".png"))
                first_pair["src"] = str(img_path)
                first_pair["dst"] = str(dst_guess)
        else:
            failures.append((img_path, err))
            with tabs[2]:
                err_box.error(f"{img_path.name}: {err}")

        progress.progress(idx / len(images))
        run_log.write(f"Processed {idx}/{len(images)}")

    st.success(f"Finished ✓ {successes} succeeded, {len(failures)} failed.")

    # Before/After for first image
    if first_pair["src"] and first_pair["dst"]:
        st.subheader("Before / After")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        try:
            if HAS_COMPARISON:
                image_comparison(
                    img1=first_pair["src"],
                    img2=first_pair["dst"],
                    label1="Original",
                    label2="Processed",
                    show_labels=True,
                    make_responsive=True,
                )
            else:
                c1, c2 = st.columns(2)
                c1.image(first_pair["src"], caption="Original", use_container_width=True)
                c2.image(first_pair["dst"], caption="Processed", use_container_width=True)
        except Exception:
            pass
        st.markdown('</div>', unsafe_allow_html=True)

    # ZIP download if needed
    if out_mode == "zip":
        zip_bytes = zip_dir_to_bytes(out_root)
        st.download_button("⬇️ Download processed dataset (ZIP)",
                           data=zip_bytes, file_name="processed_dataset.zip",
                           mime="application/zip", use_container_width=True)

    for d in cleanup_dirs:
        shutil.rmtree(d, ignore_errors=True)

    # Footer
    YEAR = datetime.now().year
    st.markdown(
        f"""
        <style>
        .block-container {{ padding-bottom: 4.5rem !important; }}
        .custom-footer {{
            position: fixed; left: 0; right: 0; bottom: 0;
            width: 100%;
            text-align: center;
            padding: 10px 8px;
            font-size: 0.9rem;
            background: color-mix(in srgb, var(--accent) 8%, transparent);
            backdrop-filter: blur(8px);
            border-top: 1px solid rgba(0,0,0,.08);
            z-index: 9999;
            color: rgba(0,0,0,0.78);
        }}
        [data-theme="dark"] .custom-footer {{
            border-top: 1px solid rgba(255,255,255,.12);
            color: rgba(255,255,255,0.88);
        }}
        </style>
        <div class="custom-footer">© {YEAR} Developed by <strong>Md. Mehedi Hasan Shoib</strong></div>
        """,
        unsafe_allow_html=True,

    )
