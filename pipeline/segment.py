#!/usr/bin/env python3
"""SAM 3.1 masking stage (Meta Model API): segment session photos, mask them.

Usage:
  pip install -r pipeline/requirements-meta.txt   # openai, meta_sam_parser
  export MODEL_API_KEY=...
  python3 pipeline/segment.py --session data/<id> --concept person --mode remove
  python3 pipeline/reconstruct.py --session data/<id> --images-from data/<id>/work/masked

Modes: `remove` blacks out matches (dynamic occluders, e.g. people walking
through the scene); `keep` blacks out everything EXCEPT matches (background
removal around the subject). Repeat --concept for several noun phrases (one
API request each; masks are unioned).

Writes work/masked/<photo> (full-res, same filenames) + work/masks.json with
per-photo boxes and foreground fractions. Zero masks = photo copied unchanged
(never blacken blindly). Photos are downscaled to 1600px for the API call;
masks are upscaled back to full resolution for output.

SAM request flow adapted from Meta's copy-and-combine blocks in
meta-models/meta-model-cookbook, 07_sam/01_api_basics/python/sam_api.py.
"""
import argparse
import asyncio
import base64
import io
import json
import mimetypes
import os
import sys
from contextlib import aclosing

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reconstruct import session_photos

BASE_URL = "https://api.meta.ai/v1"
MODEL = "sam-3.1"
SEND_MAX = 1600  # downscale long edge for the API call


def need(mod):
    raise SystemExit(
        "missing dependency '%s': run  pip install -r pipeline/requirements-meta.txt" % mod)


async def stream_events(stream):
    """Adapt SDK events to parser input (from the Meta cookbook: synthesize the
    response.output_text.done lane-closer the API omits)."""
    completed = set()
    async for event in stream:
        data = event.model_dump() if hasattr(event, "model_dump") else dict(event)
        lane = (data.get("item_id"), data.get("output_index"), data.get("content_index"))
        if data.get("type") == "response.output_text.done":
            if lane not in completed:
                completed.add(lane)
                yield data
            continue
        yield data
        part = data.get("part")
        if (data.get("type") == "response.content_part.done"
                and lane not in completed and isinstance(part, dict)
                and part.get("type") == "output_text"
                and isinstance(part.get("text"), str)):
            completed.add(lane)
            yield {"type": "response.output_text.done",
                   "item_id": data.get("item_id"),
                   "output_index": data.get("output_index"),
                   "content_index": data.get("content_index"),
                   "text": part["text"]}


async def segment_image(api, img_bytes, mime, concept):
    try:
        from meta_sam_parser import (parse_responses_stream,
                                     image_segmentation_format)
    except ImportError:
        need("meta_sam_parser")
    data_url = "data:%s;base64,%s" % (mime, base64.b64encode(img_bytes).decode())
    stream = await api.responses.create(
        model=MODEL, stream=True,
        input=[{"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": concept.strip()},
            {"type": "input_image", "image_url": data_url}]}])
    async with stream, aclosing(stream_events(stream)) as events:
        return await parse_responses_stream(
            events, image_segmentation_format()).final_result()


def check_result(result, concept, photo):
    if result.outcome.status != "completed":
        raise RuntimeError("%s: %s incomplete (%s)" % (
            photo, concept, getattr(result.outcome, "reason", "unknown")))
    errs = [d for d in result.diagnostics if d.severity == "error"]
    if errs:
        raise RuntimeError("%s: parser errors: %s" % (
            photo, "; ".join("line %s: %s" % (d.line, d.message) for d in errs)))


def union_raster(result):
    """OR all mask rasters; returns (w, h, bytearray) or None when no masks."""
    from meta_sam_parser import decode_mask_to_raster
    masks = [r for r in result.records if r.kind == "mask"]
    if not masks:
        return None
    w, h = masks[0].mask.width, masks[0].mask.height
    acc = bytearray(w * h)
    for rec in masks:
        if rec.mask.width != w or rec.mask.height != h:
            continue  # skip size mismatches rather than corrupt the union
        for i, v in enumerate(decode_mask_to_raster(rec.mask)):
            if v:
                acc[i] = 1
    return w, h, acc


