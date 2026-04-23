import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays as np_arrays

from auto_stretch import apply_stretch, stretch


@pytest.fixture
def simple_image():
    return np.array([[1, 2], [3, 1]], dtype=np.float64)


@pytest.fixture
def expected_stretch_simple():
    """Golden-value reference computed step-by-step for [[1,2],[3,1]].

    Uses the canonical (median - c0) / (1 - c0) formula matching the fixed algorithm.
    """
    d = np.array([[1 / 3, 2 / 3], [1.0, 1 / 3]], dtype=np.float64)  # after /nanmax
    flat = d.flatten()
    median = np.median(flat)               # 0.5
    avg_dev = np.mean(np.abs(flat - median))  # 0.25
    c0 = np.clip(median + (-1.25 * avg_dev), 0, 1)  # 0.1875
    m = _mtf_reference(0.25, (median - c0) / (1 - c0))

    below = d < c0
    above = d >= c0
    d[below] = 0
    d[above] = _mtf_reference(m, (d[above] - c0) / (1 - c0))
    np.clip(d, 0.0, 1.0, out=d)
    return d


def _mtf_reference(m, x):
    """Midtones Transfer Function – pure function for golden-value computation.

    Matches the fixed _mtf: no flatten/reshape, explicit NaN mask.
    """
    x = np.asarray(x, dtype=np.float64).copy()
    zeros = x == 0
    halfs = x == m
    ones = x == 1
    nans = np.isnan(x)
    others = ~(zeros | halfs | ones | nans)
    x[zeros] = 0
    x[halfs] = 0.5
    x[ones] = 1
    x[others] = (m - 1) * x[others] / (((2 * m - 1) * x[others]) - m)
    return x


# ── Shape & value correctness ──────────────────────────────────────────

def test_stretch_preserves_shape(simple_image):
    s = stretch.Stretch()
    result = s.stretch(simple_image)
    assert result.shape == simple_image.shape


def test_stretch_values_are_correct(simple_image, expected_stretch_simple):
    s = stretch.Stretch()
    result = s.stretch(simple_image)
    assert np.allclose(result, expected_stretch_simple)


def test_standalone_function(simple_image, expected_stretch_simple):
    result = apply_stretch(simple_image)
    assert result.shape == simple_image.shape
    assert np.allclose(result, expected_stretch_simple)


# ── Edge cases ─────────────────────────────────────────────────────────

def test_all_zeros():
    image = np.zeros((4, 4), dtype=np.float64)
    s = stretch.Stretch()
    result = s.stretch(image)
    assert result.shape == image.shape
    assert np.allclose(result, 0.0)


def test_single_pixel():
    # A single pixel normalizes to 1.0; median == 1.0 so c0 clips the entire image.
    image = np.array([[42.0]])
    s = stretch.Stretch()
    result = s.stretch(image)
    assert result.shape == image.shape
    assert np.all(result >= 0.0) and np.all(result <= 1.0)


def test_float32_input():
    image = np.array([[1, 2], [3, 1]], dtype=np.float32)
    s = stretch.Stretch()
    result = s.stretch(image)
    assert result.dtype == np.float64
    assert result.shape == image.shape


def test_float64_input():
    image = np.array([[1, 2], [3, 1]], dtype=np.float64)
    s = stretch.Stretch()
    result = s.stretch(image)
    assert result.dtype == np.float64
    assert result.shape == image.shape


def test_nan_handling():
    image = np.array([[1.0, np.nan], [3.0, 1.0]], dtype=np.float64)
    s = stretch.Stretch()
    result = s.stretch(image)
    assert result.shape == image.shape
    assert np.isnan(result[0, 1])


def test_non_contiguous_array():
    full = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.float64)
    image = full[:, ::2]  # columns 0 and 2 → non-contiguous
    assert not image.flags.c_contiguous
    s = stretch.Stretch()
    result = s.stretch(image)
    assert result.shape == image.shape


