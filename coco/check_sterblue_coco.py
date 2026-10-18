"""Check that a converted Sterblue export still connects end to end.

Sterblue source JSON -> JPEG on disk -> per-mission COCO -> merged COCO, and optionally -> viewer data
written by build_coco_viewer.py. Exits non-zero when anything is out of place.

Usage: check_sterblue_coco.py <export_root> [--viewer <viewer folder>]
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

WINDOWS_INVALID = re.compile(r'[<>:"\\|?*\x00-\x1f]')


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_js_payload(path: Path, pattern: str) -> dict:
    return json.loads(re.match(pattern, path.read_text(encoding="utf-8"), re.S).group(1))


def mission_dirs(root: Path) -> list[Path]:
    """Directories holding a Sterblue mission JSON (skips helper dirs such as success/)."""
    return sorted(
        p for p in root.iterdir()
        if p.is_dir() and any(not j.name.startswith("._") for j in p.glob("*.json"))
    )


def check_export(root: Path, viewer: Path | None = None) -> tuple[dict, list[str]]:
    problems: list[str] = []

    def check(ok: bool, message: str) -> None:
        if not ok:
            problems.append(message)

    merged = load_json(root / "merged.coco.json")
    merged_images = {i["file_name"]: i for i in merged["images"]}
    merged_ann_counts = Counter(a["image_id"] for a in merged["annotations"])
    index = load_js_payload(viewer / "assets/data/index.js", r"window\.VIEWER_INDEX = (.*);\s*$") if viewer else None
    viewer_missions = {m["dir"]: m for m in index["missions"]} if index else {}

    stats = {"missions": 0, "images": 0, "detections": 0}
    for mission_dir in mission_dirs(root):
        jsons = [p for p in mission_dir.glob("*.json") if not p.name.startswith("._")]
        sources = [p for p in jsons if not p.name.endswith(".coco.json")]
        cocos = [p for p in jsons if p.name.endswith(".coco.json")]
        check(len(sources) == 1 and len(cocos) == 1, f"{mission_dir.name}: {len(sources)} source / {len(cocos)} coco json")
        if not (sources and cocos):
            continue
        for path in (sources[0], cocos[0]):
            check(not WINDOWS_INVALID.search(path.name), f"Windows-invalid name: {path.name}")

        source, coco = load_json(sources[0]), load_json(cocos[0])
        stats["missions"] += 1
        source_images = source["execution"]["images"]
        check(len(source_images) == len(coco["images"]), f"{mission_dir.name}: image count differs")
        category_names = {c["id"]: c["name"] for c in coco["categories"]}
        coco_ids = {i["id"] for i in coco["images"]}
        anns_by_image: dict[int, list[dict]] = {}
        for ann in coco["annotations"]:
            check(ann["image_id"] in coco_ids, f"{mission_dir.name}: dangling image_id {ann['image_id']}")
            anns_by_image.setdefault(ann["image_id"], []).append(ann)

        viewer_mission = viewer_missions.get(mission_dir.name)
        if viewer:
            check(viewer_mission is not None or not source_images, f"{mission_dir.name}: missing from viewer")
        viewer_data = (
            load_js_payload(viewer / f"assets/data/{viewer_mission['key']}.js", r'window\.VIEWER_MISSION_LOADED\("m\d+", (.*)\);\s*$')
            if viewer_mission else None
        )
        if viewer_mission:
            check(viewer_mission["files"] == {"source": sources[0].name, "coco": cocos[0].name},
                  f"{mission_dir.name}: viewer file links are stale, rebuild the viewer")

        for number, (source_image, coco_image) in enumerate(zip(source_images, coco["images"]), start=1):
            stats["images"] += 1
            jpeg = f'{source_image["file"]["name"]}-{source_image["id"]}.jpeg'
            check((mission_dir / jpeg).is_file(), f"missing jpeg {mission_dir.name}/{jpeg}")
            check(coco_image["file_name"] == jpeg and coco_image["sterblue_image_id"] == source_image["id"]
                  and coco_image["id"] == number, f"{mission_dir.name}: COCO image {number} does not match the source")
            detections = [d for d in source_image["detections"] if not d.get("deletedAt")]
            stats["detections"] += len(detections)
            anns = anns_by_image.get(coco_image["id"], [])
            check(Counter(d["id"] for d in detections) == Counter(a["sterblue_detection_id"] for a in anns),
                  f"{jpeg}: detection ids differ from the source")
            check(Counter(d["type"]["name"] for d in detections) == Counter(category_names[a["category_id"]] for a in anns),
                  f"{jpeg}: categories differ from the source")
            merged_image = merged_images.get(f"{mission_dir.name}/{jpeg}")
            check(merged_image is not None and merged_ann_counts[merged_image["id"]] == len(anns),
                  f"{jpeg}: merged COCO does not match")
            if viewer_data:
                record = viewer_data["images"][number - 1]
                check(record["file"] == jpeg and record["sid"] == source_image["id"] and len(record["a"]) == len(anns)
                      and merged_image is not None and record.get("gid") == merged_image["id"],
                      f"{jpeg}: viewer record does not match")
                check((viewer / f"assets/img/{viewer_mission['key']}/{number:04d}.jpg").is_file(),
                      f"{jpeg}: viewer image missing")

    check(len(merged["images"]) == stats["images"] and len(merged["annotations"]) == stats["detections"],
          "merged COCO totals differ from the sources")
    check(all(n == 1 for n in Counter(a["sterblue_detection_id"] for a in merged["annotations"]).values()),
          "merged COCO has duplicate detection ids")
    return stats, problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("export_root", type=Path)
    parser.add_argument("--viewer", type=Path, help="viewer folder built by build_coco_viewer.py")
    args = parser.parse_args()

    stats, problems = check_export(args.export_root, args.viewer)
    print(f'checked {stats["missions"]} missions, {stats["images"]} images, {stats["detections"]} detections')
    print(f"problems: {len(problems)}")
    for problem in problems[:50]:
        print("  " + problem)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
