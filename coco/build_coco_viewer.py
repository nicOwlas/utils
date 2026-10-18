"""Build an offline, double-click HTML viewer for a merged COCO file.

Images are grouped by the first path component of their file_name (the mission directory).
Output (portable folder, short paths, no server needed):
  <out>/Ouvrir la visionneuse.html
  <out>/assets/data/index.js          categories, missions, per-image category ids
  <out>/assets/data/mNN.js            polygons of one mission, loaded on demand
  <out>/assets/img/mNN/NNNN.jpg       half-resolution copies
  <out>/assets/thumb/mNN/NNNN.jpg     thumbnails
"""

import argparse
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from itertools import chain
from pathlib import Path

GROUPS = [
    ("vegetation", "Végétation", "#2f9e44", ("végétation", "vegetation")),
    ("inventory", "Inventaire (Recensement)", "#1c7ed6", ("recensement", "equipment/")),
    ("line", "Défauts de ligne", "#ae3ec9", ("/ligne",)),
    ("device", "État des appareils", "#0c8599", ("/appareil",)),
    ("support", "Défauts de support / poteau", "#e03131", ("support", "pylon")),
    ("equipment", "Défauts d'équipement", "#f08c00", ("equipement", "etriers", "armement", "attache")),
    ("other", "Autre", "#868e96", ("",)),
]

TEMPLATE = Path(__file__).with_name("viewer_template.html")
HTML_NAME = "Ouvrir la visionneuse.html"


def category_group(name: str) -> str:
    lowered = name.lower()
    return next(key for key, _, _, needles in GROUPS if any(n in lowered for n in needles))


def mission_label(mission_dir: str) -> tuple[str, str]:
    """'2020-11-19-ORES_Namur - Zone Buzin-ckhonkm8605uj...' -> ('2020-11-19', 'ORES_Namur - Zone Buzin')."""
    match = re.match(r"(\d{4}-\d{2}-\d{2})-(.*)-c[a-z0-9]{24}$", mission_dir)
    return (match.group(1), match.group(2)) if match else ("", mission_dir)


def rounded(polygon: list[float]) -> list[int]:
    return [round(v) for v in polygon]


def plan(coco: dict) -> list[dict]:
    """Group images by mission directory and assign short keys/paths."""
    by_mission = defaultdict(list)
    for image in coco["images"]:
        by_mission[image["file_name"].split("/", 1)[0]].append(image)
    missions = sorted(by_mission.items())
    return [
        {
            "key": f"m{m:02d}",
            "dir": mission_dir,
            "images": [
                {**image, "short": f"{m:02d}/{i:04d}.jpg"} for i, image in enumerate(images, start=1)
            ],
        }
        for m, (mission_dir, images) in enumerate(missions, start=1)
    ]


def source_code(category_id: int, is_ai: bool) -> int:
    """Pack (category, AI-or-human) into one int for the index: category * 2 + is_ai."""
    return category_id * 2 + int(is_ai)


def build_data(coco: dict, missions: list[dict], ai_authors: set[str]) -> tuple[dict, dict]:
    anns_by_image = defaultdict(list)
    for ann in coco["annotations"]:
        anns_by_image[ann["image_id"]].append(ann)
    authors = sorted({a.get("sterblue_author") or "" for a in coco["annotations"]})
    author_index = {a: i for i, a in enumerate(authors)}
    ai_indices = {author_index[a] for a in authors if a in ai_authors}

    def image_record(image: dict) -> dict:
        anns = anns_by_image[image["id"]]
        return {
            "w": image["width"],
            "h": image["height"],
            "name": Path(image["file_name"]).name.split(".")[0],
            "file": Path(image["file_name"]).name,
            "sid": image.get("sterblue_image_id"),
            "date": image.get("date_captured", ""),
            "a": [
                [a["category_id"], author_index[a.get("sterblue_author") or ""], [rounded(p) for p in a["segmentation"]]]
                for a in anns
            ],
        }

    per_mission = {
        m["key"]: {"images": [image_record(img) for img in m["images"]]} for m in missions
    }
    index = {
        "groups": [{"key": k, "label": label, "color": color} for k, label, color, _ in GROUPS],
        "categories": [
            {"id": c["id"], "name": c["name"], "group": category_group(c["name"])} for c in coco["categories"]
        ],
        "authors": authors,
        "aiAuthors": sorted(ai_indices),
        "missions": [
            {
                "key": m["key"],
                "date": mission_label(m["dir"])[0],
                "name": mission_label(m["dir"])[1],
                "images": [
                    sorted({source_code(a[0], a[1] in ai_indices) for a in rec["a"]}) + [len(rec["a"])]
                    for rec in per_mission[m["key"]]["images"]
                ],
            }
            for m in missions
        ],
    }
    return index, per_mission


