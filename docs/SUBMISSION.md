# 3ill (thrill) — submission package

## Title + tagline

**3ill** — Link phones by location; every camera adds its perspective to one
navigable 3D scene with a free virtual camera.

## What it does (paste-ready)

One phone sees one flat view — the scene exists *between* all cameras. 3ill
links phones in one location so each camera contributes its perspective of a
physical scene. A central aggregator fuses them into a navigable 3D world you
fly a virtual camera through, like a video game whose level is built live from
everyone's phones. The system maps coverage from all poses, exposes blind
spots, and guides phones to positions where the fewest cameras cover the most
scene. Meta's SAM 3.1 segments every capture first, stripping background and
occluders before fusion.

## How it works

1. **Capture (no app install):** phones open `/capture/` in the browser, join
   a session, and photograph the scene. Photos + metadata stream to the
   aggregator (stdlib-only Python server).
2. **Segment (Meta SAM 3.1):** `pipeline/segment.py` masks each photo —
   subject isolation or occluder removal — verified live on 57/63 session
   photos via the Meta Model API.
3. **Pose:** COLMAP sparse reconstruction registers the views (56/63 across
   all three phones in the demo session).
4. **Coverage:** `/cover/` renders every phone as a 3D camera frustum plus
   sparse points — gaps between frustums are the blind spots, and the same
   geometry drives "stand here" placement guidance.
5. **Scene:** dense point cloud baked on GPU (`pipeline/dense.py`), orbited in
   the browser; `/viewer/` photo-orbit works with zero GPU as the fallback.

## Meta models used (rule compliance)

- **SAM 3.1 (`sam-3.1`) via Meta Model API** — working pipeline stage:
  text-prompted segmentation of every capture before reconstruction
  (`pipeline/segment.py`, `work/masks.json`, before/after images). Verified
  live 2026-11-02.
- **Muse Code** — the repo (server, pages, pipeline, docs) was built with
  Meta's coding agent.
- Roadmap (documented, not faked): Muse Voice Transcribe for voice-driven
  capture; Muse Wonder as capture-QA agent; Muse Image for blind-spot
  previews. See `docs/META.md`.

## Try it

```bash
git clone https://github.com/babaolu/3ill.git && cd 3ill
python3 server/app.py          # http://localhost:8000/viewer/
# phones on the same WiFi: http://<laptop-ip>:8000/capture/
python3 pipeline/reconstruct.py --session data/<id>
python3 pipeline/poses_to_json.py --session data/<id>
# open http://localhost:8000/cover/ for the session
```

## Demo video shot list (60–90 s)

1. (0:00) Three phones on `/capture/`, one session — "every phone sees the
   same scene from a different angle."
2. (0:15) Snapping photos around the generator; uploads landing live.
3. (0:30) `/viewer/` orbit across all 63 contributed photos.
4. (0:45) `/cover/`: 56 camera frustums from 3 phones + sparse cloud —
   "the scene is the phones."
5. (1:00) SAM before/after: original vs background-stripped generator —
   "Meta's SAM 3.1 cleans every view before fusion."
6. (1:15, if the dense bake lands) Dense 100k-point cloud orbit + close:
   "more phones, fewer blind spots."

Record with phone #4 or screen capture; narrate over it. Backup: the same
shots as silent screen recording with captions. **Record before 22:00 no
matter what the GPU is doing.**
