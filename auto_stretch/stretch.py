"""
This product is based on software from the PixInsight project, developed by
Pleiades Astrophoto and its contributors (http://pixinsight.com/).
"""

import numpy as np


class Stretch:

    def __init__(self, target_bkg=0.25, shadows_clip=-1.25):
        self.shadows_clip = shadows_clip
        self.target_bkg = target_bkg

    def _get_avg_dev(self, data):
        """Return the average deviation from the median.

        Args:
            data (np.array): array of floats, presumably the image data
        """
        return np.mean(np.abs(data - np.median(data)))

    def _mtf(self, m, x):
        """Midtones Transfer Function

        MTF(m, x) = {
            0                for x == 0,
            1/2              for x == m,
            1                for x == 1,

            (m - 1)x
            --------------   otherwise.
            (2m - 1)x - m
        }

        See the section "Midtones Balance" from
        https://pixinsight.com/doc/tools/HistogramTransformation/HistogramTransformation.html

        Args:
            m (float): midtones balance parameter
                       a value below 0.5 darkens the midtones
                       a value above 0.5 lightens the midtones
            x (np.array or float): the data to transform (modified in place).
        """
        x = np.asarray(x, dtype=np.float64)
        zeros = x == 0
        halfs = x == m
        ones = x == 1
        nans = np.isnan(x)
        others = ~(zeros | halfs | ones | nans)

        x[zeros] = 0
        x[halfs] = 0.5
        x[ones] = 1
        x[others] = (m - 1) * x[others] / (((2 * m - 1) * x[others]) - m)
        # NaN values are left unchanged (propagate naturally)
        return x

    def _get_stretch_parameters(self, data):
        """Get the stretch parameters automatically.

        m (float) is the midtones balance
        c0 (float) is the shadows clipping point
        """
        median = np.median(data)
        avg_dev = self._get_avg_dev(data)

        c0 = np.clip(median + (self.shadows_clip * avg_dev), 0, 1)

        # Guard against degenerate c0 == 1 (would cause division by zero)
        if c0 >= 1:
            return {"c0": c0, "m": 0.5}

        m = self._mtf(self.target_bkg, (median - c0) / (1 - c0))

        return {
            "c0": c0,
            "m": m,
        }

    def stretch(self, data):
        """Stretch the image.

        Args:
            data (np.array): the original 2D image data array.

        Returns:
            np.array: the stretched image data (float64, values in [0, 1])

        Raises:
            ValueError: if data is empty or not 2-dimensional.
        """
        d = np.asarray(data, dtype=np.float64).copy()

        if d.size == 0:
            raise ValueError("Input array must be non-empty.")
        if d.ndim != 2:
            raise ValueError(
                f"Input array must be 2-dimensional, got {d.ndim}D array with shape {d.shape}."
            )

        max_val = np.nanmax(d)
        if max_val == 0:
            return np.zeros_like(d)

        # Normalize the data
        d /= max_val

        # Obtain the stretch parameters
        stretch_params = self._get_stretch_parameters(d)
        m = stretch_params["m"]
        c0 = stretch_params["c0"]

        # If c0 == 1 everything is clipped; return zeros immediately.
        if c0 >= 1:
            return np.zeros_like(d)

        # Selectors for pixels that lie below or above the shadows clipping point
        below = d < c0
        above = d >= c0

        # Clip everything below the shadows clipping point
        d[below] = 0

        # For the rest of the pixels: apply the midtones transfer function
        d[above] = self._mtf(m, (d[above] - c0) / (1 - c0))

        # Clamp output to [0, 1]
        np.clip(d, 0.0, 1.0, out=d)

        return d


# Wrapper function for simpler interface
def apply_stretch(data, target_bkg=0.25, shadows_clip=-1.25):
    return Stretch(target_bkg, shadows_clip).stretch(data)
