#!/usr/bin/env python3
"""3ill reconstruction pipeline (v0 scaffold).

Phase-0 path: session photos -> camera poses (COLMAP) -> scene -> novel views.

Usage:
  python3 pipeline/reconstruct.py --session data/<session-id> [--work DIR]

What it does today:
  1. Validates the session (photos present).
  2. Reports which reconstruction tools are installed (colmap, ffmpeg).
  3. If COLMAP is present, runs the real sparse reconstruction
     (feature extraction + exhaustive matching + mapping) and writes poses.
  4. Otherwise exits 2 with install pointers -- no fake outputs, ever.

Next steps (see docs/PLAN.md Phase 0): dense/scene step (Gaussian splatting
trainer of choice) + a novel-view render served under /data/<id>/render/.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def run(cmd, cwd):
    print("+ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        raise SystemExit("command failed (%d): %s" % (r.returncode, " ".join(cmd)))


def session_photos(sdir):
    return sorted(
        f for f in os.listdir(sdir)
        if f.lower().endswith(IMG_EXTS) and os.path.isfile(os.path.join(sdir, f))
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True, help="e.g. data/20261030-183000")
    ap.add_argument("--work", default=None, help="work dir (default: <session>/work)")
    args = ap.parse_args()

    sdir = args.session
    photos = session_photos(sdir)
    print("session: %s  photos: %d" % (sdir, len(photos)))
    if len(photos) < 2:
        raise SystemExit("need at least 2 photos; capture more via /capture/ first")

    work = args.work or os.path.join(sdir, "work")
    img_dir = os.path.join(work, "images")
    db_path = os.path.join(work, "db.db")
    sparse_dir = os.path.join(work, "sparse")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(sparse_dir, exist_ok=True)
    for f in photos:
        dst = os.path.join(img_dir, f)
        if not os.path.exists(dst):
            os.symlink(os.path.abspath(os.path.join(sdir, f)), dst)

    tools = {t: shutil.which(t) for t in ("colmap", "ffmpeg")}
    print("tools: " + json.dumps(tools))
    if not tools["colmap"]:
        print(
            "COLMAP not found. Install it to run poses, e.g.:\n"
            "  Ubuntu/Debian: sudo apt install colmap\n"
            "  macOS:         brew install colmap\n"
            "  or: https://colmap.github.io/install.html"
        )
        raise SystemExit(2)

    run(["colmap", "feature_extractor", "--database_path", db_path,
         "--image_path", img_dir], work)
    run(["colmap", "exhaustive_matcher", "--database_path", db_path], work)
    run(["colmap", "mapper", "--database_path", db_path,
         "--image_path", img_dir, "--output_path", sparse_dir], work)
    print("sparse poses written to %s" % sparse_dir)
    print("NEXT: dense/scene step not yet implemented (see pipeline/README.md).")


if __name__ == "__main__":
    main()