def mission_files(image_root: Path, mission_dir: str) -> dict:
    """Original annotation files of one mission: the source JSON and the COCO one written next to it."""
    jsons = sorted(p.name for p in (image_root / mission_dir).glob("*.json") if not p.name.startswith("._"))
    return {
        "coco": next((n for n in jsons if n.endswith(".coco.json")), None),
        "source": next((n for n in jsons if not n.endswith(".coco.json")), None),
    }


def relative_url(target: Path, start: Path) -> str:
    return Path(os.path.relpath(target.resolve(), start.resolve())).as_posix()


def write_js(path: Path, statement: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(statement, encoding="utf-8")


def resize_one(job: tuple[str, str, str, int, int]) -> str | None:
    from PIL import Image

    src, img_out, thumb_out, width, height = job
    if Path(img_out).exists() and Path(thumb_out).exists():
        return None
    with Image.open(src) as im:
        if im.size != (width, height):
            return f"size mismatch {src}: {im.size} vs {(width, height)}"
        im.draft("RGB", (width // 2, height // 2))
        half = im.convert("RGB").resize((width // 2, height // 2))
    Path(img_out).parent.mkdir(parents=True, exist_ok=True)
    Path(thumb_out).parent.mkdir(parents=True, exist_ok=True)
    half.save(img_out, "JPEG", quality=82, progressive=True, optimize=True)
    half.thumbnail((420, 420))
    half.save(thumb_out, "JPEG", quality=78, optimize=True)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("coco", type=Path, help="merged COCO file")
    parser.add_argument("image_root", type=Path, help="directory file_name paths are relative to")
    parser.add_argument("out", type=Path, help="viewer output folder")
    parser.add_argument("--title", default="Annotations viewer")
    parser.add_argument("--ai-author", action="append", default=["Sterblue"],
                        help="author name whose annotations are automatic (repeatable)")
    parser.add_argument("--no-images", action="store_true", help="only (re)write HTML and data")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    coco = json.loads(args.coco.read_text())
    missions = [m for m in plan(coco) if m["images"]]
    index, per_mission = build_data(coco, missions, set(args.ai_author))
    index["title"] = args.title
    args.out.mkdir(parents=True, exist_ok=True)
    index["originals"] = {
        "root": relative_url(args.image_root, args.out),
        "rootName": args.image_root.resolve().name,
        "merged": relative_url(args.coco, args.out),
    }
    for entry, mission in zip(index["missions"], missions):
        entry["dir"] = mission["dir"]
        entry["files"] = mission_files(args.image_root, mission["dir"])

    data_dir = args.out / "assets" / "data"
    write_js(data_dir / "index.js", f"window.VIEWER_INDEX = {json.dumps(index, ensure_ascii=False, separators=(',', ':'))};\n")
    for key, data in per_mission.items():
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        write_js(data_dir / f"{key}.js", f"window.VIEWER_MISSION_LOADED({json.dumps(key)}, {payload});\n")
    html = TEMPLATE.read_text(encoding="utf-8").replace("{{TITLE}}", args.title)
    (args.out / HTML_NAME).write_text(html, encoding="utf-8")
    print(f"data written: {len(missions)} missions, {sum(len(m['images']) for m in missions)} images")

    if args.no_images:
        return
    jobs = [
        (
            str(args.image_root / img["file_name"]),
            str(args.out / "assets" / "img" / f"m{img['short']}"),
            str(args.out / "assets" / "thumb" / f"m{img['short']}"),
            img["width"],
            img["height"],
        )
        for img in chain.from_iterable(m["images"] for m in missions)
    ]
    with ProcessPoolExecutor(args.workers) as pool:
        for done, error in enumerate(pool.map(resize_one, jobs, chunksize=8), start=1):
            if error:
                print(error)
            if done % 250 == 0 or done == len(jobs):
                print(f"images {done}/{len(jobs)}", flush=True)


if __name__ == "__main__":
    main()
