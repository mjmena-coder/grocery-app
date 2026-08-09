# Grocery App

Turns printed cookbook recipes into aisle-ordered grocery lists for
King Soopers and Whole Foods, replacing manual weekend list-building.

## Architecture

- **Pi 5** (`backend/`): always-on API service + SQLite database.
  Reachable on the home network only, no public exposure.
- **`capture/`**: on-demand recipe-photo OCR via Apple Vision
  (`VNRecognizeTextRequest`). Runs on a Mac or iPhone (Shortcuts),
  never on the Pi -- macOS/iOS only, not part of CI. See
  `capture/README.md`.
- **Frontend**: PWA, not yet started. Will be reachable from any
  device (iPhone, Pixel, laptop) regardless of which device did OCR
  capture.

Full design rationale and phasing lives in `grocery-app-build-plan.md`
and `build-plan-addendum.md` (OCR engine pivot), tracked outside this
repo.

## Status

Phase 0 (schema + CI) complete. Phase 1 (recipe parsing) in progress --
OCR engine finalized (Apple Vision), reading-order validation and
ingredient/directions segmentation still being built out.

## Setup

```bash
pip install -r requirements.txt
pytest
```

For the OCR capture step, see `capture/README.md` (separate
macOS-only dependencies).