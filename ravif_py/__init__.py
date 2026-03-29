import io
import os
from pathlib import Path

import numpy as np
from PIL import Image


from ._ravif_py import (
    encode_rgba,
    encode_rgba16,
    ColorModel,
    AlphaColorMode,
    BitDepth
)

InputType = str | bytes | Path | os.PathLike[str] | os.PathLike[bytes] | io.BytesIO | Image.Image | np.ndarray


def encode_file(
        input_source: InputType,
        quality: float = 80.0,
        alpha_quality: float | None = None,
        speed: int = 4,
        color_model: ColorModel = ColorModel.YCbCr,
        alpha_mode: AlphaColorMode = AlphaColorMode.UnassociatedClean,
        bit_depth: BitDepth = BitDepth.Auto,
        threads: int = 0,
        exif: bytes | None = None
) -> bytes:
    """
    Encodes an image from various sources into AVIF format.

    A universal function that accepts file paths, byte objects, `PIL.Image`
    instances, or `numpy.ndarray` arrays as a source. For `numpy.ndarray`
    arrays, both 8-bit and 16-bit color depths are supported.

    Args:
        input_source (InputType): Image source. Can be a file path (str, Path),
            a byte object (bytes, io.BytesIO), a `PIL.Image` instance, or
            a `numpy.ndarray` array.
        quality (float, optional): Compression quality from 1 to 100.
            Default is 80.0.
        alpha_quality (float | None, optional): Separate quality for the
            alpha channel. If `None`, the `quality` value is used.
            Default is `None`.
        speed (int, optional): Encoding speed (from 1 to 10), where 1 is
            best quality and 10 is fastest speed. Default is 4.
        color_model (ColorModel, optional): Color model for encoding.
            Default is `ColorModel.YCbCr`.
        alpha_mode (AlphaColorMode, optional): Alpha channel processing mode.
            Default is `AlphaColorMode.UnassociatedClean`.
        bit_depth (BitDepth, optional): Color depth of the output image.
            Default is `BitDepth.Auto`.
        threads (int, optional): Number of threads for encoding. 0 means
            automatic detection. Default is 0.
        exif (bytes | None, optional): Byte object with EXIF metadata to
            embed in the file. Default is `None`.

    Note:
        When processed via `PIL.Image` (i.e., for all types except
        `numpy.ndarray`), 16-bit images will be converted to 8-bit.

    Returns:
        bytes: A byte object containing the encoded AVIF file data.

    Raises:
        TypeError: If `input_source` has an unsupported type.
        IOError: In case of an error reading the source file.
    """

    # 1. If a Numpy array was passed (e.g., from OpenCV or Diffusers)
    if isinstance(input_source, np.ndarray):
        height, width = input_source.shape[:2]

        # If the array is 16-bit
        if input_source.dtype == np.uint16:
            # Ensure there is an alpha channel
            if input_source.shape[2] == 3:
                input_source = np.dstack((input_source, np.full((height, width), 65535, dtype=np.uint16)))

            return encode_rgba16(
                input_source, width, height,
                quality, alpha_quality, speed,
                color_model, alpha_mode, threads, exif
            )['avif']

        # If the array is 8-bit
        else:
            if input_source.dtype != np.uint8:
                input_source = input_source.astype(np.uint8)
            if input_source.shape[2] == 3:
                input_source = np.dstack((input_source, np.full((height, width), 255, dtype=np.uint8)))

            return encode_rgba(
                input_source.tobytes(), width, height,
                quality, alpha_quality, speed,
                color_model, alpha_mode, bit_depth, threads, exif
            )['avif']

    # 2. General processing (Paths, Files, Bytes, Pillow)
    is_path_or_bytes = isinstance(input_source, (str, bytes, Path, os.PathLike, io.BytesIO))

    if isinstance(input_source, bytes):
        img = Image.open(io.BytesIO(input_source))
    elif is_path_or_bytes:
        img = Image.open(input_source)
    elif isinstance(input_source, Image.Image):
        img = input_source
    else:
        raise TypeError("Неподдерживаемый тип входных данных. Ожидается: Path, str, bytes, BytesIO, Image.Image или numpy.ndarray")

    try:
        # Note: Pillow converts 16-bit to 8-bit when calling convert("RGBA").
        # Therefore, everything processed via Pillow will be treated as 8-bit.
        img_rgba = img.convert("RGBA")

        res = encode_rgba(
            img_rgba.tobytes(), img.width, img.height,
            quality, alpha_quality, speed,
            color_model, alpha_mode, bit_depth, threads, exif
        )
        return res['avif']
    finally:
        if is_path_or_bytes:
            img.close()


__all__ = ["encode_file", "encode_rgba", "encode_rgba16", "ColorModel", "AlphaColorMode", "BitDepth"]
