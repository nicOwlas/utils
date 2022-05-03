import json, os, sys, shutil

# Move duplicated files
# Priority 1: extension is in list of valid extensions (do not move .lua, .lrdata)
# Priority 2: ignore when there are 2 duplicates and one is in #recycle
# Priority 3: keep the file with the shortest path
def filter_files(duplicated_files, extensions_watched):
    files_to_move = []
    for k in duplicated_files["duplicates"].keys():
        # Remove from list the files with #recycle in its path
        files_outside_bin = [
            file for file in duplicated_files["duplicates"][k] if "#recycle" not in file
        ]
        # Sort the list of files with the shortest path first
        duplicated_sorted_files = sorted(files_outside_bin, key=len)

        # Consider moving files if at least one element is in the list
        if len(duplicated_sorted_files) > 1:
            print("\nKeep ", duplicated_sorted_files[0])
            for file in duplicated_sorted_files[1:]:
                filename, file_extension = os.path.splitext(file)
                if file_extension in extensions_watched:
                    files_to_move.append(file)
                    print("Move ", file)
    return files_to_move


def move_files(files_to_move, destination):
    for file in files_to_move:
        print("Moving file {} to {}".format(file, os.path.join(destination, file[1:])))
        # shutil.move(file, os.join(destination, file))


if __name__ == "__main__":
    input_file = sys.argv[1]
    destination = sys.argv[2]
    extensions_watched = {
        ".WAV",
        ".JPEG",
        ".MP4",
        ".HEIC",
        ".JPG",
        ".CR2",
        ".dng",
        ".jpeg",
        ".mp4",
        ".jpg",
        ".avi",
        ".MOV",
        ".PNG",
        ".mov",
        ".png",
        ".heic",
    }
    # "/Users/nicolas/Downloads/2022-05-02_duplicates-test.json"
    with open(input_file, "r") as f:
        duplicated_files = json.load(f)

    print(
        "Number of hash with duplicates: ", len(duplicated_files["duplicates"].keys())
    )

    files_to_move = filter_files(duplicated_files, extensions_watched)
    move_files(files_to_move, destination)
    print(destination)
