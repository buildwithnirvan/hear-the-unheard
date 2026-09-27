# Build context is the REPO ROOT (see docker-compose.yml's `context: .`),
# not backend/ — the backend imports directly from ../ml/preprocessing and
# ../ml/training (see e.g. backend/app/ml/vision/isl_classifier.py), so
# both directories need to land in the image at the same relative layout
# they have in the repo.
#
# NOT YET RUN AGAINST A REAL DOCKER DAEMON — this environment has no
# docker available to verify it (see docs/STATUS.md). Written carefully
# from the actual requirements.txt / app structure, but treat the first
# `docker compose up` as the real test, the same honesty standard as
# everything else in this project.
FROM python:3.12-slim

# opencv-python-headless still links against a few system libs at import
# time even in headless mode (font/codec support) — without these,
# `import cv2` fails inside a slim image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY ml ./ml

WORKDIR /app/backend
ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Seeds/model-registration are idempotent (see scripts/) — run them before
# the server starts so a fresh container comes up with real vocabulary and
# the trained model already active, matching what was verified manually
# throughout development.
CMD sh -c "python scripts/seed_vocabulary.py && python scripts/register_trained_model.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
