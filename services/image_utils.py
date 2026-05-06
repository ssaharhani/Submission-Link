"""
image_utils.py
--------------
Image pre-processing before upload.

Goal: keep uploads fast even on 4G by capping the image at a sensible
resolution and JPEG quality. The defaults below work well for handwritten
solutions photographed on a phone.

The teacher can adjust MAX_DIMENSION and JPEG_QUALITY if needed.
"""

import io
from PIL import Image

# ── Tunable constants ─────────────────────────────────────────────────────────

MAX_DIMENSION = 1600    # longest side in pixels (preserves readability)
JPEG_QUALITY = 82       # 75–85 is the sweet spot: sharp text, small file


# ── Public API ────────────────────────────────────────────────────────────────

def compress_image(raw_bytes: bytes) -> bytes:
    """
    Accept raw image bytes (any format the camera produces: JPEG, PNG, HEIC*).
    Return compressed JPEG bytes suitable for Drive upload.

    * HEIC requires the `pillow-heif` package; we silently fall back to the
      original bytes if an unsupported format is encountered.
    """
    try:
        img = Image.open(io.BytesIO(raw_bytes))

        # Normalise orientation from EXIF data (common on phone photos)
        img = _fix_orientation(img)

        # Convert palette / RGBA modes to plain RGB so JPEG encoder is happy
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Resize only if the image exceeds MAX_DIMENSION on either axis
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return output.getvalue()

    except Exception:
        # If compression fails for any reason, return the original bytes.
        # The upload will still work; it will just be larger.
        return raw_bytes


# ── Private helpers ───────────────────────────────────────────────────────────

def _fix_orientation(img: Image.Image) -> Image.Image:
    """Rotate image according to its EXIF orientation tag, if present."""
    try:
        from PIL import ExifTags
        exif = img._getexif()
        if exif is None:
            return img
        orientation_key = next(
            k for k, v in ExifTags.TAGS.items() if v == "Orientation"
        )
        orientation = exif.get(orientation_key)
        rotations = {3: 180, 6: 270, 8: 90}
        if orientation in rotations:
            img = img.rotate(rotations[orientation], expand=True)
    except Exception:
        pass  # EXIF not available — just return unchanged
    return img
