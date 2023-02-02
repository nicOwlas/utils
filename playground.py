"""Play with yield"""
import json
import os


def list_of_files(input_path: str) -> list:
    """test os.walk"""
    for directory_path, _, files in os.walk(input_path):
        for file in files:
            yield os.path.join(directory_path, file)


def export_file_names(file_name: str, output_file: str):
    """export file names"""
    print(file_name)
    # try:
    #     with open(output_file, "r", encoding="utf-8") as file:
    #         data = json.load(file)
    # except FileNotFoundError:
    #     with open(output_file, "w", encoding="utf-8") as file:
    #         json.dump(file_names, file, indent=4)
    # else:
    #     data.update(file_names)
    #     with open(output_file, "w", encoding="utf-8") as file:
    #         json.dump(data, file, indent=4)
    # file.write()


if __name__ == "__main__":
    path = "/Users/nicolas/Library/CloudStorage/GoogleDrive-nicolas.draber@gmail.com/My Drive/Pictures/Mobile/iPhone de Nicolas"
    output_file = "/Users/nicolas/Downloads/filenames.json"
    file_generator = list_of_files(path)
    for file in file_generator:
        export_file_names(file_name=file, output_file=output_file)
