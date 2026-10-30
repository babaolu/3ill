# 3ill (thrill)

Link phones together in one location. Each phone's camera adds its perspective
of the physical scene; 3ill fuses them into a navigable 3D scene you can move a
virtual camera through — like a video game whose world is built live from
everyone's phones.

- **Capture phones** stream photos/video + pose to one aggregator session.
- **Compute-lender phones** (camera off) take pipeline stages: decode, feature
  extraction, tile rendering.
- **Viewer** places a virtual eye anywhere in the fused scene and rotates it.
- **Placement guide** finds positions where the fewest phones cover the scene,
  shows blind spots, and re-plans live when a phone drifts.

Built for the Meta Global AI Developer Hackathon. See [docs/HACKATHON.md](docs/HACKATHON.md)
for the demo strategy, [docs/PLAN.md](docs/PLAN.md) for the feasibility plan,
and [docs/STATE_OF_ART.md](docs/STATE_OF_ART.md) for prior-art notes.

## Repo layout

- `server/` — aggregator: sessions, photo/pose ingest, static pages (stdlib-only Python).
- `capture/` — phone capture web page (no app install: open in the phone browser).
- `viewer/` — session viewer web page (v0 preview; true novel-view render is the pipeline target).
- `pipeline/` — reconstruction scripts (pose estimation → scene → render).
- `docs/` — plan, state of art, hackathon strategy.

## Quickstart (2 minutes, no installs)

```bash
python3 server/app.py            # serves on http://<your-laptop-ip>:8000
```

1. On each phone (same WiFi): open `http://<laptop-ip>:8000/capture/`, create or
   join a session, snap photos around the scene.
2. On the laptop: open `http://localhost:8000/viewer/`, enter the session id,
   and orbit the v0 preview.

Captured sessions land in `data/<session-id>/` (git-ignored).

## Roadmap

- **Phase 0** — static proof: synced phone photos → poses → navigable 3D view.
- **Phase 1** — live poses + coverage/blind-spot guidance.
- **Phase 2** — near-live dynamic views (laptop-class aggregator).
- **Phase 3** — phone-as-aggregator, quality-vs-phone-count scaling.
- **Phase 4** — compute lending across camera-off phones.

Details in [docs/PLAN.md](docs/PLAN.md).
