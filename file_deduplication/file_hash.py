import hashlib


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
    """Return file hash"""
    return hash_bytestr_iter(
        file_as_blockiter(open(file, "rb")),
        hashlib.sha256(),
        ashexstr=True,
    )
