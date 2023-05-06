import numpy as np
import pytest

from bell.avr.utils import images


@pytest.mark.parametrize(
    "in_image, compress",
    [
        (np.array([[1, 2], [3, 4]]), False),
        (np.array([[1, 2], [3, 4]]), True),
        (np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]]), False),
        (np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]]), True),
    ],
)
def test_serialization(in_image: np.ndarray, compress: bool) -> None:
    # this is a full end-to-end test to make sure data in = data out

    image_data = images.serialize_image(in_image, compress)
    out_image = images.deserialize_image(image_data)

    print(in_image)
    print(out_image)
    np.testing.assert_array_equal(in_image, out_image)
