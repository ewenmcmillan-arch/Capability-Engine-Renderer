# Logos

Not yet supplied:
- `capability_master.svg`
- `capability_master.png`
- `watermark_light.png`
- `watermark_dark.png`
- `favicon.png`

Until these exist, `graphics.crest()` draws a deterministic vector
crest as a fallback, and `graphics.logo()` uses it automatically
when the asset path doesn't resolve. `validation.validate_assets()`
reports the gap as a warning, not an error, so rendering isn't
blocked on missing brand art.
