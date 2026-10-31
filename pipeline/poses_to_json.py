#!/usr/bin/env python3
"""COLMAP sparse model -> cover.json for the coverage viewer (/cover/).

Usage:  python3 pipeline/poses_to_json.py --session data/<id> [--max-points 5000]

Reads <session>/work/sparse/0 (runs `colmap model_converter` to TXT first when
only .bin files exist) and writes <session>/cover.json with camera poses and a
sample of sparse points. Stdlib only.
"""

import argparse
import json
import os
import subprocess


def qvec2rotmat(q):
    w, x, y, z = q
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]


def cam_position(rot, t):
    # p = -R^T t
    return [
        -(rot[0][0] * t[0] + rot[1][0] * t[1] + rot[2][0] * t[2]),
        -(rot[0][1] * t[0] + rot[1][1] * t[1] + rot[2][1] * t[2]),
        -(rot[0][2] * t[0] + rot[1][2] * t[1] + rot[2][2] * t[2]),
    ]


def read_txt(path):
    with open(path) as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--max-points", type=int, default=5000)
    args = ap.parse_args()

    model = os.path.join(args.session, "work", "sparse", "0")
    if not os.path.isdir(model):
        model = os.path.join(args.session, "work", "sparse")
    if not os.path.isfile(os.path.join(model, "images.txt")):
        print("converting binary model to TXT ...")
        r = subprocess.run(["colmap", "model_converter", "--input_path", model,
                            "--output_path", model, "--output_type", "TXT"])
        if r.returncode != 0:
            raise SystemExit("model_converter failed; is this a valid sparse model?")
    if not os.path.isfile(os.path.join(model, "images.txt")):
        raise SystemExit("no sparse model found; run reconstruct.py first")

    cams = {}
    for ln in read_txt(os.path.join(model, "cameras.txt")):
        toks = ln.split()
        cid, w, h = int(toks[0]), int(toks[2]), int(toks[3])
        f = float(toks[4])  # first param is f/fx for all common models
        cams[cid] = {"w": w, "h": h, "f": f}

    cameras = []
    lines = read_txt(os.path.join(model, "images.txt"))
    for i in range(0, len(lines), 2):
        toks = lines[i].split()
        q = [float(v) for v in toks[1:5]]
        t = [float(v) for v in toks[5:8]]
        cid, name = int(toks[8]), toks[9]
        rot = qvec2rotmat(q)
        cameras.append({
            "name": name, "w": cams[cid]["w"], "h": cams[cid]["h"],
            "f": cams[cid]["f"], "pos": cam_position(rot, t), "quat": q,
        })

    points = []
    ppath = os.path.join(model, "points3D.txt")
    if os.path.isfile(ppath):
        allpts = read_txt(ppath)
        stride = max(1, len(allpts) // args.max_points)
        for ln in allpts[::stride][:args.max_points]:
            toks = ln.split()
            points.append([float(toks[1]), float(toks[2]), float(toks[3]),
                           int(toks[4]), int(toks[5]), int(toks[6])])

    out = os.path.join(args.session, "cover.json")
    with open(out, "w") as f:
        json.dump({"cameras": cameras, "points": points}, f)
    print("wrote %s  cameras=%d points=%d" % (out, len(cameras), len(points)))


if __name__ == "__main__":
    main()
