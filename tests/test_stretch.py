import pytest
import numpy as np
from auto_stretch import stretch

def test_stretch():
    s = stretch.Stretch()
    image = np.array([[1,2],[3,1]])
    stretched_image = s.stretch(image) 
    print(f"Image: {image}")
    print(f"Stretched image: {stretched_image}")
    assert np.shape(stretched_image) == np.shape(image)

