import base64
import zlib
from typing import List, TypedDict

import numpy as np


class ImageData(TypedDict):
    """
    Data structure to hold image data and metadata.
    This is a TypedDict so it can easily be used with other classes with parameter
    expansion.

    Example:

    ```python
    from bell.avr.mqtt.payloads import AVRVIOImageCapture
    from bell.avr.utils.images import serialize_image


    image_data = self.camera.get_rgb_image(side)
    serialized_image_data = serialize_image(image_data, compress=compressed)

    payload = AVRVIOImageCapture(**serialized_image_data, side=side)
    self.send_message("avr/vio/image/capture", payload)
    ```
    """

    data: str
    """
    The raw image data after it has been base64-encoded.
    """
    shape: List[int]
    """
    The shape of the image data. This could be 2D or 3D.
    2D is simply width and height, while 3D includes the number of
    channels for each pixel (Red, Green, Blue for example).
    """
    compressed: bool
    """
    Whether or not the image data is compressed.
    """


def serialize_image(image: np.ndarray, compress: bool = False) -> ImageData:
    """
    Takes a numpy array of image data, and transforms it into format that can
    be sent over JSON. Expects a 2D or 3D numpy array. If the array does
    not contain integers, all of the values will be rounded to the nearest
    integer. Setting `compress` to `True` enables
    [zlib](https://docs.python.org/3/library/zlib.html) compression.
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
    image_data = ImageData(data=base64_image_data, shape=shape, compressed=compress)

    return image_data


def deserialize_image(image_data: ImageData) -> np.ndarray:
    """
    Given an `ImageData` object, will reconstruct the original numpy array.
    """
    # convert the string to bytes, and then undo the base64
    image_bytes = base64.b64decode(image_data["data"].encode("utf-8"))

    # decompress with zlib
    if image_data["compressed"]:
        image_bytes = zlib.decompress(image_bytes)

    # convert bytes to a byte array
    image_byte_array = bytearray(image_bytes)
    # convert the byte array back into a numpy array
    image_array = np.array(image_byte_array)

    return np.reshape(image_array, image_data["shape"])
