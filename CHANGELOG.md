# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org).

## [0.1.0] — 2026-04-23

### Changed (breaking)

- MTF normalization now uses the canonical PixInsight STF form `(median - c0) / (1 - c0)`; numerical output differs slightly from 0.0.3 but better matches the reference algorithm.
- Non-2D inputs now raise `ValueError` instead of silently producing incorrect results. Multi-channel (3D/RGB) support is planned for a later release.

### Fixed

- Divide-by-zero when image max is zero; now returns a zero image.
- Integer-dtype silent truncation inside `_mtf`; inputs are now coerced to float64 at the boundary.
- NaN pixels now propagate through the stretch unchanged instead of being misclassified.
- Removed unused `astropy` import (was pulling in a heavy dependency that wasn't actually used).

### Added

- `Stretch` class is now re-exported at the top level: `from auto_stretch import Stretch, apply_stretch`.
- `__version__` attribute sourced from package metadata.
- Output is clamped to `[0, 1]`.
- Expanded test suite with fixtures, parametrized cases, and hypothesis property tests.
- GitHub Actions CI (test matrix on Python 3.10–3.13) and tag-triggered PyPI publish via OIDC Trusted Publishing.

### Removed

- Legacy `setup.py` (replaced by `pyproject.toml` + hatchling).

## [0.0.3]

Initial public release.
