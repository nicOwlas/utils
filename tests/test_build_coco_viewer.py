import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "coco"))

from build_coco_viewer import build_data, category_group, mission_files, mission_label, plan, relative_url, source_code


def coco_fixture():
    return {
        "categories": [
            {"id": 1, "name": "042-Chaine d'arrêt 3 plateaux/Recensement"},
            {"id": 2, "name": "053-Conducteur/Contact avec la végétation"},
        ],
        "images": [
            {"id": 1, "file_name": "2020-11-19-Zone B-ckhonkm8605uj0716h5zkte8e/b1.jpeg", "width": 100, "height": 50,
             "date_captured": "2020-05-09T17:05:52", "sterblue_image_id": "sb1"},
            {"id": 2, "file_name": "2020-01-27-Zone A-ck5wj28vk4ju0090407afrsb0/a1.jpeg", "width": 100, "height": 50,
             "date_captured": "", "sterblue_image_id": "sa1"},
        ],
        "annotations": [
            {"id": 1, "image_id": 1, "category_id": 1, "segmentation": [[1.4, 2.6, 3, 4, 5, 6]], "sterblue_author": "Sterblue"},
            {"id": 2, "image_id": 1, "category_id": 2, "segmentation": [[1, 2, 3, 4, 5, 6]], "sterblue_author": "isahit18"},
        ],
    }


class TestCategoryGroup(unittest.TestCase):
    def test_groups_by_keyword_with_vegetation_first(self):
        self.assertEqual(category_group("053-Conducteur/Contact avec la végétation"), "vegetation")
        self.assertEqual(category_group("Recensement/Support-Beton"), "inventory")
        self.assertEqual(category_group("012-Béton détérioré/Support"), "support")
        self.assertEqual(category_group("Other defect"), "other")


class TestMissionLabel(unittest.TestCase):
    def test_splits_date_and_name_and_drops_id(self):
        self.assertEqual(mission_label("2020-11-19-Zone B-ckhonkm8605uj0716h5zkte8e"), ("2020-11-19", "Zone B"))

    def test_falls_back_to_dir_name(self):
        self.assertEqual(mission_label("free name"), ("", "free name"))


class TestPlan(unittest.TestCase):
    def test_groups_by_mission_dir_sorted_with_short_paths(self):
        missions = plan(coco_fixture())
        self.assertEqual([m["key"] for m in missions], ["m01", "m02"])
        self.assertEqual(missions[0]["dir"], "2020-01-27-Zone A-ck5wj28vk4ju0090407afrsb0")
        self.assertEqual(missions[1]["images"][0]["short"], "02/0001.jpg")


class TestBuildData(unittest.TestCase):
    def test_index_encodes_category_and_source_per_image(self):
        coco = coco_fixture()
        index, per_mission = build_data(coco, plan(coco), {"Sterblue"})
        zone_b = index["missions"][1]
        self.assertEqual(zone_b["images"], [[source_code(1, True), source_code(2, False), 2]])
        self.assertEqual([index["authors"][i] for i in index["aiAuthors"]], ["Sterblue"])
        self.assertEqual(index["missions"][0]["images"], [[0]])

    def test_mission_data_keeps_file_ids_and_rounded_polygons(self):
        coco = coco_fixture()
        _, per_mission = build_data(coco, plan(coco), {"Sterblue"})
        record = per_mission["m02"]["images"][0]
        self.assertEqual((record["file"], record["sid"], record["gid"], record["w"], record["h"]), ("b1.jpeg", "sb1", 1, 100, 50))
        self.assertEqual(record["a"][0][2], [[1, 3, 3, 4, 5, 6]])


class TestOriginalFiles(unittest.TestCase):
    def test_mission_files_separates_source_and_coco_and_skips_apple_double(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission = Path(tmp) / "m"
            mission.mkdir()
            for name in ["m.json", "m.coco.json", "._m.json"]:
                (mission / name).write_text("{}")
            self.assertEqual(mission_files(Path(tmp), "m"), {"source": "m.json", "coco": "m.coco.json"})

    def test_relative_url_uses_forward_slashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            export, viewer = Path(tmp) / "export", Path(tmp) / "viewer"
            self.assertEqual(relative_url(export / "merged.coco.json", viewer), "../export/merged.coco.json")


if __name__ == "__main__":
    unittest.main()
