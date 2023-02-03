"""
Find file duplicates in a given directory
Be able to resume
    - Create a DB (path, secret)
    - 
    - Store the checked images : hash : [path]
    - Store the duplicated images = hash : [path]
    - Store the files = [paths]
    - store the paths [path]
    - create a json for every file with its hash
0. Open an existing json
    - add an option to scan for new files
1. For every image:
    if image was checked:
        continue
    else:
        check image
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
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


def hexhash(file: str):
    """Return file hash"""
    return hash_bytestr_iter(
        file_as_blockiter(open(file, "rb")),
        hashlib.sha256(),
        ashexstr=True,
    )


def file_list(input_dir: str, extensions_to_skip: list):
    """List files in input_dir"""
    file_names = []
    exclude_directories = set(
        [
            "@eaDir",
            "Lightroom",
            "Lightroom (1)",
            "Lightroom_1",
            "Lightroom_2",
            "Lightroom-old",
        ]
    )  # Do not explore Synology hidden directory
    for input_dir, dirs, files in os.walk(input_dir):
        dirs[:] = [
            d for d in dirs if d not in exclude_directories
        ]  # exclude directory if in exclude list
        files = [file for file in files if not file[0] == "."]
        for file in files:
            _, file_extension = os.path.splitext(file)
            if file_extension.lower() not in extensions_to_skip:
                file_names.append(os.path.join(input_dir, file))
    print(json.dumps(file_names, indent=4, sort_keys=True))
    return file_names


if __name__ == "__main__":
    INPUT_PATH = sys.argv[1]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    OUTPUT_FILE = f"{INPUT_PATH}{os.path.sep}{now}-duplicatedFiles.json"
    EXTENSIONS_TO_IGNORE = [
        ".zip",
        ".db",
        ".db-wal",
        ".db-shm",
        ".lrcat",
        ".lrcat-wal",
        ".lrcat-shm",
        ".lock",
        ".docstore-wal",
        ".wfindex-wal",
    ]

    file_name_list = file_list(INPUT_PATH, EXTENSIONS_TO_IGNORE)

    NUMBER_OF_FILES = len(file_name_list)
    print("Number of files to check:", NUMBER_OF_FILES)
    duplicated_files = {}
    checked_files = {}
    for file_index, file_name in enumerate(file_name_list):
        progress = (file_index + 1) / NUMBER_OF_FILES
        print(
            "[%-100s] %d%%" % ("=" * int(100 * progress), 100 * progress),
            end="\r",
        )
        sleep(0.001)
        FILE_HASH = hexhash(file_name)
        if FILE_HASH in checked_files:
            checked_files[FILE_HASH].append(file_name)
            duplicated_files[FILE_HASH] = checked_files[FILE_HASH]
        else:
            checked_files[FILE_HASH] = [file_name]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        outfile.write(
            json.dumps(
                {"duplicates": duplicated_files, "checked": checked_files}, indent=4
            )
        )
    print(f"\nNumber of duplicates: {len(duplicated_files)}")
