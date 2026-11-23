"""JPEG fixtures for the upload endpoint.

The three real images are checked-in files under ``tests/resources/images``; the invalid payloads are derived
from bytes, so no image library is needed.
"""
from functools import cache

from climanuvem.common import config

IMAGES_DIR = config.ROOT_DIR / "tests" / "resources" / "images"
MAX_IMAGE_BYTES = 5 * 1024 * 1024


@cache
def _load(name: str) -> bytes:
    return (IMAGES_DIR / name).read_bytes()


def tiny() -> bytes:
    """Minimal valid JPEG (10x10 grey square): small and fast, accepted by the upload endpoint."""
    return _load("tiny.jpg")


def cloudy() -> bytes:
    """640x360 blue sky with overlapping white/grey clouds."""
    return _load("cloudy.jpg")


def clear_sky() -> bytes:
    """640x360 clear vertical sky gradient, no clouds."""
    return _load("clear-sky.jpg")


def too_large() -> bytes:
    """A valid small JPEG followed by filler bytes, just past the 5 MB upload limit."""
    image = tiny()
    return image + bytes(MAX_IMAGE_BYTES + 1 - len(image))


def not_a_jpeg() -> bytes:
    """Bytes that are not a JPEG at all."""
    return b"not-a-jpeg-image"
