"""
vondr package exports.
"""

from importlib import metadata as importlib_metadata

from .core import greet

__all__ = ["greet"]


def _load_version() -> str:
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:
        return "0.0.0"


__version__ = _load_version()

