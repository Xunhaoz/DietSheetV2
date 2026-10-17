import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

MAX_BYTES = 15 * 1024 * 1024
MAX_PIXELS = 24_000_000

CONTENT_TYPES = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
EXTENSIONS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}

# EXIF orientations 5-8 rotate by 90 degrees, swapping displayed width and height.
_SWAPPING_ORIENTATIONS = {5, 6, 7, 8}


class InvalidImage(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


@dataclass(frozen=True)
class ImageInfo:
    format: str
    width: int
    height: int

    @property
    def content_type(self) -> str:
        return CONTENT_TYPES[self.format]

    @property
    def extension(self) -> str:
        return EXTENSIONS[self.format]


def inspect_image(data: bytes) -> ImageInfo:
    """Decode the photo and apply the upload rules from design.md."""
    try:
        image = Image.open(io.BytesIO(data))
    except UnidentifiedImageError:
        raise InvalidImage(415, "Unsupported image format")
    except Image.DecompressionBombError:
        raise InvalidImage(413, "Image exceeds 24 megapixels")
    except OSError:
        # Recognised format, but the header or first bytes are damaged (e.g. truncated upload).
        raise InvalidImage(422, "Image data is corrupt")

    with image:
        if image.format not in CONTENT_TYPES:
            raise InvalidImage(415, "Only JPEG, PNG and WebP are supported")
        if getattr(image, "n_frames", 1) > 1:
            raise InvalidImage(415, "Animated images are not supported")
        width, height = image.size
        if width * height > MAX_PIXELS:
            raise InvalidImage(413, "Image exceeds 24 megapixels")
        try:
            image.load()
            orientation = image.getexif().get(0x0112)
        except (OSError, SyntaxError):
            raise InvalidImage(422, "Image data is corrupt")
        if orientation in _SWAPPING_ORIENTATIONS:
            width, height = height, width

    if not (_matches_ratio(width, height, 3, 4) or _matches_ratio(width, height, 4, 3)):
        raise InvalidImage(422, "Photo must be 3:4 or 4:3")
    return ImageInfo(image.format, width, height)


def _matches_ratio(width: int, height: int, ratio_w: int, ratio_h: int) -> bool:
    return abs(height - width * ratio_h / ratio_w) <= 1
