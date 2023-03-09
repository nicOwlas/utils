import hashlib
import pathlib

import imagehash
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()


def hash_bytestr_iter(bytesiter, hasher, ashexstr=False):
    for block in bytesiter:
        hasher.update(block)
    return hasher.hexdigest() if ashexstr else hasher.digest()


def file_as_blockiter(afile, blocksize=65536):
    with afile:
        block = afile.read(blocksize)
        while len(block) > 0:
            yield block
            block = afile.read(blocksize)


def hexhash(file: str):
    """Return file sha256 hash"""
    return hash_bytestr_iter(
        file_as_blockiter(open(file, "rb")),
        hashlib.sha256(),
        ashexstr=True,
    )


def dhash(file: str):
    """Return 16 bit perceptual hash of an image file (JPG, TIFF, HEIC, PNG)"""
    ext = pathlib.Path(file).suffix.lower()
    if ext in [".jpg", ".jpeg", ".png", ".heic"]:
        return str(
            imagehash.dhash(
                Image.open(file),
                hash_size=16,
            )
        )
    else:
        print(f"{ext} file type is not supported")
        return None

    # if ext not in [".jpg", ".jpeg", ".png", ".heic"]:
    #     return ""
    #     raise ValueError(f"{ext} file type is not supported")
    # return imagehash.dhash(
    #     Image.open(file),
    #     hash_size=16,
    # )
