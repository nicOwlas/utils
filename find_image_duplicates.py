import glob
import hashlib
from os.path import isfile, join
from os import listdir
import os, sys
import json


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


def hexhash(file_name):
    return hash_bytestr_iter(
        file_as_blockiter(open(file_name, "rb")),
        hashlib.sha256(),
        ashexstr=True,
    )


def file_list(input_path):
    file_name_list = []
    exclude_directories = set(["@eaDir"])  # Do not explore Synology hidden directory
    for input_path, dirs, files in os.walk(input_path):
        dirs[:] = [
            d for d in dirs if d not in exclude_directories
        ]  # exclude directory if in exclude list
        files = [file for file in files if not file[0] == "."]
        for file in files:
            file_name_list.append(os.path.join(input_path, file))
    print(json.dumps(file_name_list, indent=4, sort_keys=True))
    return file_name_list


if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    # input_path = "/Volumes/GoogleDrive-112639467614389739071/My Drive/Pictures/2022/05"

    file_name_list = file_list(input_path)

    seen = set()
    duplicates = []

    for file_name in file_name_list:
        file_hash = hexhash(file_name)
        if file_hash in seen:
            duplicates.append((file_name, file_hash))
        else:
            seen.add((file_name, file_hash))

    # print("Duplicates:", duplicates)
    # print("Number of analyzed files:", len(file_name_list))
    with open(output_path, "w") as outfile:
        outfile.write(
            json.dumps({"duplicates": duplicates, "seen": list(seen)}, indent=4)
        )
