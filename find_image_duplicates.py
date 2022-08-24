import glob
import hashlib
from os.path import isfile, join
from os import listdir
import os, sys
import json
from time import sleep


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

    file_name_list = file_list(input_path)
    seen = set()

    number_of_files = len(file_name_list)
    print("Number of files to check:", number_of_files)
    duplicated_files = {}
    checked_files = {}
    for file_index, file_name in enumerate(file_name_list):
        progress = (file_index + 1) / number_of_files
        print(
            "[%-100s] %d%%" % ("=" * int(100 * progress), 100 * progress),
            end="\r",
        )
        sleep(0.001)
        file_hash = hexhash(file_name)
        if file_hash in checked_files:
            checked_files[file_hash].append(file_name)
            duplicated_files[file_hash] = checked_files[file_hash]
        else:
            checked_files[file_hash] = [file_name]

    with open(output_path, "w") as outfile:
        outfile.write(
            json.dumps(
                {"duplicates": duplicated_files, "checked": checked_files}, indent=4
            )
        )
    print("\nNumber of duplicates:", len(duplicated_files))
