# Pipeline

`reconstruct.py` implements the Phase-0 path: session photos → camera poses →
scene → novel views. Today the pose step is real (COLMAP sparse mapper); the
scene/render step is the next build.

## Prerequisites

- `colmap` on PATH (pose estimation). Check: `colmap -h`.
- `ffmpeg` on PATH (used once video ingest lands).
- Python 3.9+ (stdlib only for the scaffold).

## Run

```bash
# capture photos first via /capture/, then:
python3 pipeline/reconstruct.py --session data/<session-id>
# poses land in data/<session-id>/work/sparse/
```

With fewer than ~8 overlapping photos of a textured scene, expect COLMAP to
register only some (or none) of the images — that is normal signal, not a bug:
add more overlap and retry. Textureless walls and pure-rotation captures are
the known failure modes (see docs/PLAN.md).

## Dense scene step (needs CUDA — runs in the cloud)

COLMAP's dense stereo is CUDA-only (verified: the local CPU-only build refuses
to run it), so `dense.py` runs on a free cloud GPU following
[docs/CLOUD_RUN.md](../docs/CLOUD_RUN.md):

```bash
python3 pipeline/dense.py --session data/<session-id> [--max-size 1200]
# writes data/<session-id>/dense.json, auto-loaded as a layer in /cover/
```

Lower `--max-size` for speed, raise it for detail. The local laptop keeps the
fast CPU job: `reconstruct.py` as the overlap check (if poses register locally,
the scene will densify in the cloud).

## Stretch: photorealistic splat (same cloud notebook, after dense is secured)

Hard timebox: 3 hours. If it slips, cut it — the dense cloud is the demo.

## Segmentation (Meta SAM 3.1 — needs `MODEL_API_KEY`)

```bash
pip install -r pipeline/requirements-meta.txt
export MODEL_API_KEY=...
# smoke test on 3 photos, then full session:
python3 pipeline/segment.py --session data/<id> --concept person --mode remove --limit 3
python3 pipeline/segment.py --session data/<id> --concept person --mode remove
# reconstruct from masked images (separate --work: the default work/images
# symlinks already point at the originals and would shadow the masked set):
python3 pipeline/reconstruct.py --session data/<id> --images-from data/<id>/work/masked --work data/<id>/work-masked
```

`remove` blacks out matches (people/occluders); `keep` blacks out everything
except matches (subject isolation, e.g. `--concept generator --mode keep`).
Writes `work/masked/` + `work/masks.json`. Zero masks = photo copied unchanged.
