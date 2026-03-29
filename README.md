# ravif-py

A high-performance AVIF image encoder for Python, powered by the Rust [ravif](https://github.com/kornelski/cavif-rs/tree/main/ravif) library and [rav1e](https://github.com/xiph/rav1e).

`ravif-py` provides a simple, "batteries-included" interface for converting images to AVIF. It supports 8-bit and 16-bit (HDR) color depths, seamless integration with **NumPy** and **Pillow**, and advanced control over compression, speed, and metadata.

It is built using [PyO3](https://github.com/PyO3/pyo3) and [Maturin](https://github.com/PyO3/maturin).

## Features

- ♾️ **Universal Input**: Supports file paths, bytes, `PIL.Image`, and `numpy.ndarray`.
- 📸 **HDR Support**: Native encoding of 16-bit images (scaled to 10-bit AVIF).
- 🚀 **Fast**: Multi-threaded encoding using Rust's safety and speed.
- ✨ **Optimized**: Supports "Clean Alpha" mode which removes invisible color data under transparent pixels to significantly reduce file size.
- 🏷️ **Metadata**: Support for embedding EXIF data.

## Installation

```bash
uv add ravif-py
```

or

```bash
pip install ravif-py
```

## Quick Start

The easiest way to use the library is the `encode_file` function, which automatically handles different input types.

```python
from ravif_py import encode_file

# Encode from a file path
avif_data = encode_file("input.png", quality=85, speed=4)

# Save the result
with open("output.avif", "wb") as f:
    f.write(avif_data)
```

---

## Detailed Usage Examples

### 1. Working with Pillow (PIL)
`ravif-py` integrates perfectly with Pillow for pre-processing.

```python
from PIL import Image
from ravif_py import encode_file

img = Image.open("photo.jpg")
# Perform crops, resizing, etc.
img = img.resize((800, 600))

# Encode PIL object directly
avif_bytes = encode_file(img, quality=70)
```

### 2. NumPy Integration (8-bit and 16-bit HDR)
Useful for computer vision (OpenCV) or AI generation (Diffusers).

```python
import numpy as np
from ravif_py import encode_file

# Example: 8-bit RGB array (0-255)
data_8bit = np.zeros((1024, 1024, 3), dtype=np.uint8)
avif_8bit = encode_file(data_8bit)

# Example: 16-bit HDR array (0-65535)
# ravif-py will automatically encode this as a 10-bit AVIF
data_16bit = np.random.randint(0, 65535, (1024, 1024, 3), dtype=np.uint16)
avif_hdr = encode_file(data_16bit)
```

### 3. Advanced Configuration
You can fine-tune the encoder using enums for color models and alpha processing.

```python
from ravif_py import encode_file, ColorModel, AlphaColorMode, BitDepth

avif_data = encode_file(
    "input.png",
    quality=90.0,
    alpha_quality=80.0,      # Different quality for transparency
    speed=3,                  # 1 (slowest/best) to 10 (fastest)
    color_model=ColorModel.YCbCr,
    alpha_mode=AlphaColorMode.UnassociatedClean, # Reduces size for transparent images
    bit_depth=BitDepth.Ten,   # Force 10-bit output for smoother gradients
    threads=4                 # 0 for auto-detection
)
```

### 4. Preserving Metadata (EXIF)
You can pass raw EXIF bytes to be embedded in the output file.

```python
from PIL import Image
from ravif_py import encode_file

img = Image.open("input_with_exif.jpg")
exif_data = img.info.get("exif")

avif_data = encode_file(img, exif=exif_data)
```

---

## API Reference

### `encode_file(...)`
The primary high-level function.

| Argument | Type | Description |
| :--- | :--- | :--- |
| `input_source` | `Path`, `str`, `bytes`, `Image`, `ndarray` | The source image. |
| `quality` | `float` | Main image quality (1-100). Default: `80.0`. |
| `alpha_quality` | `float \| None` | Quality for alpha channel. Defaults to `quality`. |
| `speed` | `int` | Encoding speed (1-10). Default: `4`. |
| `color_model` | `ColorModel` | `YCbCr` (standard) or `RGB`. |
| `alpha_mode` | `AlphaColorMode` | How to treat transparent pixels. |
| `bit_depth` | `BitDepth` | `Eight`, `Ten`, or `Auto`. |
| `threads` | `int` | Number of CPU threads. `0` for all available. |
| `exif` | `bytes \| None` | Raw EXIF metadata to embed. |

### Enums

#### `ColorModel`
- `YCbCr`: Optimized for human vision (smaller files). Recommended for photos.
- `RGB`: Direct color encoding. High quality but significantly larger files.

#### `AlphaColorMode`
- `UnassociatedClean`: **Recommended.** Fills transparent areas with a solid color to maximize compression.
- `UnassociatedDirty`: Keeps original color data even in fully transparent pixels.
- `Premultiplied`: Uses premultiplied alpha.

#### `BitDepth`
- `Eight`: Standard 8-bit compatibility.
- `Ten`: 10-bit depth. Better for gradients (prevents banding).
- `Auto`: Automatically chooses (usually selects 10-bit for higher quality).

---

## Low-level Functions
If you have raw pixel buffers, you can use the core Rust wrappers directly:
- `encode_rgba(pixels: bytes, width: int, height: int, ...)`: For 8-bit raw RGBA.
    ```python
    import ravif_py
    from PIL import Image
    
    img = Image.open("input.png").convert("RGBA")
    width, height = img.size
    result = ravif_py.encode_rgba(
        img.tobytes(), 
        width, 
        height, 
        quality=70.0, 
        speed=5
    )
    
    with open("output.avif", "wb") as f:
        f.write(result['avif'])
    
    print(f"Compressed to {len(result['avif']) / 1024:.1f} KB")
    ```

- `encode_rgba16(pixels: Buffer, width: int, height: int, ...)`: For 16-bit raw RGBA.
    ```python
    import numpy as np
    import ravif_py
    
    data_16bit = np.random.randint(0, 65535, (1024, 1024, 4), dtype=np.uint16)
    
    result = ravif_py.encode_rgba16(
        data_16bit, 
        1024, 1024, 
        quality=85.0,
    )
    ```

## License
This project is licensed under the same terms as the `ravif` library (BSD-3-Clause license).