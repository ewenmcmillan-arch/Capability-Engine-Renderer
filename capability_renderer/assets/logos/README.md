# Logos

Real assets, generated from the "Best Prepared — The Ageing Runner"
badge artwork:

- `capability_master.png` — full circular badge, transparent corners,
  full colour (masked from the source 1254×1254 artwork)
- `capability_master.svg` — true vector, auto-traced from the same
  artwork (potrace, high-contrast threshold + speckle cleanup).
  **Single colour (black on transparent)** — potrace traces shapes,
  not photographic tone or gradients, so the sunset sky and colour
  palette couldn't come along; that's the real tradeoff for getting
  an actual scalable vector rather than a raster. Recolour by
  editing the single `fill="#000000"` attribute on the wrapping
  `<g>` element — the whole mark uses one fill throughout.
  Legible down to favicon sizes for the main silhouette shapes;
  the ring text (e.g. "STRONGER TODAY...") stops being readable
  below roughly 120px, same limitation the PNG has at that size —
  that's the amount of detail in the design, not a tracing artifact.
- `favicon.png` — 256×256 resize of the master, for small-icon use
- `favicon_64.png` — 64×64, for true browser-favicon-sized contexts
- `watermark_dark.png` — heavily blurred + desaturated + low-alpha
  (peak ~16%) gold-tinted version, for the renderer's dark card
  background. Deliberately blurred *before* alpha reduction so the
  badge's small text/linework doesn't remain legible at low
  opacity — a watermark that still reads as text competes with real
  card content sitting on top of it. See graphics.watermark()'s
  docstring for how this gets composited.
- `watermark_light.png` — same treatment, dark-tinted, for a future
  light/print theme background

`graphics.crest()` remains as the deterministic vector fallback for
any context where these asset files aren't available.
