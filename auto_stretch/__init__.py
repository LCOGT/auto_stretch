from importlib.metadata import PackageNotFoundError, version

from .stretch import Stretch, apply_stretch

try:
    __version__ = version("auto-stretch")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = ["Stretch", "apply_stretch", "__version__"]
