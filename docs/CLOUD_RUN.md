# Cloud compute runbook (Colab free T4)

Neither local PC has NVIDIA. So compute splits across machines — same scripts,
two runners:

- **Laptop (this repo, CPU):** capture, sparse poses, coverage viz, serving,
  final viewer. `reconstruct.py` doubles as the fast overlap check: if poses
  register locally, the scene will densify in the cloud.
- **Colab free-T4 notebook (CUDA):** `dense.py` (COLMAP PatchMatch needs CUDA),
  plus the optional splat bake if time allows.

## Dense bake steps (~30-60 min first time)

1. Capture the hero scene via `/capture/` (30-60 photos, textured object,
   plenty of overlap). Note the session id, e.g. `20261101-103000`.
2. Run the local overlap check (minutes, CPU):
   ```bash
   python3 pipeline/reconstruct.py --session data/<id>
   python3 pipeline/poses_to_json.py --session data/<id>
   ```
   If fewer than ~2/3 of photos register, capture more overlap before burning
   cloud time. Check frustums in `/cover/`.
3. Pack the session (photos only; work/ stays local):
   ```bash
   cd data && tar czf <id>.tgz <id> --exclude='work' && cd ..
   ```
4. Open a new Colab notebook, Runtime → Change runtime type → **T4 GPU**.
   Verify the GPU is actually attached:
   ```bash
   !nvidia-smi
   ```
   No GPU here = stop and tell the human; the dense plan needs Kaggle instead.
5. In the notebook:
   ```bash
   !apt update -qq && apt install -qq -y colmap > /dev/null 2>&1
   !git clone https://github.com/babaolu/3ill.git
   ```
   NOTE: the apt COLMAP binary reports "without CUDA" — it does sparse
   reconstruction only, on any machine. It can NEVER run `dense.py`'s
   PatchMatch step, even on a GPU machine. Dense options on the T4:
   - (a) torch-based dense stereo (spike path — reuses the GPU via pip
     wheels, no building; export converts to `dense.json` for `/cover/`);
   - (b) build COLMAP from source with CUDA (~45 min, predictable but slow);
   - (c) skip dense: splat bake directly from sparse poses (glossiest).
   Upload `<id>.tgz` via the file browser, then run the fast sparse pass:
   ```bash
   !cd 3ill && mkdir -p data && tar xzf /content/<id>.tgz -C data
   !cd 3ill && python3 pipeline/reconstruct.py --session data/<id>
   !cd 3ill && python3 pipeline/poses_to_json.py --session data/<id>
   ```
   Then pick (a)/(b)/(c) with the human based on remaining time.
6. Download the resulting `dense.json`/`cover.json` (or splat export) into the
   laptop's `data/<id>/`, open `/cover/`, orbit the scene.

## If Colab has no free GPU

- Retry later / new account / Kaggle (30 free GPU-hours weekly, same commands).
- Fallback demo needs no cloud at all: sparse points + frustums + photo orbit
  (all local). Still "phones built this 3D scene," just sparser.

## Stretch: splat bake (only after dense.json is secured)

Same notebook, same photos: install one Gaussian-splatting trainer, train on
the COLMAP sparse output, export a web-viewable scene, wire it into
`/viewer/`. Hard timebox: 3 hours. If it slips, cut it — the dense cloud is
the demo.
