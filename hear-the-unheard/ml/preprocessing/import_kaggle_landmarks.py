"""
import_kaggle_landmarks.py

Imports the "Indian Sign Language words with Landmarks" Kaggle dataset
(kaushikyh/indian-sign-language-words-with-landmarks) into our internal
landmark format.

WHY THIS SCRIPT IS WRITTEN THE WAY IT IS:
I have not been able to download or open this dataset myself — Kaggle
isn't reachable from this environment. Its public description says it
contains hand + holistic landmarks derived from the INCLUDE dataset, but
I don't have ground truth on the exact file layout (per-video CSV? one
big parquet? .npy arrays? which landmark indices/ordering?). Rather than
guess a schema and silently produce wrong training data, this script's
first job is to INSPECT whatever you extracted and print what it
actually finds. Only run the conversion step after confirming the
printed structure matches what convert_one_file() expects — and edit
convert_one_file() if it doesn't. Do not skip the inspection step.

Usage:
    python import_kaggle_landmarks.py inspect  <path-to-extracted-dataset>
    python import_kaggle_landmarks.py convert   <path-to-extracted-dataset>
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np


def inspect(root: Path, max_examples_per_ext: int = 2) -> None:
    """
    Walks the extracted dataset and reports:
      - directory depth / apparent class structure (folder-per-word?)
      - file extension counts
      - a peek at up to `max_examples_per_ext` files of each extension
    Prints everything — makes no assumptions, writes nothing to disk.
    """
    if not root.exists():
        print(f"ERROR: {root} does not exist. Extract the Kaggle zip there first.")
        sys.exit(1)

    ext_counter: Counter[str] = Counter()
    all_files = []
    for p in root.rglob("*"):
        if p.is_file():
            ext_counter[p.suffix.lower()] += 1
            all_files.append(p)

    print(f"Scanned {root}")
    print(f"Total files: {len(all_files)}")
    print("Extension breakdown:")
    for ext, count in ext_counter.most_common():
        print(f"  {ext or '(no extension)'}: {count}")

    top_level_dirs = sorted(d.name for d in root.iterdir() if d.is_dir())
    print(f"\nTop-level directories ({len(top_level_dirs)}): {top_level_dirs[:30]}"
          + (" ..." if len(top_level_dirs) > 30 else ""))
    print("(If these are word-sign names like 'HELLO', 'WATER' etc., the "
          "dataset is folder-per-class — map folder name -> our vocabulary "
          "gloss in convert_one_file() / SIGN_ID_MAP below.)")

    shown_per_ext: Counter[str] = Counter()
    print("\n--- File previews ---")
    for f in all_files:
        ext = f.suffix.lower()
        if shown_per_ext[ext] >= max_examples_per_ext:
            continue
        shown_per_ext[ext] += 1
        print(f"\n[{f.relative_to(root)}]  ({f.stat().st_size} bytes)")
        try:
            if ext == ".csv":
                with open(f) as fh:
                    lines = [next(fh) for _ in range(3)]
                print("  first lines:", *[l.strip() for l in lines], sep="\n    ")
            elif ext == ".json":
                data = json.loads(f.read_text())
                preview = json.dumps(data, indent=2)[:500]
                print("  json preview:", preview)
            elif ext == ".npy":
                arr = np.load(f, allow_pickle=True)
                print(f"  numpy array: shape={arr.shape}, dtype={arr.dtype}")
            elif ext in (".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mov"):
                print("  (media file — size only, not previewed)")
            else:
                print("  (unrecognized extension — open manually)")
        except (StopIteration, UnicodeDecodeError) as e:
            print(f"  could not preview: {e}")

    print("\n--- Next step ---")
    print("Compare the structure above against convert_one_file() in this "
          "file. Edit convert_one_file() and SIGN_ID_MAP to match reality, "
          "THEN run the 'convert' command. Do not run 'convert' against an "
          "assumed schema.")


# --- Below this line: EDIT AFTER RUNNING `inspect`, not before. -----------------

def convert_one_file(path: Path):
    """
    PLACEHOLDER — not yet implemented against a confirmed schema.
    Once `inspect` shows the real file layout, this function should parse
    one sample file and return a list of per-frame feature vectors in the
    same layout as LandmarkExtractor.to_feature_vector() (see
    ml/preprocessing/landmark_extractor.py) so downstream training code
    doesn't need two different feature formats.
    """
    raise NotImplementedError(
        "convert_one_file() has not been implemented yet — it depends on "
        "the actual file schema, which requires running `inspect` against "
        "the real downloaded dataset first. See this file's module "
        "docstring."
    )


def convert(root: Path, output_dir: Path):
    raise NotImplementedError(
        "Run `inspect` first, implement convert_one_file() against the "
        "confirmed schema, then this function can walk the dataset and "
        "call it per sample."
    )


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("inspect", "convert"):
        print(__doc__)
        sys.exit(1)

    command, dataset_path = sys.argv[1], Path(sys.argv[2])

    if command == "inspect":
        inspect(dataset_path)
    else:
        convert(dataset_path, Path(__file__).parent.parent / "datasets" / "landmarks")
