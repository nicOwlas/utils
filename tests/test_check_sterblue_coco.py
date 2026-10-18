import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "coco"))

from check_sterblue_coco import check_export
from transform_sterblue_to_coco import build_categories, convert_mission, merge_missions

MISSION_DIR = "2020-11-19-Zone-ckhonkm8605uj0716h5zkte8e"


def sterblue_mission():
    return {
        "id": "ckhonkm8605uj0716h5zkte8e",
        "name": "Zone",
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
                    "detections": [
                        {
                            "id": "d1",
                            "deletedAt": None,
                            "type": {"name": "A"},
                            "geometry": {"geojson": {"coordinates": [[[10, -10], [20, -10], [20, -20], [10, -10]]]}},
                            "author": {"name": "Sterblue"},
                            "level": 0.5,
                        }
                    ],
                }
            ]
        },
    }


def write_export(root: Path) -> Path:
    """Write a one-mission export with its COCO outputs, as transform_sterblue_to_coco.py would."""
    mission = sterblue_mission()
    mission_dir = root / MISSION_DIR
    mission_dir.mkdir(parents=True)
    (mission_dir / f"{MISSION_DIR}.json").write_text(json.dumps(mission))
    (mission_dir / "DJI_0001.JPG-img1.jpeg").write_bytes(b"jpeg")
    metadata = {"anomalyLevelMappings": [{"structureType": "MediumVoltagePowerLine", "anomalyTypes": [{"name": "A"}]}]}
    coco, _ = convert_mission(mission, build_categories(metadata, "MediumVoltagePowerLine", ["A"]))
    (mission_dir / f"{MISSION_DIR}.coco.json").write_text(json.dumps(coco))
    (root / "merged.coco.json").write_text(json.dumps(merge_missions([(MISSION_DIR, coco)])))
    return mission_dir


class TestCheckExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.mission_dir = write_export(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_export_has_no_problems(self):
        stats, problems = check_export(self.root)
        self.assertEqual(problems, [])
        self.assertEqual(stats, {"missions": 1, "images": 1, "detections": 1})

    def test_reports_missing_jpeg(self):
        (self.mission_dir / "DJI_0001.JPG-img1.jpeg").unlink()
        _, problems = check_export(self.root)
        self.assertTrue(any("missing jpeg" in p for p in problems), problems)

    def test_reports_windows_invalid_file_name(self):
        source = self.mission_dir / f"{MISSION_DIR}.json"
        source.rename(self.mission_dir / "Zone?.json")
        _, problems = check_export(self.root)
        self.assertTrue(any("Windows-invalid" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
