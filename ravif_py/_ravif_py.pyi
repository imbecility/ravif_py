from collections.abc import Buffer
from enum import IntEnum
from typing import TypedDict

class ColorModel(IntEnum):
    """
    Internal color model for AVIF encoding.

    - YCbCr - standard for video and photos. Better compression, optimized for human vision.
    - RGB - direct RGB encoding. Larger file size, used for specialized tasks.
    """
    YCbCr = 0
    RGB = 1

class AlphaColorMode(IntEnum):
    """
    Transparency (Alpha channel) processing mode.

    - UnassociatedDirty - keep hidden colors of transparent pixels as is.
    - UnassociatedClean - (recommended) clear hidden colors under transparency, significantly reduces file size without loss of quality.
    - Premultiplied - use premultiplied alpha channel.
    """
    UnassociatedDirty = 0
    UnassociatedClean = 1
    Premultiplied = 2

class BitDepth(IntEnum):
    """
    Color depth of the output file.

    - Eight - 8 bits per channel. Maximum compatibility.
    - Ten -  10 bits per channel. Better quality, less banding on gradients.
    - Auto - automatic selection (usually 10 bits for better quality).
    """
    Eight = 0
    Ten = 1
    Auto = 2

class EncodeResult(TypedDict):
    """
    Encoding result.

    - avif - binary data of the resulting .avif file.
    - color_size - bytes used by color data (AV1 payload).
    - alpha_size - bytes used by alpha channel data.
    """
    avif: bytes
    color_size: int
    alpha_size: int

def encode_rgba(
    pixels: bytes,
    width: int,
    height: int,
    quality: float = 80.0,
    alpha_quality: float | None = None,
    speed: int = 4,
    color_model: ColorModel = ColorModel.YCbCr,
    alpha_mode: AlphaColorMode = AlphaColorMode.UnassociatedClean,
    bit_depth: BitDepth = BitDepth.Auto,
    threads: int = 0,
    exif: bytes | None = None
) -> EncodeResult:
    """
    Encodes raw 8-bit RGBA pixels into AVIF format.

    Args:
        pixels (bytes): Byte string of pixels in [R, G, B, A, R, G, B, A...] format.
                        Length must be exactly width * height * 4.
        width (int): Image width in pixels.
        height (int): Image height in pixels.
        quality (float): Color quality from 1.0 (worst) to 100.0 (best). Default is 80.0.
        alpha_quality (Optional[float]): Alpha channel quality. If None, calculated automatically based on `quality`.
        speed (int): Encoding speed from 1 (slow, best size) to 10 (fast, worse compression).
                     Recommended values: 4-6 for balance.
        color_model (ColorModel): Internal color model (YCbCr or RGB).
        alpha_mode (AlphaColorMode): Dirty alpha processing method. "Clean" helps significantly compress files with transparency.
        bit_depth (BitDepth): Color depth in the resulting file. 10-bit provides better quality even for 8-bit sources.
        threads (int): Number of threads. 0 — use all available CPU cores.
        exif (Optional[bytes]): Raw EXIF metadata bytes (e.g., generation parameters from ComfyUI).

    Returns:
        EncodeResult: Dictionary containing AVIF bytes and size statistics.

    Raises:
        ValueError: If the pixel buffer size does not match width * height * 4.
        RuntimeError: If an internal rav1e encoder error occurred.
    """
    ...

def encode_rgba16(
    pixels: Buffer,
    width: int,
    height: int,
    quality: float = 80.0,
    alpha_quality: float | None = None,
    speed: int = 4,
    color_model: ColorModel = ColorModel.YCbCr,
    alpha_mode: AlphaColorMode = AlphaColorMode.UnassociatedClean,
    threads: int = 0,
    exif: bytes | None = None
) -> EncodeResult:
    """
    Encodes 16-bit RGBA pixels into AVIF format (HDR support).

    Internally, data will be scaled to 10 bits, as this is the standard for HDR AVIF.

    Args:
        pixels (Buffer): Any list or array (numpy.uint16) of pixels (numpy.ndarray, array.array, memoryview, etc.).
        width (int): Width.
        height (int): Height.
        quality (float): Image quality.
        alpha_quality (Optional[float]): Transparency quality.
        speed (int): Speed (1-10).
        color_model (ColorModel): Color model.
        alpha_mode (AlphaColorMode): Transparency processing.
        threads (int): Number of threads.
        exif (Optional[bytes]): EXIF metadata.

    Returns:
        EncodeResult: Encoding result.

    Note:
        To pass data from numpy, use `arr.flatten().tolist()`.
    """
    ...