# Generate a test fits file to ensure autostretch works in production

import numpy as np
from astropy.io import fits

# Parameters
ny, nx = 1024, 1024   # image size
n_stars = 50        # number of stars
seed = 42
output_file = "test_image.fits"

# Random seed for reproducibility
rng = np.random.default_rng(seed)

# Background
image = np.full((ny, nx), 1000.0, dtype=np.float32)

# Add some stars as Gaussian spots
y, x = np.mgrid[0:ny, 0:nx]
for _ in range(n_stars):
    x0 = rng.uniform(0, nx)
    y0 = rng.uniform(0, ny)
    amp = rng.uniform(500, 5000)
    sigma = rng.uniform(1.0, 2.5)
    image += amp * np.exp(-((x - x0) ** 2 + (y - y0) ** 2) / (2 * sigma ** 2))

# Add noise
image += rng.normal(0, 5, size=image.shape)

# Save to FITS
hdu = fits.PrimaryHDU(image)

hdu.header["NUMSTARS"] = n_stars
hdu.header["SEED"] = seed
hdu.header["HISTORY"] = "Created synthetic image with stars for auto_stretch test"

hdu.writeto(output_file, overwrite=True)

print(f"Created {output_file}")