def apply_mask(photo_path, out_path, union, mode):
    from PIL import Image
    img = Image.open(photo_path).convert("RGB")
    if union is None:
        img.save(out_path, quality=92)  # no matches: copy unchanged
        return 0.0
    w, h, acc = union
    m = Image.frombytes("L", (w, h), bytes(b * 255 for b in acc))
    m = m.resize(img.size, Image.NEAREST).point(lambda v: 255 if v > 128 else 0)
    black = Image.new("RGB", img.size, (0, 0, 0))
    if mode == "remove":
        inv = m.point(lambda v: 0 if v else 255)
        Image.composite(img, black, inv.convert("L")).save(out_path, quality=92)
    else:  # keep
        Image.composite(img, black, m.convert("L")).save(out_path, quality=92)
    px = m.tobytes()
    return sum(1 for b in px if b) / len(px)


async def worker(api, sem, sdir, outdir, photo, concepts, mode, report):
    from PIL import Image
    async with sem:
        path = os.path.join(sdir, photo)
        img = Image.open(path).convert("RGB")
        img.thumbnail((SEND_MAX, SEND_MAX), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88)
        small = buf.getvalue()
        acc = None
        boxes = []
        for concept in concepts:
            res = await segment_image(api, small, "image/jpeg", concept)
            check_result(res, concept, photo)
            boxes += [{"concept": concept, "object_id": r.object_id,
                       "left": r.left, "top": r.top,
                       "right": r.right, "bottom": r.bottom}
                      for r in res.records if r.kind == "box"]
            u = union_raster(res)
            if u and acc is None:
                acc = u
            elif u:
                _, _, more = u
                w0, h0, base = acc
                if (w0, h0) == (u[0], u[1]):
                    for i, v in enumerate(more):
                        if v:
                            base[i] = 1
        fg = apply_mask(path, os.path.join(outdir, photo), acc, mode)
        report.append({"photo": photo, "boxes": boxes,
                       "foreground_fraction": round(fg, 4),
                       "masked": acc is not None})
        print("%s: %d box(es), fg=%.3f%s" % (
            photo, len(boxes), fg, "" if acc else " (unchanged)"), flush=True)


async def main_async(sdir, concepts, mode, limit, jobs):
    try:
        from openai import AsyncOpenAI
    except ImportError:
        need("openai")
    key = os.environ.get("MODEL_API_KEY")
    if not key:
        raise SystemExit("Set MODEL_API_KEY before calling the SAM API.")
    photos = session_photos(sdir)
    if limit:
        photos = photos[:limit]
    outdir = os.path.join(sdir, "work", "masked")
    os.makedirs(outdir, exist_ok=True)
    report = []
    sem = asyncio.Semaphore(jobs)
    async with AsyncOpenAI(base_url=BASE_URL, api_key=key) as api:
        await asyncio.gather(*[worker(api, sem, sdir, outdir, p, concepts,
                                      mode, report) for p in photos])
    with open(os.path.join(sdir, "work", "masks.json"), "w") as f:
        json.dump(report, f, indent=1)
    n = sum(1 for r in report if r["masked"])
    print("masked %d/%d photos -> %s" % (n, len(report), outdir))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--concept", action="append", required=True,
                    help="short noun phrase; repeatable")
    ap.add_argument("--mode", choices=["remove", "keep"], default="remove")
    ap.add_argument("--limit", type=int, default=0, help="process first N only")
    ap.add_argument("--jobs", type=int, default=4, help="parallel requests")
    args = ap.parse_args()
    asyncio.run(main_async(os.path.abspath(args.session), args.concept,
                           args.mode, args.limit, args.jobs))


if __name__ == "__main__":
    main()
