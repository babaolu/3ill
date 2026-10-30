# State of the art (working notes)

Honesty label: these notes are **search-discovery level** (result snippets, not
inspected primary sources). Every claim below needs verification against the
linked primary source before it is cited in the pitch or relied on in code.
Highest-value verifications are marked [VERIFY FIRST].

## Synchronized phone capture

- Software-only WiFi sync of smartphone cameras reporting sub-millisecond
  accuracy on unmodified commodity hardware (leader-follower clock sync +
  delay estimation). If it holds, 3ill needs no custom hardware for sync.
  [VERIFY FIRST] — http://arxiv.org/pdf/1507.01147v2 (see also the
  `1812.09366` wireless-sync paper mirrors in search results).
- PanoSwarm / "Camera Swarm": multiple phones capturing panoramas of dynamic
  scenes collaboratively with a server coordinating viewfinders in real time —
  direct precedent for 3ill's coordinated-capture UX.
  [VERIFY FIRST] — http://arxiv.org/pdf/1507.01147v2
- OpenCap: 3 tripod-mounted iPhones at 720p60 fused for 3D human movement,
  matching lab-grade multi-camera rigs on some metrics — precedent that a few
  phones can stand in for expensive rigs.
  — https://scienmag.com/smartphone-cameras-match-lab-systems-in-reading-how-aging-muscles-fail-the-chair-stand-test/

## Sparse-view / dynamic novel-view synthesis

- LiveGS (ByteDance MultiMedia Lab, SIGGRAPH 2025 Emerging Technologies):
  free-viewpoint video from a small number of synchronized cameras, including
  iPhones, instead of a dense volumetric array. Closest industry precedent to
  3ill's core claim. [VERIFY FIRST]
  — https://radiancefields.com/bytedance-multimedia-lab-builds-a-4d-media-system-for-live-and-on-demand-6dof-video
- 4DGC / streamable dynamic Gaussian compression: rate-aware compression
  claiming real-time decoding/rendering of free-viewpoint video on mobile.
  — https://arxiv.deeppaper.ai/papers/2503.18421v1
- Mobile-GS: Gaussian-splatting rendering at 100+ fps at ~1600×1063 on a
  Snapdragon 8 Gen 3 GPU with megabyte-scale storage. Suggests the *rendering*
  side can live on phones; reconstruction remains the heavy side.
  — https://arxiv.org/pdf/2603.11531
- OrbitSplat: reconstructing objects from ordinary handheld smartphone video
  via pose estimation + Gaussian splatting; documents practical pains (blurry
  frames, redundant views, background contamination, limited GPU memory) that
  3ill's capture UX should design around.
  — https://github.com/battery-ta-tfn/orbitsplat
- GPS-Gaussian: generalizable pixel-wise splatting for real-time human novel
  view synthesis without per-scene optimization — the direction that removes
  3ill's training-latency problem if it generalizes past humans.
  — https://ai.updf.cn/paper-detail/GPS-Gaussian:-Generalizable-Pixel-Wise-3D-Gaussian-Splatting-for-Real-Time-Human-Novel-zheng-zhou-745095916bb16d8e11562ede6ce30846c37e9ebd

## Single-video / generative directions (fallback if sparse-view stalls)

- Stable Video 4D 2.0: single video → multi-view perspectives (12 frames × 4
  views) for rapid 4D asset creation.
  — https://apatero.com/blog/stable-video-4d-20-sv4d-complete-guide-2025
- Room360: smartphone videos → navigable 3D environments via cloud AI pipeline.
  — https://undercodenews.com/room360-revolution-transforming-simple-smartphone-videos-into-immersive-3d-digital-worlds/
- PackUV (Brown): volumetric video compatible with standard video codecs,
  targeting streamable 3D on everyday devices.
  — https://thedebrief.org/explore-a-scene-from-any-vantage-point-you-want-3d-volumetric-video-breakthrough-means-streaming-in-3d-may-soon-be-a-reality/

## Distributed / edge compute

- Real-time multi-view 3D pose with smart edge sensors (lightweight on-device
  models, feature-level fusion at backend) — supports the stage-split
  collaboration model over true GPU pooling.
  — https://www.alphaxiv.org/overview/2106.14729v1
- MeshVision/indview: connected smartphones as collaborative spatial scanners
  with live sync over WebSockets — nearest open-source-shaped precedent.
  — https://github.com/sumanbaul/indview/blob/HEAD/src/readme.md

## What to verify first (ordered)

1. Phone sync accuracy claims (wireless-sync paper) — decides capture design.
2. LiveGS camera count + latency envelope — decides the demo's credibility bar.
3. Mobile-GS rendering load — decides whether the viewer can be fully on-phone.
4. Generalizable (no-per-scene-training) dynamic methods — decides whether live
   mode is a hackathon-timescale feature or a roadmap item.
