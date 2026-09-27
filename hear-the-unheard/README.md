# Hear the Unheard

Breaking communication barriers by translating between Indian Sign
Language, speech, and text.

**Read `docs/STATUS.md` first.** It's an honest, current account of what's
real vs. stubbed vs. blocked, and it's more likely to be up to date than
this paragraph is.

## Quick start (backend)

Needs a MongoDB instance — no other database is used anywhere in this
project. Easiest local option: `docker run -d -p 27017:27017 mongo:7`, or
install MongoDB Community Edition yourself.

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # defaults to mongodb://localhost:27017
ENVIRONMENT=development python -m uvicorn app.main:app --reload
```

Then:
- `GET /health`
- `GET /api/v1/vocabulary` — browse the seeded ISL vocabulary
- `GET /api/v1/model/status` — honest report on whether recognition is live

Seed the vocabulary and load the trained model (both idempotent):
```bash
python scripts/seed_vocabulary.py
python scripts/register_trained_model.py
```

Run the verified CV/translation pipeline tests:
```bash
python ../tests/test_landmark_extractor.py
python ../tests/test_sign_segmenter.py
python ../tests/test_isl_to_text.py
```

## Quick start (frontend)

```bash
cd frontend
npm install
cp .env.local.example .env.local   # points at localhost:8000 by default
npm run dev
```

Open http://localhost:3000 — start the backend first so `/translate` can
actually reach `/ws/recognize` and `/api/v1/translate`. Needs a real
browser with camera access; hasn't been through an actual click-through
test yet (no browser in the environment this was built in) — see
`docs/STATUS.md` for exactly what was and wasn't verified.

## Or: everything at once with Docker

```bash
cp .env.example .env   # optional — has working dev-only defaults
docker compose up --build
```

Brings up MongoDB, the backend (auto-seeded), and the frontend together.
**Unverified** — this environment has no docker daemon, so this has never
actually been run. It's written carefully against the real app structure;
report back what breaks on your first `docker compose up`.

## Project layout

```
hear-the-unheard/
  backend/     FastAPI app — API, MongoDB document schemas, auth, ML services
  frontend/    Next.js app — landing page, live translator, about
  ml/
    preprocessing/   landmark extraction + sign segmentation (real, tested)
    training/        model training pipeline (real — see ml/models/)
    models/           the actual trained classifier + its model card
    datasets/        raw/processed/train/validation/test/landmarks/vocabulary
  docs/        architecture + honest status tracking
  scripts/     one-off dev/admin scripts (seed vocabulary, register model)
  tests/       real tests, run them, don't trust a green check you haven't seen
```

## Why MongoDB, and why mediapipe==0.10.13 specifically

MongoDB: used exclusively per explicit instruction — no SQL database
anywhere in this stack. Documents use plain string UUIDs as `_id` rather
than MongoDB's native ObjectId, so ids stay simple strings everywhere
they cross an API boundary (JWTs, JSON responses) without a custom
encoder. See `backend/app/database/mongo.py`'s docstring.

mediapipe: see the docstring at the top of
`ml/preprocessing/landmark_extractor.py` — short version, it's the last
release that bundles the actual model weights in the pip wheel, so
hand/pose detection works with zero network access at runtime. Don't
casually bump this version.
