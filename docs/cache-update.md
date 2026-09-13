# Cache Update Workflow

Run this after every qualifying session and again after the race itself.

---

## After qualifying

```bash
python scripts/rebuild_cache.py --stage2
git add data/
git commit -m "Update 2026 cache post-{Race} GP qualifying (R{N})"
git push
```

## After the race

```bash
python scripts/rebuild_cache.py --stage2
git add data/
git commit -m "Update 2026 cache post-{Race} GP (R{N})"
git push
```

Render detects the push, rebuilds the Docker image with the new pkl files baked in, and redeploys automatically. First request after redeploy is warm — no live FastF1 fetch needed.

---

## What the script does

`rebuild_cache.py --stage2` refreshes:

| Data | Source | Purpose |
|---|---|---|
| 2026 race history (all completed rounds) | FastF1 | Stage 2 driver/team form features |
| Qualifying session (each completed round) | FastF1 | Gap-to-pole feature |
| FP2 / Sprint laps (each completed round) | FastF1 | Race pace proxy feature |

The pkl filenames embed the completed-round count (e.g. `history_2026_r14_v3.pkl`), so adding a new race automatically invalidates the previous file — no manual cleanup needed.

---

## Force re-download (if FastF1 served stale data)

```bash
python scripts/rebuild_cache.py --stage2 --refresh
```

---

## Full rebuild (start of a new season or after a major model change)

```bash
python scripts/rebuild_cache.py          # Stage 1 (2024+2025) + Stage 2 (current)
git add data/
git commit -m "Full cache rebuild for {year} season"
git push
```

Stage 1 (historical data from 2024–2025) rarely changes and can be skipped most of the time — use `--stage2` for routine post-race updates.
