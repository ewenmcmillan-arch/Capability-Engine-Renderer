# Capability Engine — Renderer

Renders Capability Engine mission-snapshot cards from a run/walk GPX
file plus a JSON config: distance, pace, heart rate, elevation,
splits, and a GPX-derived route trace, laid out on a fixed 1080×1620
card. Originally a single-file script (`render.py`/`render-2.py`,
v1.2 "locked baseline" layout); this repo is the rebuilt, tested,
modular version of that same locked layout.

## Status

Working and tested — not a prototype. See `capability_renderer/CHANGELOG.md`
for the full detail; summary below.

## What's in this repo

`capability_renderer/` — the package. Panel-based architecture
(`panels/`, one file per card section), pure functions split by
responsibility (`layout.py` computes coordinates, `graphics.py` only
draws, `metrics.py` only calculates, `typography.py` only handles
fonts) instead of one monolithic script. See
`capability_renderer/README.md` for how to run and test it, and how
to add a new report type.

## Work done so far

**Structural refactor.** Split the original single-file renderer into
the current package. Verified pixel-parity against the original
locked v1.2 output before trusting the refactor — found and fixed two
real bugs the parity check surfaced (a `TextBlock` height miscalculation
that shifted stacked mission-panel text, and a metric-strip cell
boundary that got truncated to int and shifted glyph centres by
sub-pixel amounts). 99.99% pixel-identical to the original after
fixing both.

**Real-GPX testing**, not just synthetic fixtures. Rendered an actual
Strava-exported GPX (3,101 trackpoints) end-to-end. That surfaced two
real bugs synthetic test data hadn't caught:
- The trace-panel legend's "Start / finish" marker key was positioned
  at a hardcoded coordinate that assumed a fixed legend height —
  collided with the "Below mission pace" label above it whenever that
  entry's shorter pitch left less room than assumed. Pre-existing in
  the original locked v1.2 design, not introduced by the refactor.
  Fixed by deriving the marker position from where the legend actually
  finished stacking.
- The Heart Rate Recovery panel had hardcoded placeholder numbers
  (145/115/-17/-30) as silent fallbacks — any session without a real
  recovery reading rendered fabricated data indistinguishable from
  genuine. Recovery is a real external measurement (e.g. Huawei
  Health, HR monitored for two minutes post-run) — not derivable from
  GPX even in principle, since GPS recording stops before recovery
  monitoring would. Fixed to show "No recovery data supplied" instead
  of inventing numbers.

**Cadence support added** — `parse_gpx()` now reads the GPX's
`gpxtpx:cad` extension; `metrics.cadence_summary()` computes avg/max.
Not yet shown on the card itself (the metrics strip is pixel-locked
at 5 fixed cells); computed and available for a future panel.

**Real brand assets**, generated from the "Best Prepared — The Ageing
Runner" badge artwork:
- `capability_master.png` / `.svg` — full-colour raster and a true
  single-colour vector (auto-traced, cleaned up) master logo
- `favicon.png` / `favicon_64.png` — thumbnails
- `watermark_dark.png` / `watermark_light.png` — heavily blurred and
  dimmed before compositing, specifically so the source artwork's
  text/linework doesn't stay legible and compete with real card text
  sitting on top of it (an early attempt at just reducing opacity
  looked wrong for exactly that reason — verified by compositing onto
  the real dark panel background, not just eyeballing the source)

See `capability_renderer/assets/logos/README.md` for the exact
tradeoffs on each (the SVG is single-colour — vectorizing a
photographic illustration means losing the colour/gradient, not a
setting that can be tuned around).

**Test suite**: 23 tests (`capability_renderer/tests/`), covering
layout math, metrics calculations, every panel rendering without
error, and an end-to-end render + a validation-failure case. All
passing.

## Relationship to Capability-Engine

This repo is wired into the main
[`Capability-Engine`](https://github.com/ewenmcmillan-arch/Capability-Engine)
repo as a git submodule at `renderer/` (branch `develop/v4.8`),
invoked via `tools/renderer.py`'s `render_snapshot()`. A fresh clone
of that repo needs `git submodule update --init` to actually fetch
this content — the submodule pointer alone doesn't.
