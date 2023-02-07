import os
import shutil
import sys


def delete_empty_dirs(path):
    """Delete every subdirectory which is empty or contains only a directory named @eaDir"""
    if not os.path.isdir(path):
        return

    # Remove empty sub-directories
    files = os.listdir(path)
    if len(files):
        for f in files:
            full_path = os.path.join(path, f)
            if os.path.isdir(full_path):
                delete_empty_dirs(full_path)

    # If directory is empty or contains only "@eaDir", delete it
    files = os.listdir(path)
    if len(files) == 0 or (len(files) == 1 and files[0] == "@eaDir"):
        print("Deleting empty directory:", path)
        shutil.rmtree(path)


if __name__ == "__main__":
    PATH = sys.argv[1]

    delete_empty_dirs(PATH)
