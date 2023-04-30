import base64
import dataclasses
import zlib
from typing import List, Optional

import numpy as np


@dataclasses.dataclass
class ImageData:
    data: str
    shape: List[int]
    compressed: bool
    width: int
    height: int
    channels: Optional[int] = None


def serialize_image(image: np.ndarray, compress: bool = False) -> ImageData:
    """
    Takes a numpy array of image data, and transforms it into format that can
    be sent over JSON. Expects a 2D or 3D numpy array. If the array does
    not contain integers, all of the values will be rounded to the nearest
    integer. `compress` enables zlib compression.
    """
    # record the shape before we start making changes
    shape = list(np.shape(image))

    # round all of the items to integers
    image_rounded = np.rint(image).astype(int)
    # flatten the array
    image_integer_list: List[int] = image_rounded.flatten().tolist()
    # convert the flat integer list into a bytearray
    image_byte_array = bytearray(image_integer_list)

    # compress with zlib if desired
    if compress:
        image_byte_array = zlib.compress(image_byte_array)

    # convert to base64 and convert to a string
    base64_image_data = base64.b64encode(image_byte_array).decode("utf-8")

    # build class
    image_data = ImageData(
        data=base64_image_data,
        shape=shape,
        compressed=compress,
        width=shape[0],
        height=shape[1],
    )

    # if the array has at least 2 dimensions
    if len(shape) > 2:
        image_data.channels = shape[2]

    return image_data


def deserialize_image(image_data: ImageData) -> np.ndarray:
    """
    Given an `ImageData` object, will reconstruct the original numpy array.
    """
    # convert the string to bytes, and then undo the base64
    image_bytes = base64.b64decode(image_data.data.encode("utf-8"))

    # decompress with zlib
    if image_data.compressed:
        image_bytes = zlib.decompress(image_bytes)

    # convert bytes to a byte array
    image_byte_array = bytearray(image_bytes)
    # convert the byte array back into a numpy array
    image_array = np.array(image_byte_array)

    return np.reshape(image_array, image_data.shape)
