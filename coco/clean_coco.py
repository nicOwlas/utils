import sys, getopt, json, logging

logger = logging.getLogger(__name__)


def __eq__(self, other):
    return self.name == other.name and self.supercategory == other.supercategory


def __hash__(self):
    return hash(("name", self.name, "supercategory", self.supercategory))


def coco_clean(input_dirty: str, output_clean: str) -> str:
    """Clean COCO annotation files by removing duplicated classes

    Args:
        input_dirty: Path to input file to be cleaned
        output_file : Path to output file with duplicated annotations removed
    """
    indent = 4
    with open(input_dirty, "r") as f:
        data_dirty = json.load(f)

    output: Dict[str, Any] = {
        k: data_dirty[k] for k in data_dirty if k not in ("categories", "annotations")
    }

    print("Categories", data_dirty["categories"])

    unique_categories = set()
    output["categories"], output["annotations"] = [], []
    mapping_category_old_id_new_id = {}
    mapping_category_name_new_id = {}
    for category in data_dirty["categories"]:
        if category["name"] not in unique_categories:
            unique_categories.add(category["name"])
            mapping_category_name_new_id[category["name"]] = category["id"]
            mapping_category_old_id_new_id[category["id"]] = category["id"]
            output["categories"].append(category)
        else:
            mapping_category_old_id_new_id[
                category["id"]
            ] = mapping_category_name_new_id[category["name"]]

    for annotation_dirty in data_dirty["annotations"]:
        annotation_cleaned = {
            key: annotation_dirty[key]
            for key in annotation_dirty
            if key not in ("category_id")
        }
        annotation_cleaned["category_id"] = mapping_category_old_id_new_id[
            annotation_dirty["category_id"]
        ]
        output["category_id"] = mapping_category_name_new_id[category["name"]]
        output["annotations"].append(annotation_cleaned)

    print("Categories", output["categories"])
    print("mapping_category_old_id_new_id", mapping_category_old_id_new_id)
    print("mapping_category_name_new_id", mapping_category_name_new_id)
    with open(output_clean, "w") as f:
        json.dump(output, f, indent=indent)

    #     logger.info(
    #         "Input {}: {} images, {} annotations".format(
    #             i + 1, len(data["images"]), len(data["annotations"])
    #         )
    #     )

    #     cat_id_map = {}
    #     for new_cat in data["categories"]:
    #         new_id = None
    #         for output_cat in output["categories"]:
    #             if new_cat["name"] == output_cat["name"]:
    #                 new_id = output_cat["id"]
    #                 break

    #         if new_id is not None:
    #             cat_id_map[new_cat["id"]] = new_id
    #         else:
    #             new_cat_id = max(c["id"] for c in output["categories"]) + 1
    #             cat_id_map[new_cat["id"]] = new_cat_id
    #             new_cat["id"] = new_cat_id
    #             output["categories"].append(new_cat)

    #     img_id_map = {}
    #     for image in data["images"]:
    #         n_imgs = len(output["images"])
    #         img_id_map[image["id"]] = n_imgs
    #         image["id"] = n_imgs

    #         output["images"].append(image)

    #     for annotation in data["annotations"]:
    #         n_anns = len(output["annotations"])
    #         annotation["id"] = n_anns
    #         annotation["image_id"] = img_id_map[annotation["image_id"]]
    #         annotation["category_id"] = cat_id_map[annotation["category_id"]]

    #         output["annotations"].append(annotation)

    # logger.info(
    #     "Result: {} images, {} annotations".format(
    #         len(output["images"]), len(output["annotations"])
    #     )
    # )

    # with open(output_file, "w") as f:
    #     json.dump(output, f, indent=indent)

    # print("Merge status: Finished")

    # return output_file


if __name__ == "__main__":
    # try:
    input_dirty = sys.argv[1]
    output = sys.argv[2]
    print("Clean status: Starting")
    coco_clean(input_dirty, output)
    # except:
    #     print(
    #         "One or more argument missing. Syntax: > merge_coco.py inputfile1.json inputfile2.json output.json"
    #     )
    #     sys.exit(2)
