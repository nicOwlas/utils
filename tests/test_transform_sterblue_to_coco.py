import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "coco"))

from transform_sterblue_to_coco import build_categories, convert_mission, coco_output_name, merge_missions


def detection(name, rings, det_id="d1"):
    return {
        "id": det_id,
        "deletedAt": None,
        "type": {"name": name},
        "geometry": {"geojson": {"type": "Polygon", "coordinates": rings}},
        "author": {"name": "annotator"},
        "level": 0.5,
    }


def mission(detections, mission_id="m1"):
    return {
        "id": mission_id,
        "name": "Mission",
        "createdAt": "2020-11-19T10:00:00",
        "type": "InspectPowerLineMediumVoltagePylon",
        "execution": {
            "images": [
                {
                    "id": "img1",
                    "capturedAt": "2020-05-09T17:05:52",
                    "width": 100,
                    "height": 50,
                    "file": {"name": "DJI_0001.JPG"},
                    "detections": detections,
                }
            ]
        },
    }


METADATA = {
    "anomalyLevelMappings": [
        {"structureType": "MediumVoltagePowerLine", "anomalyTypes": [{"name": "A"}, {"name": "B"}]},
        {"structureType": "WindTurbine", "anomalyTypes": [{"name": "W"}]},
    ]
}

SQUARE = [[10, -10], [20, -10], [20, -20], [10, -20], [10, -10]]


class TestBuildCategories(unittest.TestCase):
    def test_mapped_types_first_then_unmapped_used_types(self):
        categories = build_categories(METADATA, "MediumVoltagePowerLine", ["Z", "A", "Y"])
        self.assertEqual([c["name"] for c in categories], ["A", "B", "Y", "Z"])
        self.assertEqual([c["id"] for c in categories], [1, 2, 3, 4])
        self.assertEqual([c["in_anomaly_mapping"] for c in categories], [True, True, False, False])


class TestConvertMission(unittest.TestCase):
    def convert(self, detections):
        categories = build_categories(METADATA, "MediumVoltagePowerLine", ["Unmapped"])
        return convert_mission(mission(detections), categories)

    def test_flips_y_and_uses_polygon_area(self):
        coco, dropped = self.convert([detection("A", [SQUARE])])
        ann = coco["annotations"][0]
        self.assertEqual(dropped, 0)
        self.assertEqual(ann["bbox"], [10, 10, 10, 10])
        self.assertEqual(ann["area"], 100)
        self.assertEqual(ann["segmentation"], [[10, 10, 20, 10, 20, 20, 10, 20, 10, 10]])

    def test_unmapped_type_gets_a_real_category(self):
        coco, _ = self.convert([detection("Unmapped", [SQUARE])])
        self.assertEqual(coco["annotations"][0]["category_id"], 3)

    def test_keeps_every_ring_as_a_polygon(self):
        second = [[50, -10], [60, -10], [60, -20], [50, -10]]
        coco, _ = self.convert([detection("A", [SQUARE, second])])
        ann = coco["annotations"][0]
        self.assertEqual(len(ann["segmentation"]), 2)
        self.assertEqual(ann["bbox"], [10, 10, 50, 10])
        self.assertEqual(ann["area"], 150)

    def test_clips_to_image_bounds(self):
        outside = [[-5, 3], [110, 3], [110, -60], [-5, -60], [-5, 3]]
        coco, _ = self.convert([detection("A", [outside])])
        self.assertEqual(coco["annotations"][0]["bbox"], [0, 0, 100, 50])

    def test_drops_degenerate_polygons(self):
        line = [[10, -10], [20, -10], [10, -10]]
        coco, dropped = self.convert([detection("A", [line])])
        self.assertEqual((coco["annotations"], dropped), ([], 1))

    def test_image_file_name_matches_export_jpeg(self):
        coco, _ = self.convert([])
        self.assertEqual(coco["images"][0]["file_name"], "DJI_0001.JPG-img1.jpeg")


class TestCocoOutputName(unittest.TestCase):
    def test_appends_coco_suffix(self):
        self.assertEqual(coco_output_name("2020-11-19-Mission-abc.json"), "2020-11-19-Mission-abc.coco.json")

    def test_replaces_characters_windows_rejects(self):
        self.assertEqual(coco_output_name('Zone Janne?e <a>:b"c|d*.json'), "Zone Janne_e _a__b_c_d_.coco.json")


class TestMergeMissions(unittest.TestCase):
    def test_reindexes_ids_and_prefixes_file_names_with_mission_dir(self):
        categories = build_categories(METADATA, "MediumVoltagePowerLine", [])
        first, _ = convert_mission(mission([detection("A", [SQUARE])], "m1"), categories)
        second, _ = convert_mission(mission([detection("B", [SQUARE], "d2")], "m2"), categories)

        merged = merge_missions([("dir one", first), ("dir two", second)])

        self.assertEqual([i["id"] for i in merged["images"]], [1, 2])
        self.assertEqual(
            [i["file_name"] for i in merged["images"]],
            ["dir one/DJI_0001.JPG-img1.jpeg", "dir two/DJI_0001.JPG-img1.jpeg"],
        )
        self.assertEqual([a["id"] for a in merged["annotations"]], [1, 2])
        self.assertEqual([a["image_id"] for a in merged["annotations"]], [1, 2])
        self.assertEqual([a["category_id"] for a in merged["annotations"]], [1, 2])
        self.assertEqual(merged["categories"], categories)

    def test_does_not_mutate_inputs(self):
        categories = build_categories(METADATA, "MediumVoltagePowerLine", [])
        coco, _ = convert_mission(mission([detection("A", [SQUARE])]), categories)
        merge_missions([("d", coco), ("e", coco)])
        self.assertEqual(coco["images"][0]["file_name"], "DJI_0001.JPG-img1.jpeg")
        self.assertEqual(coco["annotations"][0]["id"], 1)


if __name__ == "__main__":
    unittest.main()
