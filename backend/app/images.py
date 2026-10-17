import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

# Clients resize the long edge to 1024 px before upload. A 1024x768 JPEG is at most
# about 1.3 MiB even at quality 100 on pure noise, so 2 MiB leaves room for metadata.
MAX_BYTES = 2 * 1024 * 1024
MAX_LONG_EDGE = 1024

CONTENT_TYPE = "image/jpeg"
EXTENSION = "jpg"

# EXIF orientations 5-8 rotate by 90 degrees, swapping displayed width and height.
_SWAPPING_ORIENTATIONS = {5, 6, 7, 8}


class InvalidImage(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


@dataclass(frozen=True)
class ImageInfo:
    width: int
    height: int
    content_type: str = CONTENT_TYPE
    extension: str = EXTENSION


def inspect_image(data: bytes) -> ImageInfo:
    """Decode the photo and apply the upload rules from design.md."""
    try:
        image = Image.open(io.BytesIO(data))
    except UnidentifiedImageError:
        raise InvalidImage(415, "Only JPEG photos are supported")
    except Image.DecompressionBombError:
        raise InvalidImage(422, f"Photo long edge must be at most {MAX_LONG_EDGE} px")
    except OSError:
        # Recognised format, but the header or first bytes are damaged (e.g. truncated upload).
        raise InvalidImage(422, "Image data is corrupt")

    with image:
        # Multi-picture JPEGs (MPO) report a different format and are rejected here too.
        if image.format != "JPEG":
            raise InvalidImage(415, "Only JPEG photos are supported")
        width, height = image.size
        # Checked before decoding so an oversized header cannot exhaust memory.
        if max(width, height) > MAX_LONG_EDGE:
            raise InvalidImage(422, f"Photo long edge must be at most {MAX_LONG_EDGE} px")
        try:
            image.load()
            orientation = image.getexif().get(0x0112)
        except (OSError, SyntaxError):
            raise InvalidImage(422, "Image data is corrupt")
        if orientation in _SWAPPING_ORIENTATIONS:
            width, height = height, width

    if not (_matches_ratio(width, height, 3, 4) or _matches_ratio(width, height, 4, 3)):
        raise InvalidImage(422, "Photo must be 3:4 or 4:3")
    return ImageInfo(width, height)


def _matches_ratio(width: int, height: int, ratio_w: int, ratio_h: int) -> bool:
    return abs(height - width * ratio_h / ratio_w) <= 1
