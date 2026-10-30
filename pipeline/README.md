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

## Scene/render step (TODO, in priority order)

1. Pick one scene trainer that consumes COLMAP sparse output and emits
   something renderable in a browser (shortlist to spike: a Gaussian-splatting
   trainer with a web viewer export).
2. `render.py --session ...` producing `data/<id>/render/` + a viewer hook.
3. Wire viewer orbit mode to rendered novel views when `render/` exists,
   falling back to the photo crossfade otherwise.
