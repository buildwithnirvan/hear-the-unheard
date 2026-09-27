# ISL Training Data

## Decision

**Primary dataset:** *Indian Sign Language words with Landmarks* (Kaggle,
uploaded by Kaushik Y.H., `kaushikyh/indian-sign-language-words-with-landmarks`).

- License: **CC BY-SA 4.0** — usable, requires attribution and share-alike
  if the dataset itself is redistributed. (Not a lawyer, not legal advice —
  read the license yourself before any commercial deployment.)
- ~50MB, hand + holistic landmarks already extracted — matches our
  landmark-first architecture directly.
- Derived from **INCLUDE** (Sridhar, Ganesan, Kumar & Khapra, 2020,
  IIT Madras/AI4Bharat) — the real, published, peer-reviewed ISL dataset,
  recorded with deaf students at St. Louis School for the Deaf, Adyar,
  Chennai. DOI: 10.1145/3394171.3413528. Currently covers 80 of INCLUDE's
  263 word signs.
- **Full INCLUDE** (263 signs, 4,287 raw videos, 56.8GB) is hosted on
  Zenodo (record 4010759) and Hugging Face (`ai4bharat/INCLUDE`) for
  future expansion once the pipeline is proven on the smaller set.

## Why not download it automatically

This container's network egress is restricted to PyPI/npm/GitHub. Kaggle
requires both network access we don't have here and an authenticated API
token. The person running this project needs to download the dataset and
provide it — see the top-level conversation for the current status of
that handoff.

## How to plug it in once you have the zip

1. Extract it into `ml/datasets/raw/kaggle_isl_landmarks/`.
2. Run `python ml/preprocessing/import_kaggle_landmarks.py` (see that
   script's docstring — it's written defensively because the exact
   internal file layout wasn't verifiable without downloading the file,
   so it inspects the actual structure first and tells you what it found
   before assuming a schema).
3. That script will populate `ml/datasets/landmarks/` in our internal
   format (matching `FRAME_FEATURE_DIM` in
   `ml/preprocessing/landmark_extractor.py`) and register a `Dataset` row
   via the backend so `/api/v1/vocabulary/stats/summary` and
   `/api/v1/model/status` reflect real coverage.
4. From there, `ml/training/train.py` trains the actual sequence model
   (Phase 3) — not written yet; it's the next step once real data is on
   disk and its schema is confirmed.

## Ground rule

No synthetic/fabricated landmark sequences get treated as "training data"
anywhere in this pipeline (§32/§33 of the project spec). Synthetic data
in `tests/` is clearly scoped to testing segmentation *logic*, never fed
to a model as if it were real signing.
