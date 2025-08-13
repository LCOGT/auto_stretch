import pytest
import numpy as np
from astropy.io import fits
from auto_stretch import stretch
from auto_stretch import apply_stretch

def test_stretch_from_class():
    s = stretch.Stretch()
    image = np.array([[1,2],[3,1]])
    stretched_image = s.stretch(image) 
    print(f"Image: {image}")
    print(f"Stretched image: {stretched_image}")
    assert np.shape(stretched_image) == np.shape(image)

def test_stretch_from_standalone():
    image = np.array([[1,2],[3,1]])
    stretched_image = apply_stretch(image) 
    print(f"Image: {image}")
    print(f"Stretched image: {stretched_image}")
    assert np.shape(stretched_image) == np.shape(image)

def test_stretch_with_fits_file():
    file = fits.open("test_image.fits")
    image = file[0].data
    s = stretch.Stretch()
    stretched_image = s.stretch(image)
    print(f"Image: {image}")
    print(f"Stretched image: {stretched_image}")
    assert np.shape(stretched_image) == np.shape(image)
    fits.writeto("stretched_test_image.fits", stretched_image, header=file[0].header, overwrite=True)

if __name__ == "__main__":
    pytest.main([__file__])