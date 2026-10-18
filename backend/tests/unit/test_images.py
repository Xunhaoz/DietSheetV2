import random
import struct

import pytest
from PIL import Image

from app.images import MAX_LONG_EDGE, InvalidImage, inspect_image
from tests.support import encode, make_jpeg


@pytest.mark.parametrize(("width", "height"), [(1024, 768), (768, 1024), (400, 300)])
def test_accepts_jpeg_within_long_edge_and_ratio(width: int, height: int) -> None:
    # Arrange
    photo = make_jpeg(width, height)

    # Act
    info = inspect_image(photo)

    # Assert
    assert (info.width, info.height, info.content_type) == (width, height, "image/jpeg")


@pytest.mark.parametrize("fmt", ["PNG", "WEBP", "GIF"])
def test_rejects_non_jpeg_formats_with_415(fmt: str) -> None:
    # Arrange
    photo = encode(Image.new("RGB", (1024, 768)), fmt)

    # Act
    with pytest.raises(InvalidImage) as raised:
        inspect_image(photo)

    # Assert
    assert raised.value.status_code == 415


def test_rejects_multi_picture_jpeg_with_415() -> None:
    # Arrange
    first, second = Image.new("RGB", (1024, 768)), Image.new("RGB", (1024, 768))
    photo = encode(first, "MPO", save_all=True, append_images=[second])

    # Act
    with pytest.raises(InvalidImage) as raised:
        inspect_image(photo)

    # Assert
    assert raised.value.status_code == 415


def test_rejects_non_image_bytes_with_415() -> None:
    # Arrange
    data = b"not an image"

    # Act
    with pytest.raises(InvalidImage) as raised:
        inspect_image(data)

    # Assert
    assert raised.value.status_code == 415


@pytest.mark.parametrize(("width", "height"), [(MAX_LONG_EDGE + 1, 769), (4032, 3024)])
def test_rejects_long_edge_over_limit_with_422(width: int, height: int) -> None:
    # Arrange
    photo = make_jpeg(width, height)

    # Act
    with pytest.raises(InvalidImage) as raised:
        inspect_image(photo)

    # Assert
    assert raised.value.status_code == 422
    assert "long edge" in raised.value.message


def test_rejects_ratio_other_than_3_4_or_4_3_with_422() -> None:
    # Arrange
    photo = make_jpeg(1024, 1024)

    # Act
    with pytest.raises(InvalidImage) as raised:
        inspect_image(photo)

    # Assert
    assert raised.value.message == "Photo must be 3:4 or 4:3"


def test_reports_dimensions_after_exif_rotation() -> None:
    # Arrange: stored landscape, tagged to display rotated by 90 degrees
    photo = make_jpeg(1024, 768, orientation=6)

    # Act
    info = inspect_image(photo)

    # Assert
    assert (info.width, info.height) == (768, 1024)


def test_rejects_forged_oversized_header_before_decoding() -> None:
    # Arrange: a tiny JPEG whose frame header claims 60000x45000
    photo = bytearray(make_jpeg(8, 6))
    frame = photo.find(b"\xff\xc0")
    struct.pack_into(">HH", photo, frame + 5, 45000, 60000)

    # Act
    with pytest.raises(InvalidImage) as raised:
        inspect_image(bytes(photo))

    # Assert
    assert raised.value.status_code == 422


def test_damaged_jpegs_only_ever_raise_invalid_image() -> None:
    # Arrange: truncations and byte flips, which once escaped as 500
    rng = random.Random(0)
    original = make_jpeg(1024, 768, orientation=6)
    samples = []
    for i in range(200):
        damaged = bytearray(original)
        if i % 2:
            damaged = damaged[: rng.randint(1, len(damaged) - 1)]
        else:
            for _ in range(rng.randint(1, 30)):
                damaged[rng.randrange(len(damaged))] = rng.randrange(256)
        samples.append(bytes(damaged))

    # Act
    unexpected = []
    for sample in samples:
        try:
            inspect_image(sample)
        except InvalidImage:
            pass
        except Exception as exc:
            unexpected.append(repr(exc))

    # Assert
    assert unexpected == []
