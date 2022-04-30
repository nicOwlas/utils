import glob
import hashlib
from os.path import isfile, join
from os import listdir


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


if __name__ == "__main__":
    path = "/Volumes/GoogleDrive-112639467614389739071/My Drive/Pictures/2022/02"
    file_name_list = [join(path, f) for f in listdir(path) if isfile(join(path, f))]

    seen = set()
    duplicates = []

    for file_name in file_name_list:
        file_hash = hash_bytestr_iter(
            file_as_blockiter(open(file_name, "rb")),
            hashlib.sha256(),
            ashexstr=True,
        )
        if file_hash in seen:
            duplicates.append((file_name, file_hash))
        else:
            seen.add((file_name, file_hash))

    print("Duplicates:", duplicates)
    # print("Seen:", seen)
