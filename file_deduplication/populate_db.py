"""
Store files' hash in a DB
"""
import os
import sys

from db_operations import (
    create_db,
    insert_db_entry,
    is_ascii_path_in_db,
    is_dhash_null,
    update_dhash,
)
from unidecode import unidecode


def is_path_relevant(path: str, directories_to_ignore: list) -> bool:
    """A path containing a subdirectory in the directories_to_ignore list is not relevant"""

    path = os.path.normpath(path)
    path_parts = path.split(os.sep)

    if any(dir_name in path_parts for dir_name in directories_to_ignore):
        return False
    else:
        return True


def scantree(path, directories_to_ignore: list, relevant_extensions: list):
    """Recursively yield DirEntry objects for given directory."""
    for entry in os.scandir(path):
        try:
            if entry.is_dir(follow_symlinks=False) and is_path_relevant(
                entry.path, directories_to_ignore
            ):
                yield from scantree(
                    entry.path, directories_to_ignore, relevant_extensions
                )
            else:
                entry_extension = os.path.splitext(entry.name)[-1].lower()
                if entry_extension in set(relevant_extensions):
                    yield entry
        except PermissionError:  # No access to file or folder
            continue


def populate_db(
    root_path: str, db_path: str, directories_to_ignore: list, relevant_extensions: list
):
    """Store in a DB, media files hashes"""
    connection, cursor = create_db(db_path)
    files_generator = scantree(root_path, directories_to_ignore, relevant_extensions)
    count_files = 0
    added_files = 0
    with connection:
        for file in files_generator:
            if file.is_file():
                count_files += 1
                print(f"Analyzing file #{count_files} - {file.path}")
                relative_path = os.path.relpath(file.path, root_path)
                ascii_path = unidecode(relative_path).lower()

                if not is_ascii_path_in_db(ascii_path, cursor):
                    insert_db_entry(relative_path, file.path, ascii_path, cursor)
                    added_files += 1
                elif is_dhash_null(ascii_path, cursor):
                    update_dhash(ascii_path, file.path, cursor)
                    added_files += 1

            if added_files > 0 and added_files % 100 == 0:
                connection.commit()
                print(f"Committing to DB - Files analyzed: {count_files}")
        connection.commit()

    print(f"Task completed: Scanned {count_files} files. Added {added_files} files")


if __name__ == "__main__":
    INPUT_PATH = sys.argv[1]
    DB_PATH = sys.argv[2]
    media_extensions = [
        ".jpeg",
        ".heic",
        ".tiff",
        ".jpg",
        ".cr2",
        ".raf",
        ".zip",
        ".png",
        ".mov",
        ".avi",
        ".mp4",
        ".dng",
    ]
    directories_to_ignore = ["@eaDir", "Lightroom"]
    populate_db(
        root_path=INPUT_PATH,
        db_path=DB_PATH,
        directories_to_ignore=directories_to_ignore,
        relevant_extensions=media_extensions,
    )
