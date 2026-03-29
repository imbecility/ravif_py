use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use pyo3::buffer::PyBuffer;
use ravif::{Encoder, ColorModel, AlphaColorMode, BitDepth, Img, MatrixCoefficients, PixelRange};
use rgb::FromSlice;

#[pyclass(name = "ColorModel")]
#[derive(Clone, Copy)]
pub enum PyColorModel {
    YCbCr,
    RGB,
}

#[pyclass(name = "AlphaColorMode")]
#[derive(Clone, Copy)]
pub enum PyAlphaColorMode {
    UnassociatedDirty,
    UnassociatedClean,
    Premultiplied,
}

#[pyclass(name = "BitDepth")]
#[derive(Clone, Copy)]
pub enum PyBitDepth {
    Eight,
    Ten,
    Auto,
}

/// Helper function for creating an encoder
fn create_encoder<'a>(
    quality: f32,
    aq: Option<f32>,
    speed: u8,
    cm: PyColorModel,
    am: PyAlphaColorMode,
    bd: PyBitDepth,
    threads: usize,
    exif: Option<&'a [u8]>,
) -> Encoder<'a> {
    let mut enc = Encoder::new()
        .with_quality(quality)
        .with_speed(speed)
        .with_internal_color_model(match cm {
            PyColorModel::YCbCr => ColorModel::YCbCr,
            PyColorModel::RGB => ColorModel::RGB,
        })
        .with_alpha_color_mode(match am {
            PyAlphaColorMode::UnassociatedDirty => AlphaColorMode::UnassociatedDirty,
            PyAlphaColorMode::UnassociatedClean => AlphaColorMode::UnassociatedClean,
            PyAlphaColorMode::Premultiplied => AlphaColorMode::Premultiplied,
        })
        .with_bit_depth(match bd {
            PyBitDepth::Eight => BitDepth::Eight,
            PyBitDepth::Ten => BitDepth::Ten,
            PyBitDepth::Auto => BitDepth::Auto,
        });

    if let Some(q) = aq {
        enc = enc.with_alpha_quality(q);
    }
    if threads > 0 {
        enc = enc.with_num_threads(Some(threads));
    }
    if let Some(data) = exif {
        enc = enc.with_exif(data);
    }
    enc
}

/// Helper function for formatting a dictionary with results
fn format_result(py: Python<'_>, avif: Vec<u8>, c_size: usize, a_size: usize) -> PyResult<Py<PyAny>> {
    let dict = PyDict::new(py);
    dict.set_item("avif", PyBytes::new(py, &avif))?;
    dict.set_item("color_size", c_size)?;
    dict.set_item("alpha_size", a_size)?;
    Ok(dict.into())
}

#[pyfunction]
#[pyo3(signature = (
    pixels, width, height,
    quality=80.0, alpha_quality=None, speed=4,
    color_model=PyColorModel::YCbCr,
    alpha_mode=PyAlphaColorMode::UnassociatedClean,
    bit_depth=PyBitDepth::Auto,
    threads=0,
    exif=None
))]
#[allow(clippy::too_many_arguments)]
fn encode_rgba(
    py: Python<'_>,
    pixels: &[u8],
    width: usize,
    height: usize,
    quality: f32,
    alpha_quality: Option<f32>,
    speed: u8,
    color_model: PyColorModel,
    alpha_mode: PyAlphaColorMode,
    bit_depth: PyBitDepth,
    threads: usize,
    exif: Option<&[u8]>,
) -> PyResult<Py<PyAny>> {
    if pixels.len() != width * height * 4 {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Buffer size mismatch for RGBA8: expected {}, got {}", width * height * 4, pixels.len()
        )));
    }

    let img = Img::new(pixels.as_rgba(), width, height);
    let encoder = create_encoder(quality, alpha_quality, speed, color_model, alpha_mode, bit_depth, threads, exif);

    match encoder.encode_rgba(img) {
        Ok(res) => format_result(py, res.avif_file, res.color_byte_size, res.alpha_byte_size),
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
    }
}

#[pyfunction]
#[pyo3(signature = (
    pixels, width, height,
    quality=80.0, alpha_quality=None, speed=4,
    color_model=PyColorModel::YCbCr,
    alpha_mode=PyAlphaColorMode::UnassociatedClean,
    threads=0,
    exif=None
))]
#[allow(clippy::too_many_arguments)]
fn encode_rgba16(
    py: Python<'_>,
    pixels: Bound<'_, PyAny>,
    width: usize,
    height: usize,
    quality: f32,
    alpha_quality: Option<f32>,
    speed: u8,
    color_model: PyColorModel,
    alpha_mode: PyAlphaColorMode,
    threads: usize,
    exif: Option<&[u8]>,
) -> PyResult<Py<PyAny>> {
    // 1. Getting access to the buffer (numpy, array.array, etc.)
    let buffer = PyBuffer::<u16>::get(&pixels)?;

    // 2. Getting a slice from ReadOnlyCell<u16>
    let slice = buffer.as_slice(py).ok_or_else(|| {
        pyo3::exceptions::PyBufferError::new_err("Buffer is not contiguous or has wrong alignment")
    })?;

    if slice.len() != width * height * 4 {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Buffer size mismatch for RGBA16: expected {}, got {}", width * height * 4, slice.len()
        )));
    }

    let encoder = create_encoder(quality, alpha_quality, speed, color_model, alpha_mode, PyBitDepth::Ten, threads, exif);
    let matrix = match color_model {
        PyColorModel::YCbCr => MatrixCoefficients::BT601,
        PyColorModel::RGB => MatrixCoefficients::Identity,
    };

    // 3. Pixel Processing: 16-bit -> 10-bit (6-bit right shift)
    let chunks = slice.chunks_exact(4);
    let planes: Vec<[u16; 3]> = chunks.clone()
        .map(|px| [
            px[0].get() >> 6,
            px[1].get() >> 6,
            px[2].get() >> 6
        ])
        .collect();

    let alpha: Vec<u16> = chunks
        .map(|px| px[3].get() >> 6)
        .collect();

    // 4. Encoding
    match encoder.encode_raw_planes_10_bit(width, height, planes, Some(alpha), PixelRange::Full, matrix) {
        Ok(res) => format_result(py, res.avif_file, res.color_byte_size, res.alpha_byte_size),
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
    }
}

#[pymodule]
fn _ravif_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyColorModel>()?;
    m.add_class::<PyAlphaColorMode>()?;
    m.add_class::<PyBitDepth>()?;
    m.add_function(wrap_pyfunction!(encode_rgba, m)?)?;
    m.add_function(wrap_pyfunction!(encode_rgba16, m)?)?;
    Ok(())
}