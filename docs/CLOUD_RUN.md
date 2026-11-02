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
   cd data && tar czf <id>.tgz --exclude='<id>/work' <id> && cd ..
   ```
4. On the GPU box — one-time setup per fresh runtime (~5 min attended,
   then ~50 min unattended). Runtimes are EPHEMERAL: a reset wipes packages,
   the COLMAP build, clones, and uploads — only GitHub/Drive/laptop persist
   (see "Ephemeral runtimes" below). Fastest path is the one-shot script:
   ```bash
   !nvidia-smi | head -n 9
   !if [ -d 3ill ]; then git -C 3ill pull -q; else git clone -q https://github.com/babaolu/3ill.git; fi
   !cd 3ill && nohup bash cloud/setup_gpu_box.sh > $HOME/3ill-setup.log 2>&1 &
   !sleep 20; tail -n 8 $HOME/3ill-setup.log
   ```
   Prefix `COLMAP_CUDA_ARCH=60` to the script call if `nvidia-smi` shows a
   P100 instead of a T4 (T4 = 75, the default). Poll with
   `!tail -n 4 $HOME/3ill-setup.log`. Manual step-by-step cells (fallback /
   debugging) follow — skip them if the script runs clean:
   ```bash
   !sudo apt update -qq 2>&1 | tail -n 2; sudo apt install -qq -y git cmake ninja-build build-essential \
     libboost-program-options-dev libboost-filesystem-dev libboost-graph-dev \
     libboost-system-dev libeigen3-dev libflann-dev libfreeimage-dev libmetis-dev \
     libgoogle-glog-dev libgtest-dev libsqlite3-dev libglew-dev qtbase5-dev \
     libqt5opengl5-dev libcgal-dev libceres-dev libglvnd-dev libgl1-mesa-dev > /dev/null 2>&1; echo DEPS_DONE
   ```
   (`;` not `&&`: a flaky mirror must not block the install. Expect DEPS_DONE.)
   ```bash
   ![ -d colmap ] || git clone -q https://github.com/colmap/colmap.git
   !cd colmap && (git checkout -q 3.9.1 || git checkout -q main) && mkdir -p build && cd build && \
     nohup bash -c 'cmake .. -GNinja -DCUDA_ENABLED=ON -DCMAKE_CUDA_ARCHITECTURES=75 && ninja && sudo ninja install' \
     > $HOME/colmap-build.log 2>&1 &
   ```
   Poll with `!tail -n 3 $HOME/colmap-build.log` and
   `!pgrep -f '[n]inja' >/dev/null && echo BUILDING || echo DONE`
   (the bracket form avoids pgrep matching itself).
   If ninja stops early, the real error is above the tail — get it with:
   `!grep -iE "error|fatal" $HOME/colmap-build.log | head -n 20`.
   Known issue (COLMAP 3.9.1 + GCC 13): `'unique_ptr' is not a member of 'std'`
   in `src/colmap/image/line.cc` — patch and resume:
   `!cd colmap && sed -i '1i #include <memory>' src/colmap/image/line.cc`
   then `!cd colmap/build && nohup bash -c 'ninja && sudo ninja install' >
   $HOME/colmap-build.log 2>&1 &`. Repeat for any other file failing the
   same way (list them with
   `!grep -oE "src/[a-z_/]+\\.(cc|h)" $HOME/colmap-build.log | sort -u`).
   Link failure on `libOpenGL.so` (`_glapi_tls_Current`): this box's GL chain
   is broken and we only need COLMAP's CLI tools — install GLVND dev files,
   reconfigure with the GUI off, resume:
   `!sudo apt install -qq -y libglvnd-dev libgl1-mesa-dev > /dev/null 2>&1`
   then `!cd colmap/build && cmake .. -GNinja -DCUDA_ENABLED=ON
   -DCMAKE_CUDA_ARCHITECTURES=75 -DGUI_ENABLED=OFF
   -DCMAKE_EXE_LINKER_FLAGS=-lGLdispatch
   -DCMAKE_SHARED_LINKER_FLAGS=-lGLdispatch`
   then resume ninja as above. If the GL error persists, capture the failing
   target before retrying anything:
   `!grep -B12 "_glapi_tls_Current" $HOME/colmap-build.log | head -n 25`
   plus `!grep -E "^(GUI_ENABLED|CUDA_ENABLED)" colmap/build/CMakeCache.txt`
   (verifies the GUI-off reconfigure actually landed).
   PIVOT TRIGGER: if one GUI-off resume does not finish compiling within
   ~30 min, stop fixing the build — switch to the pip-wheels dense/splat spike
   (`!pip -q install gsplat`) or cut cloud-dense and demo local sparse + SAM.
   Fresh/partial runtime (`CMAKE_C_COMPILER not set`, missing ninja): the full
   deps install never landed — re-run the step-4 deps cell verbatim, verify
   with `!which gcc g++ ninja cmake nvcc`, re-check the two `sed` patches are
   still first lines of `line.cc`/`workspace.h` (fresh clones need them
   re-applied), then reconfigure + resume.
   Do steps 1-3 and the sparse pass (step 5) while it compiles. Keep the tab
   open on ephemeral runtimes — a reclaimed runtime kills the build.
5. Upload `<id>.tgz` next to the `3ill` folder (keep the tab open until the
   upload completes — a truncated file fails with `Unexpected EOF in
   archive`). Verify, then extract and run the sparse pass:
   ```bash
   !ls -lh ../<id>.tgz && tar tzf ../<id>.tgz > /dev/null && echo TARBALL_OK
   ```
   ```bash
   !cd 3ill && mkdir -p data && tar xzf ../<id>.tgz -C data
   !cd 3ill && python3 pipeline/reconstruct.py --session data/<id>
   !cd 3ill && python3 pipeline/poses_to_json.py --session data/<id>
   ```
6. When the build reports DONE: `!colmap -h | head -n 2` must show
   "with CUDA" (verified 2026-10-31: commit e9903641, installs to
   `/usr/local/bin/colmap`). Check precedence with `!which colmap` — it must
   be `/usr/local/bin/colmap`, not apt's `/usr/bin/colmap` ("without CUDA").
   If shadowed, run cells with `export PATH=/usr/local/bin:$PATH` first. Then:
   ```bash
   !cd 3ill && python3 pipeline/dense.py --session data/<id> --max-size 1200
   ```
   Download `3ill/data/<id>/dense.json` + `cover.json` to the laptop's
   `data/<id>/` **the instant dense finishes — runtimes disconnect without
   warning and take the files with them** (proven 2026-11-02: 526k-point bake
   lost to a disconnect before download). Then open `/cover/`, orbit.

## Ephemeral runtimes + GPU fallbacks

- A reset/reclaimed runtime loses everything on the box. Recovery = re-run
  step 4's script (one command, ~50 min unattended), re-upload the session
  `.tgz`, re-run steps 5-6. Keep the tab open; poll occasionally.
- Persist the session tarball on Google Drive to skip re-uploads:
  ```python
  from google.colab import drive; drive.mount('/content/drive')
  ```
  ```bash
  !cp 20261101-151941.tgz /content/drive/MyDrive/   # once, while box is alive
  !cp /content/drive/MyDrive/20261101-151941.tgz .  # after any reset
  ```
- Colab GPU limits reset on their own schedule (hours to a day; a second
  account is the only speedup). Don't wait idle: **Kaggle** gives 30 free
  GPU-hours weekly (T4/P100, sudo available) and runs the same script —
  fire it in parallel. Use `COLMAP_CUDA_ARCH=60` on a P100.
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
