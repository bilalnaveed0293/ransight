"""
Nataraj (2011) binary-to-grayscale-image visualisation.

Reference:
  Nataraj, L., Karthikeyan, S., Jacob, G., & Manjunath, B. S. (2011).
  "Malware images: visualization and automatic classification."
  Proceedings of the 8th International Symposium on Visualization for
  Cyber Security (VizSec '11).

The raw bytes of a PE (.exe) file are read as unsigned 8-bit integers,
reshaped into a 2D grayscale image whose width is chosen from a lookup
table based on file size, then resized to the dimensions expected by the
CNN model.
"""

import numpy as np
from PIL import Image

# Nataraj (2011) width lookup — file-size range → image width
_NATARAJ_WIDTH_TABLE = [
    (10 * 1024,        32),
    (30 * 1024,        64),
    (60 * 1024,       128),
    (100 * 1024,      256),
    (200 * 1024,      384),
    (500 * 1024,      512),
    (1000 * 1024,     768),
    (float("inf"),   1024),
]

# Target size the model expects (height, width)
MODEL_IMAGE_SIZE = (128, 128)


def _nataraj_width(file_size: int) -> int:
    """Return the image width for a given file size per Nataraj (2011)."""
    for threshold, width in _NATARAJ_WIDTH_TABLE:
        if file_size < threshold:
            return width
    return 1024


def extract_features(file_path: str) -> np.ndarray:
    """
    Convert a PE binary to a grayscale image using the Nataraj method,
    resize it to MODEL_IMAGE_SIZE, normalise to [0, 1], and return a
    numpy array shaped (H, W, 1) ready for the Keras model.
    """
    with open(file_path, "rb") as f:
        byte_data = f.read()

    byte_array = np.frombuffer(byte_data, dtype=np.uint8)

    # Determine width from Nataraj file-size table
    width = _nataraj_width(len(byte_array))
    height = int(np.ceil(len(byte_array) / width))

    # Zero-pad so the array fills the full rectangle
    padded = np.pad(byte_array, (0, width * height - len(byte_array)))
    image = padded.reshape((height, width))

    # Resize to the model's expected input dimensions
    img = Image.fromarray(image, mode="L")
    img = img.resize(MODEL_IMAGE_SIZE, Image.BILINEAR)

    # Normalise to [0, 1] and add channel dimension
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = arr.reshape(*MODEL_IMAGE_SIZE, 1)

    return arr