"""Convert a Sterblue organisation export to one COCO annotation file per mission, plus a merged one.

Usage: transform_sterblue_to_coco.py <export_root>
  writes <mission dir>/<mission>.coco.json and <export_root>/merged.coco.json

Fixes over the previous single-mission version of this script:
* categories = anomalyLevelMappings + every detection type actually used in the export,
  with ids shared across missions (old script emitted category_id -1 for unmapped types)
* all polygon rings are kept as separate COCO polygons (old script kept only ring 0)
* y is negated (Sterblue y points up) and coordinates are clipped to the image
  (old script used abs(), which mirrors the few points above the top edge)
* area is the polygon area, not the bbox area
* degenerate polygons (< 3 points or zero area after clipping) are dropped and counted
* Sterblue provenance (detection id, author, level) is kept on each annotation
"""

import argparse
import json
import sys
from functools import reduce
from itertools import accumulate, chain
from pathlib import Path

STRUCTURE_TYPE_BY_MISSION_TYPE = {
    "InspectWindTurbine": "WindTurbine",
    "InspectPowerLineHighVoltagePylon": "HighVoltagePowerLine",
    "InspectPowerLineMediumVoltagePylon": "MediumVoltagePowerLine",
    "InspectCoolingTower": "CoolingTower",
    "InspectSolarFarm": "SolarFarm",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def mission_files(root: Path) -> list[Path]:
    return sorted(
        p
        for p in root.glob("*/*.json")
        if not p.name.startswith("._") and not p.name.endswith(".coco.json")
    )


def detection_types(mission: dict) -> list[str]:
    return [
        det["type"]["name"]
        for image in mission["execution"]["images"]
        for det in image["detections"]
    ]


def build_categories(metadata: dict, structure_type: str, used_types: list[str]) -> list[dict]:
    mapped = [
        a["name"]
        for m in metadata["anomalyLevelMappings"]
        if m["structureType"] == structure_type
        for a in m["anomalyTypes"]
    ]
    mapped_unique = list(dict.fromkeys(mapped))
    extras = sorted(set(used_types) - set(mapped_unique))
    return [
        {"id": i, "name": name, "supercategory": "", "in_anomaly_mapping": name in set(mapped_unique)}
        for i, name in enumerate(mapped_unique + extras, start=1)
    ]


def clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def to_image_coords(ring: list[list[float]], width: int, height: int) -> list[tuple[float, float]]:
    return [(clip(x, 0, width), clip(-y, 0, height)) for x, y in ring]


def ring_area(ring: list[tuple[float, float]]) -> float:
    pairs = zip(ring, ring[1:] + ring[:1])
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in pairs)) / 2


def valid_ring(ring: list[tuple[float, float]]) -> bool:
    return len(set(ring)) >= 3 and ring_area(ring) > 0


def to_annotation(det: dict, image_id: int, width: int, height: int, category_ids: dict) -> dict | None:
    rings = [to_image_coords(r, width, height) for r in det["geometry"]["geojson"]["coordinates"]]
    rings = [r for r in rings if valid_ring(r)]
    if not rings:
        return None
    xs, ys = zip(*chain.from_iterable(rings))
    xmin, ymin = min(xs), min(ys)
    return {
        "image_id": image_id,
        "category_id": category_ids[det["type"]["name"]],
        "segmentation": [list(chain.from_iterable(r)) for r in rings],
        "area": sum(ring_area(r) for r in rings),
        "bbox": [xmin, ymin, max(xs) - xmin, max(ys) - ymin],
        "iscrowd": 0,
        "sterblue_detection_id": det["id"],
        "sterblue_author": (det.get("author") or {}).get("name"),
        "sterblue_level": det.get("level"),
    }


def to_image(image: dict, image_id: int) -> dict:
    return {
        "id": image_id,
        "file_name": f'{image["file"]["name"]}-{image["id"]}.jpeg',
        "coco_url": "",
        "date_captured": image["capturedAt"],
        "height": image["height"],
        "width": image["width"],
        "license": 0,
        "sterblue_image_id": image["id"],
    }


