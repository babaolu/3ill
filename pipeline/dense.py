#!/usr/bin/env python3
"""Dense reconstruction: sparse model -> dense point cloud -> dense.json.

Usage:  python3 pipeline/dense.py --session DIR [--max-size 1200]
                                             [--max-points 100000]

Steps:
  1. colmap image_undistorter  (downscaled to --max-size for speed)
  2. colmap patch_match_stereo (REQUIRES CUDA -- run on Colab, see CLOUD_RUN.md)
  3. colmap stereo_fusion       -> dense/fused.ply
  4. sample fused.ply           -> dense.json (loaded by /cover/)
"""

import argparse
import json
import os
import struct
import subprocess
import sys


def run(cmd):
    print("+ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit("command failed (%d): %s" % (r.returncode, " ".join(cmd)))


def read_dense_ply(path, max_points):
    """Parse COLMAP fused.ply (ASCII or binary LE) into sampled xyzrgb rows."""
    with open(path, "rb") as f:
        header = []
        while True:
            line = f.readline().decode("ascii")
            header.append(line)
            if line.strip() == "end_header":
                break
    n_verts = 0
    props = []  # (name, struct-char)
    in_vertex = False
    fmt = None
    for line in header:
        toks = line.split()
        if toks[:2] == ["format", "ascii"]:
            fmt = "ascii"
        elif toks[0] == "format":
            fmt = "binary"
        elif toks[:2] == ["element", "vertex"]:
            n_verts = int(toks[2])
            in_vertex = True
        elif toks[0] == "element":
            in_vertex = False
        elif toks[0] == "property" and in_vertex:
            kind, name = toks[1], toks[2]
            props.append((name, {"float": "f", "float32": "f", "uchar": "B",
                                 "uint8": "B", "int": "i"}[kind]))
    if not n_verts or not props:
        raise SystemExit("unparseable PLY header in %s" % path)
    names = [n for n, _ in props]
    xi = names.index("x")
    rkeys = [["red", "green", "blue"], ["diffuse_red", "diffuse_green", "diffuse_blue"],
             ["r", "g", "b"]]
    ci = next(([names.index(k) for k in cand] for cand in rkeys
               if all(k in names for k in cand)), None)
    stride = max(1, n_verts // max_points)
    pts = []
    with open(path, "rb") as f:
        for line in header:
            f.readline()
        if fmt == "ascii":
            for i, line in enumerate(f):
                if i % stride or len(pts) >= max_points:
                    continue
                v = line.split()
                rgb = [int(float(v[j])) for j in ci] if ci else [255, 255, 255]
                pts.append([float(v[xi]), float(v[xi + 1]), float(v[xi + 2])] + rgb)
        else:
            rec = struct.Struct("<" + "".join(c for _, c in props))
            for i in range(n_verts):
                buf = f.read(rec.size)
                if i % stride or len(pts) >= max_points:
                    continue
                v = rec.unpack(buf)
                rgb = [int(v[j]) for j in ci] if ci else [255, 255, 255]
                pts.append([float(v[xi]), float(v[xi + 1]), float(v[xi + 2])] + rgb)
    return pts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--max-size", type=int, default=1200)
    ap.add_argument("--max-points", type=int, default=100000)
    args = ap.parse_args()

    sparse = os.path.join(args.session, "work", "sparse", "0")
    if not os.path.isdir(sparse):
        sparse = os.path.join(args.session, "work", "sparse")
    images = os.path.join(args.session, "work", "images")
    dense = os.path.join(args.session, "work", "dense")
    os.makedirs(dense, exist_ok=True)

    run(["colmap", "image_undistorter", "--image_path", images,
         "--input_path", sparse, "--output_path", dense,
         "--output_type", "COLMAP", "--max_image_size", str(args.max_size)])
    run(["colmap", "patch_match_stereo", "--workspace_path", dense])
    fused = os.path.join(dense, "fused.ply")
    run(["colmap", "stereo_fusion", "--workspace_path", dense,
         "--output_path", fused])

    pts = read_dense_ply(fused, args.max_points)
    out = os.path.join(args.session, "dense.json")
    with open(out, "w") as f:
        json.dump({"points": pts}, f)
    print("wrote %s  points=%d" % (out, len(pts)))


if __name__ == "__main__":
    main()
