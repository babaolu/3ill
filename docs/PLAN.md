# 3ill feasibility plan

Persisted from the planning session (2026-10-30). Status: execution started.

## Goal

Answer whether 3ill — phones linked by location, each contributing a camera
perspective into one navigable 3D scene with a free virtual camera, plus
optimal-placement guidance and compute-sharing from camera-off phones — can be
built, and by what path.

## Success Criteria

- Each subsystem gets a verdict: proven, feasible-with-work, or high-risk, with
  the evidence that would confirm or refute it.
- The full vision is decomposed into ordered phases, each independently
  demonstrable, so a "no" on one phase doesn't kill the project.
- The highest-risk items (live dynamic reconstruction, phone-to-phone compute
  sharing) have concrete falsification tests, not opinions.

## Approach

**Preliminary verdict: feasible in phases; not feasible as a single build.**
Subsystem verdicts, least to most risky:

1. **Synchronized multi-phone capture** — least risky. Software clock/frame sync
   of commodity phones over WiFi plus collaborative capture UX.
2. **Pose estimation for handheld phones** — feasible with work. On-device
   visual-inertial tracking + joint cross-view refinement. Failure modes:
   textureless scenes, pure rotation, fast motion.
3. **Static-scene novel-view synthesis from sparse views** — feasible; most
   mature layer (photorealistic new viewpoints from a handful of photos,
   including on-device rendering).
4. **Live/dynamic free-viewpoint video** — feasible at reduced quality/latency
   first. First working version needs a server-class aggregator (laptop/edge);
   phone-as-aggregator comes later.
5. **Optimal-placement guidance + blind-spot detection** — feasible. Coverage is
   computable geometry from poses + frustums; next-best-view guidance optimizes
   over it; blind spots are uncovered regions to visualize.
6. **Compute lending across camera-off phones** — highest risk. No strong
   platform story for pooled mobile GPU compute. Practical form is *stage-split
   collaboration* (preprocess on-device, fuse/render central), not a true
   distributed GPU pool.

Recommended architecture: phones as smart capture/edge nodes (sync, pose,
preprocess) → one aggregator (edge device first, phone later) for fusion +
scene update → thin novel-view renderer any linked phone can drive. Placement
optimizer and coverage visualizer sit on the aggregator from day one (they only
need poses, not pixels).

## Steps

- **Phase 0 — Static proof.** 3–5 synced phones photograph a room-scale scene;
  offline pipeline produces poses + a navigable 3D view on one phone.
- **Phase 1 — Live poses + coverage guidance.** Real-time pose streaming;
  coverage map, blind-spot visualization, "move here" suggestions. No live
  pixels yet.
- **Phase 2 — Near-live dynamic views.** Streaming scene updates at reduced
  resolution/framerate with a laptop-class aggregator; measures the
  latency/quality curve.
- **Phase 3 — Phone-as-aggregator + scale.** Aggregation moves onto a phone;
  quality-vs-phone-count scaling tested.
- **Phase 4 — Compute sharing.** Pipeline stages offloaded to camera-off
  phones; proceed only if Phase 2/3 show headroom worth distributing.

## Validation Plan

- Sync accuracy: filmed timing target; bar is sub-frame alignment at 30 fps.
- Pose quality: held-out-view render quality (PSNR/SSIM/LPIPS) beats a
  single-phone baseline; tracking survives a walked loop without visible drift.
- Coverage optimizer: guided placement covers more than unguided with N
  phones; removing one phone triggers a re-plan recovering most of the loss.
- Liveness: end-to-end capture-to-novel-view latency per phase (Phase 2 target:
  seconds, tightening toward sub-second in Phase 3).
- Compute sharing: added phones must improve fps or quality net of network
  cost, or the feature is cut.

Highest-risk validation step: Phase 2's latency/quality curve — it decides
whether the experience is real-time or near-real-time.

## Risks / Open Questions

- **Evidence gap:** initial external claims were search-discovery level; close
  with a sourced literature check before heavy code (see STATE_OF_ART.md).
- **Assumptions:** one shared WiFi network; modern smartphones; room-scale
  scenes first; laptop aggregator acceptable early.
- **Risks:** handheld unsynchronized cameras harder than fixed rigs; N-stream
  uplink bandwidth; mobile background-execution/thermal limits for compute
  lenders; dynamic occluders breaking static assumptions.
- **Non-goals:** literal orthographic-plane fusion; a distributed-GPU-pooling
  framework as a first build.
