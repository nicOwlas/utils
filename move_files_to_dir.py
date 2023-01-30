import json
import os
import pathlib
import shutil
import sys


# Move duplicated files
# Priority 1: extension is in list of valid extensions (do not move .lua, .lrdata)
# Priority 2: ignore when there are 2 duplicates and one is in #recycle
# Priority 3: keep the file with the shortest path
def filter_files(duplicated_files, extensions_watched, keep_file_with_longest_path):
    files_to_move = []
    for k in duplicated_files["duplicates"].keys():
        # Remove from list the files with #recycle in its path
        files_outside_bin = [
            file
            for file in duplicated_files["duplicates"][k]
            if "blablibloblu" not in file
        ]
        # Sort the list of files with the shortest path first
        duplicated_sorted_files = sorted(
            files_outside_bin,
            key=len,
            reverse=parse_boolean(keep_file_with_longest_path),
        )

        # Consider moving files if at least one element is in the list
        if len(duplicated_sorted_files) > 1:
            for file in duplicated_sorted_files[1:]:
                _, file_extension = os.path.splitext(file)
                if file_extension.lower() in extensions_watched:
                    files_to_move.append(file)
    print("Files to move: \n", json.dumps(files_to_move, indent=4, sort_keys=True))
    return files_to_move


def parse_boolean(string):
    return string.lower() in [
        "true",
        "1",
        "t",
        "y",
        "yes",
    ]


def move_files(files_to_move, destination):
    for count, file in enumerate(files_to_move):
        destination_path = os.path.join(destination, file[1:])
        # Create directory if it does not exist
        pathlib.Path(os.path.dirname(destination_path)).mkdir(
            parents=True, exist_ok=True
        )
        print(f"Moving file #{count}: {destination_path}")
        try:
            shutil.move(file, destination_path)
        except FileNotFoundError:
            print("File not found")


if __name__ == "__main__":
    input_file = sys.argv[1]
    destination = sys.argv[2]
    keep_file_with_longest_path = sys.argv[3]
    extensions_watched = {
        ".wav",
        ".jpeg",
        ".mp4",
        ".heic",
        ".jpg",
        ".cr2",
        ".dng",
        ".avi",
        ".mov",
        ".png",
        ".thm",
    }
    with open(input_file, "r", encoding="utf-8") as f:
        duplicated_files = json.load(f)

    print(
        "Number of hash with duplicates: ", len(duplicated_files["duplicates"].keys())
    )

    files_to_move = filter_files(
        duplicated_files, extensions_watched, keep_file_with_longest_path
    )
    move_files(files_to_move, destination)
