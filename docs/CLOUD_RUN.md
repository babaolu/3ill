# Cloud compute runbook (Colab free T4)

Neither local PC has NVIDIA. So compute splits across machines — same scripts,
two runners:

- **Laptop (this repo, CPU):** capture, sparse poses, coverage viz, serving,
  final viewer. `reconstruct.py` doubles as the fast overlap check: if poses
  register locally, the scene will densify in the cloud.
- **Colab free-T4 notebook (CUDA):** `dense.py` (COLMAP PatchMatch needs CUDA),
  plus the optional splat bake if time allows.

## Cloud bake steps (T4 confirmed 2026-10-31)

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
4. In the T4 notebook — one-time setup (~10 min attended, then ~40 min
   unattended build). The apt COLMAP is sparse-only, so we build the CUDA
   binary that unlocks `dense.py`:
   ```bash
   !git clone https://github.com/babaolu/3ill.git
   !python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())"
   ```
   ```bash
   !sudo apt update -qq && sudo apt install -qq -y git cmake ninja-build build-essential \
     libboost-program-options-dev libboost-filesystem-dev libboost-graph-dev \
     libboost-system-dev libeigen3-dev libflann-dev libfreeimage-dev libmetis-dev \
     libgoogle-glog-dev libgtest-dev libsqlite3-dev libglew-dev qtbase5-dev \
     libqt5opengl5-dev libcgal-dev libceres-dev > /dev/null 2>&1
   ```
   ```bash
   !cd /content && [ -d colmap ] || git clone -q https://github.com/colmap/colmap.git
   !cd /content/colmap && (git checkout -q 3.9.1 || git checkout -q main) && mkdir -p build && cd build && \
     nohup bash -c 'cmake .. -GNinja -DCUDA_ENABLED=ON -DCMAKE_CUDA_ARCHITECTURES=75 && ninja && sudo ninja install' \
     > /content/colmap-build.log 2>&1 &
   ```
   Poll with `!tail -n 3 /content/colmap-build.log` and
   `!pgrep -f ninja >/dev/null && echo BUILDING || echo DONE`.
   Do steps 1-3 and the sparse pass (step 5) while it compiles. Keep the tab
   open — a reclaimed runtime kills the build.
5. Upload `<id>.tgz` via the file browser, run the sparse pass:
   ```bash
   !cd /content/3ill && mkdir -p data && tar xzf /content/<id>.tgz -C data
   !cd /content/3ill && python3 pipeline/reconstruct.py --session data/<id>
   !cd /content/3ill && python3 pipeline/poses_to_json.py --session data/<id>
   ```
6. When the build reports DONE: `!colmap -h | head -n 2` must show
   "with CUDA" (if it still says "without", the install step failed — paste
   the log tail). Then:
   ```bash
   !cd /content/3ill && python3 pipeline/dense.py --session data/<id> --max-size 1200
   ```
   Download `data/<id>/dense.json` + `cover.json` to the laptop's `data/<id>/`,
   open `/cover/`, orbit the scene.

## If Colab has no free GPU

- Retry later / new account / Kaggle (30 free GPU-hours weekly, same commands).
- Fallback demo needs no cloud at all: sparse points + frustums + photo orbit
  (all local). Still "phones built this 3D scene," just sparser.

## Stretch: splat bake (only after dense.json is secured)

Same notebook, same photos. Spike cells (install + import check):
```bash
!pip -q install gsplat
!python3 -c "import gsplat; print('gsplat ok')"
```
If the import works, training cells come next (train on the COLMAP sparse
output, export a web-viewable scene, wire it into `/viewer/`). Hard timebox:
3 hours. If it slips, cut it — the dense cloud is the demo.