def test_already_normalized_input():
    image = np.array([[0.25, 0.5], [0.75, 0.25]], dtype=np.float64)
    s = stretch.Stretch()
    result = s.stretch(image)
    assert result.shape == image.shape
    assert np.min(result) >= 0.0
    assert np.max(result) <= 1.0


def test_large_dynamic_range():
    image = np.array([[1.0, 2.0], [1e15, 1.0]], dtype=np.float64)
    s = stretch.Stretch()
    result = s.stretch(image)
    assert result.shape == image.shape
    assert np.all(result >= 0) and np.all(result <= 1)


# ── New guarantee tests ────────────────────────────────────────────────

def test_rejects_3d_input():
    image = np.ones((4, 4, 3), dtype=np.float64)
    with pytest.raises(ValueError):
        apply_stretch(image)


def test_rejects_1d_input():
    image = np.array([0.1, 0.5, 0.9], dtype=np.float64)
    with pytest.raises(ValueError):
        apply_stretch(image)


def test_input_not_mutated():
    image = np.array([[1.0, 2.0], [3.0, 1.0]], dtype=np.float64)
    original = image.copy()
    apply_stretch(image)
    assert np.array_equal(image, original), "apply_stretch must not modify the caller's array"


def test_int_input_promoted():
    image = np.array([[1, 2], [3, 1]], dtype=np.int32)
    result = apply_stretch(image)
    assert result.dtype == np.float64
    assert result.shape == image.shape
    assert np.all(result >= 0.0) and np.all(result <= 1.0)


def test_output_clamped_to_unit_interval():
    # Pathological: very large negative floor + extreme values can produce
    # out-of-range MTF output without explicit clamping.
    rng = np.random.default_rng(42)
    image = rng.uniform(-1e6, 1e6, (10, 10))
    # Shift so nanmax > 0
    image += 2e6
    result = apply_stretch(image)
    assert result.min() >= 0.0, f"min {result.min()} < 0"
    assert result.max() <= 1.0, f"max {result.max()} > 1"


# ── Parameter coverage ─────────────────────────────────────────────────

@pytest.mark.parametrize("target_bkg", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_target_bkg_values(simple_image, target_bkg):
    result = apply_stretch(simple_image, target_bkg=target_bkg)
    assert result.shape == simple_image.shape
    assert np.all(result >= 0) and np.all(result <= 1)


@pytest.mark.parametrize("shadows_clip", [-3.0, -1.25, 0.0, 1.0])
def test_shadows_clip_values(simple_image, shadows_clip):
    result = apply_stretch(simple_image, shadows_clip=shadows_clip)
    assert result.shape == simple_image.shape
    assert np.all(result >= 0) and np.all(result <= 1)


# ── Property-based tests (hypothesis) ──────────────────────────────────


_2d_shape = st.tuples(st.integers(1, 20), st.integers(1, 20))

# Add a positive offset so nanmax > 0 (avoids the zero-image early-return path)
_positive_2d_image = np_arrays(
    np.float64,
    shape=_2d_shape,
    elements=st.floats(0.0, 1e6, allow_nan=False, allow_infinity=False),
).map(lambda a: a + 1.0)


@given(image=_positive_2d_image)
@settings(max_examples=100)
def test_output_in_valid_range(image):
    result = apply_stretch(image)
    assert result.shape == image.shape
    assert np.all(result >= 0.0) and np.all(result <= 1.0)


@given(image=_positive_2d_image)
@settings(max_examples=100)
def test_output_shape_preserved(image):
    result = apply_stretch(image)
    assert result.shape == image.shape


@given(image=_positive_2d_image)
@settings(max_examples=100)
def test_monotonic_in_input(image):
    """Doubling all input values should not decrease any output value."""
    result_a = apply_stretch(image)
    result_b = apply_stretch(image * 2)
    assert np.all(result_b >= result_a - 1e-10)
