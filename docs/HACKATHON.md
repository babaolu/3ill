# Hackathon strategy (Meta Global AI Developer Hackathon)

## What wins

A live moment: 3+ phones photograph a scene, and a virtual camera flies through
the fused 3D result on the big screen. Everything below serves that moment.
Slides don't win; the orbit does.

## Demo script (90 seconds)

1. (0:00) "Every phone here sees the same scene from a different angle."
   Show 3 phones on `/capture/`, one session.
2. (0:20) Snap ~10 photos total, walking around an object. Crowd sees uploads
   land in `/viewer/` live (hit Load between bursts).
3. (0:50) Run the pipeline (or reveal a pre-baked reconstruction if live
   compute is too slow — pre-bake the same object as backup, disclose it).
4. (1:10) Orbit the result. "The scene is the phones. More phones, fewer blind
   spots." Point at the per-device coverage counts.
5. (1:30) Close: placement guidance + compute lending as "what's next" (show
   the mock or the roadmap, not vaporware claims).

## Priority stack

- **P0 — unbreakable capture loop.** Server + `/capture/` + `/viewer/` working
  on venue WiFi. Rehearse with a phone hotspot as backup network.
- **P0 — one pre-baked reconstruction.** A good-looking orbit of a fixed object,
  captured with the same pipeline. This is the demo insurance policy.
- **P1 — live pose/coverage readout.** Even without live rendering, showing
  "12 photos, 3 devices, coverage growing" during capture sells the fusion story.
- **P1 — blind-spot visualization.** Simplest honest version: per-device photo
  counts + capture-order timeline (already in v0 viewer); next: frustum plot
  from poses once COLMAP runs.
- **P2 — placement guidance.** "Move here" hints need live poses (Phase 1).
  If time allows, mock the UI over precomputed poses; label it a prototype.
- **P3 — compute lending.** Pitch as architecture (stage-split diagram), not a
  live feature. Do not burn demo time here.

## Cut list (say no to these during the hackathon)

- Native phone apps (browser capture is enough).
- True distributed GPU pooling.
- User accounts, cloud deploy, video ingestion.
- Supporting more than one scene type (pick textured objects, avoid blank walls).

## Pitch outline (2 minutes)

1. Problem: one phone sees one flat view; the scene exists between all cameras.
2. 3ill: phones link by location; each perspective fuses into one navigable 3D
   scene with a free virtual camera.
3. Live demo (the orbit).
4. Why it's hard / why now: sparse-view synthesis + phone GPUs crossed the
   feasibility line recently (see STATE_OF_ART.md).
5. Roadmap: live poses → guidance ("stand here") → compute lending; every
   added phone sharpens the world.

## Rehearsal checklist

- [ ] Venue WiFi tested with 3 phones, or hotspot fallback confirmed.
- [ ] Laptop IP known; `/capture/` QR code printed or on screen.
- [ ] Pre-baked session renders offline (no network dependency).
- [ ] Backup video of the full demo on the laptop.
- [ ] One textured demo object chosen (plant, chair, backpack — not white walls).
