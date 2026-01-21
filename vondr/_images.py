"""Image encoding utilities for Vondr AI Platform client.

This module requires the 'images' extra: pip install vondr[images]
"""

from __future__ import annotations

import base64
import os
from io import BytesIO
from pathlib import Path
from typing import Union

# PIL is an optional dependency
try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def encode_image(
    image: Union[str, bytes, Path],
    max_size_mb: float = 20.0,
    quality: int = 85,
) -> str:
    """Encode an image to a base64 data URI.

    Args:
        image: File path (str or Path) or raw image bytes.
        max_size_mb: Maximum size in MB. Images larger than this will be resized.
        quality: JPEG quality (1-100) for resizing. Defaults to 85.

    Returns:
        Data URI string (e.g., "data:image/jpeg;base64,...").

    Raises:
        ImportError: If Pillow is not installed and resizing is needed.
        FileNotFoundError: If the image file does not exist.
        ValueError: If the image data type is invalid.

    Example:
        from vondr import encode_image

        # From file path
        data_uri = encode_image("/path/to/image.jpg")

        # From bytes
        data_uri = encode_image(image_bytes)

        # Use in chat
        response = client.chat([
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            }
        ])
    """
    max_size_bytes = int(max_size_mb * 1024 * 1024)

    # Load image data
    if isinstance(image, (str, Path)):
        path = Path(image)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        image_size = path.stat().st_size
        with open(path, "rb") as f:
            image_bytes = f.read()

        # Detect MIME type from extension
        mime_type = _get_mime_type(path)
    elif isinstance(image, bytes):
        image_bytes = image
        image_size = len(image_bytes)
        mime_type = _detect_mime_type(image_bytes)
    else:
        raise ValueError(
            f"Invalid image type: {type(image)}. Expected str, Path, or bytes."
        )

    # Resize if necessary
    if image_size > max_size_bytes:
        if not PIL_AVAILABLE:
            raise ImportError(
                "Pillow is required for image resizing. "
                "Install it with: pip install vondr[images]"
            )

        image_bytes = _resize_image(image_bytes, max_size_bytes, quality)
        mime_type = "image/jpeg"  # Resized images are always JPEG

    # Encode to base64
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _get_mime_type(path: Path) -> str:
    """Get MIME type from file extension."""
    extension = path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    return mime_types.get(extension, "image/jpeg")


def _detect_mime_type(data: bytes) -> str:
    """Detect MIME type from image bytes."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    elif data[:2] == b"\xff\xd8":
        return "image/jpeg"
    elif data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    elif data[:2] == b"BM":
        return "image/bmp"
    else:
        return "image/jpeg"  # Default to JPEG


def _resize_image(
    image_bytes: bytes,
    max_size_bytes: int,
    quality: int,
) -> bytes:
    """Resize image to fit within max size."""
    if not PIL_AVAILABLE:
        raise ImportError(
            "Pillow is required for image resizing. "
            "Install it with: pip install vondr[images]"
        )

    with Image.open(BytesIO(image_bytes)) as img:
        # Convert to RGB if necessary (for PNG with alpha, etc.)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Calculate initial scale factor
        scale_factor = (max_size_bytes / len(image_bytes)) ** 0.5
        new_dimensions = (
            int(img.width * scale_factor),
            int(img.height * scale_factor),
        )

        # Resize
        img = img.resize(new_dimensions, Image.LANCZOS)

        # Save to buffer with initial quality
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality)

        # If still too large, reduce quality iteratively
        current_quality = quality
        while buffer.tell() > max_size_bytes and current_quality > 20:
            buffer = BytesIO()
            current_quality -= 10
            img.save(buffer, format="JPEG", quality=current_quality)

        return buffer.getvalue()
