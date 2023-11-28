import json
import logging
import sys
from itertools import chain

logger = logging.getLogger(__name__)


def bounding_box(points):
    """Compute the bounding box of a polygon
    * Sterblue image axis: (0,0): top left corner, x positive to the right, y positive upward
    * COCO image axis: (0,0): top left corner, x positive to the right, y positive downward

    Args:
        points: List of points [ [x0, y0], [x1, y1], etc.]
    Return:
        Bounding box output format: [xmin, ymin, width, height]
    """
    x_coordinates, y_coordinates = zip(*points)
    xmin = min(x_coordinates)
    ymin = -max(y_coordinates)
    width = max(x_coordinates) - min(x_coordinates)
    height = max(y_coordinates) - min(y_coordinates)
    area = width * height
    return {"geometry": [xmin, ymin, width, height], "area": area}


def transform_sterblue_to_coco(
    input_sterblue: str, input_anomalyLevelMappings: str, output_file: str
) -> str:
    """Transform STERBLUE annotation file to COCO annotation file format.

    Args:
        input_sterblue: Path to sterblue input file.
        output_file : Path to COCO format output file.
    """
    indent = 4
    with open(input_sterblue, "r") as f:
        data_sterblue = json.load(f)
    with open(input_anomalyLevelMappings, "r") as f:
        data_anomalyLevelMappings = json.load(f)

    mapping_missionType_structureType = {
        "InspectWindTurbine": "WindTurbine",
        "InspectPowerLineHighVoltagePylon": "HighVoltagePowerLine",
        "InspectPowerLineMediumVoltagePylon": "MediumVoltagePowerLine",
        "InspectCoolingTower": "CoolingTower",
        "InspectSolarFarm": "SolarFarm",
    }

    output: Dict[str, Any] = {
        "info": {
            "contributor": "",
            "date_created": "",
            "description": "",
            "url": "",
            "version": "",
            "year": "",
        },
        "licenses": [{"name": "", "id": 0, "url": ""}],
    }

    output["categories"], output["images"], output["annotations"] = [], [], []

    # Build the list of categories
    anomalyLevelMappings = data_anomalyLevelMappings["anomalyLevelMappings"]
    index_category = 1
    unique_categories = set()
    mapping_category_name_index = {}
    valid_anomalyLevelMapping_found = 0
    for anomalyLevelMapping in anomalyLevelMappings:
        # Only consider the anomaly level mappings compatible with the sterblue mission type being converted to COCO
        if (data_sterblue["type"] in mapping_missionType_structureType) and (
            anomalyLevelMapping["structureType"]
            == mapping_missionType_structureType[data_sterblue["type"]]
        ):
            valid_anomalyLevelMapping_found = 1
            for anomalyType in anomalyLevelMapping["anomalyTypes"]:
                # Add only unique categories
                if anomalyType["name"] not in unique_categories:
                    unique_categories.add(anomalyType["name"])
                    mapping_category_name_index[anomalyType["name"]] = index_category
                    output["categories"].append(
                        {
                            "id": index_category,
                            "name": anomalyType["name"],
                            "supercategory": "",
                        }
                    )
                    index_category += 1

    # No compatible mappings have been found
    if valid_anomalyLevelMapping_found == 0:
        print(
            f'Error. No mapping found for mission "{data_sterblue["id"]+"-"+data_sterblue["name"]}" with mission type "{data_sterblue["type"]}"'
        )
        exit()

    # Build the list of images
    index_annotation = 1
    images = data_sterblue["execution"]["images"]
    for index_image, image in enumerate(images, start=1):
        output["images"].append(
            {
                "id": index_image,
                "file_name": image["file"]["name"] + "-" + image["id"] + ".jpeg",
                "coco_url": "",
                "date_captured": image["capturedAt"],
                "height": image["height"],
                "width": image["width"],
                "license": 0,
            }
        )

        # Build the list of annotations
        for detection in image["detections"]:
            polygon_geometry = detection["geometry"]["geojson"]["coordinates"][0]
            bbox = bounding_box(polygon_geometry)
            output["annotations"].append(
                {
                    "id": index_annotation,
                    "image_id": index_image,
                    "category_id": mapping_category_name_index.get(
                        detection["type"]["name"], -1
                    ),
                    "segmentation": [
                        [
                            abs(coordinate)
                            for coordinate in list(chain(*polygon_geometry))
                        ]
                    ],
                    "area": bbox["area"],
                    "bbox": bbox["geometry"],
                    "iscrowd": 0,
                }
            )
            index_annotation += 1

    print(json.dumps(mapping_category_name_index, indent=4))

    with open(output_file, "w") as f:
        json.dump(output, f, indent=indent)

    print("Merge status: Finished")

    return output_file


if __name__ == "__main__":
    input_sterblue = sys.argv[1]
    input_categories = sys.argv[2]
    output = sys.argv[3]
    print("Transform status: Starting")
    transform_sterblue_to_coco(input_sterblue, input_categories, output)