def convert_mission(mission: dict, categories: list[dict]) -> tuple[dict, int]:
    category_ids = {c["name"]: c["id"] for c in categories}
    images = list(enumerate(mission["execution"]["images"], start=1))
    candidates = [
        to_annotation(det, image_id, image["width"], image["height"], category_ids)
        for image_id, image in images
        for det in image["detections"]
        if not det.get("deletedAt")
    ]
    kept = [a for a in candidates if a is not None]
    coco = {
        "info": {
            "contributor": "Sterblue export",
            "date_created": mission["createdAt"],
            "description": f'{mission["name"]} ({mission["id"]})',
            "url": "",
            "version": "",
            "year": mission["createdAt"][:4],
        },
        "licenses": [{"name": "", "id": 0, "url": ""}],
        "categories": categories,
        "images": [to_image(image, image_id) for image_id, image in images],
        "annotations": [{"id": i, **a} for i, a in enumerate(kept, start=1)],
    }
    return coco, len(candidates) - len(kept)


def merge_missions(cocos: list[tuple[str, dict]]) -> dict:
    """Merge per-mission COCO files that share categories into one.

    Image and annotation ids are renumbered globally, and each file_name is prefixed with its
    mission directory so the merged file resolves images from the export root.
    """
    offsets = list(
        accumulate(
            ((len(c["images"]), len(c["annotations"])) for _, c in cocos[:-1]),
            lambda acc, n: (acc[0] + n[0], acc[1] + n[1]),
            initial=(0, 0),
        )
    )
    images = [
        {
            **image,
            "id": image["id"] + img_offset,
            "file_name": f'{mission_dir}/{image["file_name"]}',
            "sterblue_mission": coco["info"]["description"],
        }
        for (mission_dir, coco), (img_offset, _) in zip(cocos, offsets)
        for image in coco["images"]
    ]
    annotations = [
        {**ann, "id": ann["id"] + ann_offset, "image_id": ann["image_id"] + img_offset}
        for (_, coco), (img_offset, ann_offset) in zip(cocos, offsets)
        for ann in coco["annotations"]
    ]
    first = cocos[0][1]
    return {
        "info": {**first["info"], "description": f"{len(cocos)} merged Sterblue missions"},
        "licenses": first["licenses"],
        "categories": first["categories"],
        "images": images,
        "annotations": annotations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("export_root", type=Path, help="directory holding metadata.json and one sub-directory per mission")
    parser.add_argument("--merged-name", default="merged.coco.json", help="merged COCO file written to export_root")
    parser.add_argument("--dry-run", action="store_true", help="convert and report, write nothing")
    args = parser.parse_args()

    metadata = load_json(args.export_root / "metadata.json")
    paths = mission_files(args.export_root)
    missions = [(p, load_json(p)) for p in paths]

    mission_types = {m["type"] for _, m in missions}
    unknown = mission_types - STRUCTURE_TYPE_BY_MISSION_TYPE.keys()
    if len(mission_types) != 1 or unknown:
        sys.exit(f"expected a single known mission type, got {sorted(mission_types)}")
    structure_type = STRUCTURE_TYPE_BY_MISSION_TYPE[mission_types.pop()]

    used = reduce(lambda acc, m: acc + detection_types(m[1]), missions, [])
    categories = build_categories(metadata, structure_type, used)

    converted = [(path, *convert_mission(mission, categories)) for path, mission in missions]
    for path, coco, dropped in converted:
        out = path.with_name(path.stem + ".coco.json")
        if not args.dry_run:
            out.write_text(json.dumps(coco, ensure_ascii=False, indent=2))
        print(f'{len(coco["images"]):5d} img {len(coco["annotations"]):6d} ann {dropped:3d} dropped  {out.relative_to(args.export_root)}')

    merged = merge_missions([(path.parent.name, coco) for path, coco, _ in converted])
    merged_out = args.export_root / args.merged_name
    if not args.dry_run:
        merged_out.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
    print(f'{len(merged["images"]):5d} img {len(merged["annotations"]):6d} ann merged   {merged_out.name}')


if __name__ == "__main__":
    main()
