# Meta integration plan (hackathon rule compliance)

Rule: the project must incorporate Meta's models (Muse Spark / Wonder / Image /
Voice Transcribe / SAM 3.1 via Meta Model API, Glimmer / Spark Open weights,
Muse Code agent).

## Direct answer: nothing Meta replaces Colab

Meta Model API is fixed-model inference (text/image/segmentation endpoints),
not general GPU compute — you cannot run COLMAP builds or splat training on
it. The open-weights models (Spark Open: 816B MoE) need datacenter-class
hardware, not this laptop. So: **Colab T4 stays as the compute engine; Meta
models become pipeline stages and UX around it.** That is also the stronger
submission story: Meta models doing real work, not bolted on.

## Integration table (priority order)

| # | Model | Role in 3ill | Status |
|---|-------|--------------|--------|
| P0 | SAM 3.1 (`sam-3.1`) | `pipeline/segment.py` (BUILT 2026-11-02, written against cookbook `07_sam/01_api_basics`): `--mode remove` drops dynamic occluders ("person"), `--mode keep` isolates the subject; feeds `reconstruct.py --images-from work/masked`. Verify live: `--limit 3` first, inspect `work/masked/`, then full session | VERIFIED LIVE 2026-11-02: 57/63 session photos masked, 6 unchanged (zero-mask safe copy) |
| P1 | Muse Voice Transcribe (`muse-voice-transcribe-1.0`) | Voice-driven demo on `/capture/`: "snap", "orbit", "next". Small code, big stage charm | to build if time |
| P2 | Muse Wonder (`muse-wonder-1.0`) | Capture-QA agent: which photos add no coverage, where the blind spots are, "retake from the left". Multimodal chat over thumbnails + cover.json | roadmap / if time |
| P3 | Muse Image (`muse-image-1.0`) | Generative blind-spot *preview* (clearly labeled concept, not reconstruction) | roadmap only |
| — | Muse Spark Open / Glimmer | Acknowledge as deployment path; cannot run on hackathon hardware | do not fake |
| ✓ | Muse Code | This repo was built with it (coding agent) | in use |

API facts (snippet-sourced — verify in the dashboard docs before coding):
base `https://api.meta.ai/v1`, `Bearer` auth with `MODEL_API_KEY` from
dev.meta.ai. SAM is called through the OpenAI SDK + `meta_sam_parser`;
cookbook: `meta-models/meta-model-cookbook` (`07_sam/01_api_basics`).
Cost at hackathon scale is cents (SAM ~$2.50/1000 images).

## Implementation notes

- Key handling: `MODEL_API_KEY` env var only, never in the repo or notebook.
- `segment.py` design: read session photos → SAM text-prompt masks
  ("foreground object", "person") → write `work/masked/` + `masks.json` →
  `reconstruct.py --images work/masked` uses them; viewer shows before/after.
- First verification step (human, 5 min): run the cookbook's SAM api_basics
  with your key and paste the exact call shape; then `segment.py` gets written
  against reality, not snippets.

## Submission checklist

- [ ] SAM masking live in the pipeline + visible in the demo
- [ ] Voice commands (or cut explicitly)
- [ ] README/docs credit every Meta model used + Muse Code
- [ ] Bill/usage screenshot from dev.meta.ai as proof of API use
