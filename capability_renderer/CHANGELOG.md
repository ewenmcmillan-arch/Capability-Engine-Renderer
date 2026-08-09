# Changelog

## Unreleased — bug fixes from real-GPX testing

Found and fixed while testing against a real Strava-exported GPX
(Afternoon Run, 4.85 mi):

- **Trace legend / marker collision (pre-existing in locked v1.2):**
  the "Start / finish" marker key was positioned at a hardcoded
  y-coordinate that assumed a fixed legend height, so it overlapped
  the "Below mission pace" label whenever that entry's shorter pitch
  left less room than assumed. Now derives its position from where
  the legend entries actually finished stacking.
  `geometry.TRACE_LEGEND_BOX` extended (792→815) to give it room.
- **HR recovery panel showed fabricated defaults:** `panels/recovery.py`
  read `cfg.get('hr_recovery_start', '145')`-style fallbacks directly
  from config, bypassing the computed metrics — any session with no
  real recovery reading rendered placeholder numbers (145/115/-17/-30)
  indistinguishable from genuine data. `metrics.hr_recovery()` now
  returns `{"available": False}` when no recovery fields are present,
  and the panel shows "No recovery data supplied" instead of inventing
  numbers. Recovery is a genuine external measurement (e.g. Huawei
  Health, HR monitored for two minutes post-run) — not derivable from
  GPX even in principle, since GPS recording stops before recovery
  monitoring would.
- Added cadence support: `parse_gpx()` now reads the GPX's
  `gpxtpx:cad` extension, `metrics.cadence_summary()` replaces the
  old `NotImplementedError` stub. Not yet shown on the card — the
  metrics strip is pixel-locked at 5 fixed cells with no room for a
  6th; computed and available in `computed_metrics` for a future
  panel revision.

## Unreleased — structural refactor (renderer.py → capability_renderer/)

This release does **not** implement the v1.4/v1.5 roadmap features
(automatic layout, responsive panels, theme engine, SVG export). It
is the modularisation groundwork those depend on: splitting the
single-file `render-2.py` (v1.2 locked layout) into the target
package structure with one responsibility per module and one panel
per report section.

**Pixel-parity goal:** every panel reproduces the locked v1.2 layout
from `Capability_Snapshot_Renderer_Memory_Locked_Baseline.md`
exactly — same coordinates, same colours, same text. This is a
structural refactor, not a redesign.

Changes:
- Renamed the package from the originally planned `renderer/` to
  `capability_renderer/`, making it a reusable engine rather than a
  single script.
- Split the monolithic `render.py` / `render-2.py` into:
  `render.py` (orchestrator only), `metrics.py`, `layout.py`,
  `graphics.py`, `typography.py`, `theme.py`, `geometry.py`,
  `validation.py`, `export.py`.
- Added `models/` (Mission, Panel, RunMetrics, Route, Theme) as a
  typed layer over the raw config JSON.
- Added `panels/` — one module per card section (header, mission,
  assessment, trace, verdict, summary, splits, recovery, elevation,
  footer), each with a consistent `render(img, draw, cfg, metrics,
  theme, **kwargs)` signature so a new report type is one new panel
  module, not a change to the renderer itself.
- Added `assets/themes/{default,dark,print}.json` — default/dark are
  the locked palette; print is a draft, not yet visually approved.
- Added a real pytest suite (`tests/`) covering layout, metrics,
  panel rendering, and an end-to-end render + validation-failure
  check.
- `metrics.py` includes stubs for cadence, VO2 estimate, training
  load, fatigue, and efficiency — each raises `NotImplementedError`
  with the specific data gap, rather than a fabricated number,
  because none are computable from the current GPX/JSON schema.
- PDF/SVG export are stubbed in `export.py` (raise
  `NotImplementedError`) — the data-flow seam exists per the target
  architecture, but only PNG is implemented.

Known gaps carried over from the monolith (not introduced by this
refactor):
- No automated recovery-detection from GPX (HR recovery values are
  still config-supplied, not computed from a detected stop).
- No real brand assets yet (logos/icons) — `graphics.crest()`
  vector fallback is used throughout.

## v1.2 (prior, monolithic `render-2.py`)

Locked visual baseline. See
`Capability_Snapshot_Renderer_Memory_Locked_Baseline.md` for the
full layout specification this refactor reproduces.
