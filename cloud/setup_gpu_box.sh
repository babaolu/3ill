#!/bin/bash
# 3ill GPU-box one-shot setup: system deps + CUDA COLMAP build + repo checkout.
# Idempotent: safe to re-run after a runtime reset. Unattended (~50 min).
#
# Usage on a fresh T4/P100 runtime (Colab, Kaggle, or any Ubuntu box with sudo):
#   git clone https://github.com/babaolu/3ill.git && cd 3ill
#   bash cloud/setup_gpu_box.sh                 # T4 (CUDA arch 75)
#   COLMAP_CUDA_ARCH=60 bash cloud/setup_gpu_box.sh    # P100
#
# Env: WORK (default: current dir), COLMAP_CUDA_ARCH (default: 75).
set -u
export PATH="/usr/local/bin:$PATH"
WORK="${WORK:-$PWD}"
ARCH="${COLMAP_CUDA_ARCH:-75}"
cd "$WORK" || exit 1

echo "==> system deps"
sudo apt update -qq 2>&1 | tail -n 1
sudo apt install -qq -y git cmake ninja-build build-essential pkg-config \
  libboost-program-options-dev libboost-filesystem-dev libboost-graph-dev \
  libboost-system-dev libeigen3-dev libflann-dev libfreeimage-dev libmetis-dev \
  libgoogle-glog-dev libgtest-dev libsqlite3-dev libglew-dev qtbase5-dev \
  libqt5opengl5-dev libcgal-dev libceres-dev libglvnd-dev libgl1-mesa-dev \
  > /tmp/3ill-deps.log 2>&1
command -v nvcc >/dev/null || sudo apt install -qq -y nvidia-cuda-toolkit >> /tmp/3ill-deps.log 2>&1
echo "tools: $(which gcc g++ ninja cmake nvcc 2>/dev/null | tr '\n' ' ')"

echo "==> repo"
if [ -d 3ill ]; then git -C 3ill pull -q; else git clone -q https://github.com/babaolu/3ill.git; fi

if command -v colmap >/dev/null && colmap -h 2>/dev/null | head -n 2 | grep -q "with CUDA"; then
  echo "CUDA colmap already installed; skipping build."
  exit 0
fi

echo "==> colmap source (CUDA arch $ARCH)"
[ -d colmap ] || git clone -q https://github.com/colmap/colmap.git
cd colmap && (git checkout -q 3.9.1 || git checkout -q main)
# GCC 13 needs explicit <memory> in these files (idempotent).
for f in src/colmap/image/line.cc src/colmap/mvs/workspace.h; do
  head -n 1 "$f" | grep -q '<memory>' || sed -i '1i #include <memory>' "$f"
done
mkdir -p build && cd build
cmake .. -GNinja -DCUDA_ENABLED=ON -DCMAKE_CUDA_ARCHITECTURES="$ARCH" \
  -DGUI_ENABLED=OFF -DCMAKE_EXE_LINKER_FLAGS=-lGLdispatch \
  -DCMAKE_SHARED_LINKER_FLAGS=-lGLdispatch || exit 1
ninja && sudo ninja install || exit 1

echo "==> verify"
colmap -h 2>/dev/null | head -n 2
