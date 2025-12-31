# VDG Golden Fixtures

This folder contains replayable fixtures for pipeline validation.

Structure:
```
vdg_golden/
  manifest.json
  items/
  comments/
  vdg/
```

Add a new entry:
1. Drop `items/<id>.json`, `comments/<id>.json`, and `vdg/<id>.json`.
2. Append an entry to `manifest.json` with `enabled: true`.
3. Run `python3 backend/scripts/replay_vdg_golden.py --fail-on-issue`.
