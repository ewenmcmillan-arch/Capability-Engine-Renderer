# Fonts

No bundled fonts yet. `typography.get_font()` looks here first
(`Standard-Regular.ttf`, `Standard-Bold.ttf`, `Condensed-Regular.ttf`,
`Condensed-Bold.ttf`) before falling back to system DejaVu Sans /
Liberation Sans, and to PIL's built-in default font as a last resort.

Bundling real fonts here would make renders reproducible across
machines regardless of what's installed system-wide — currently the
output depends on whichever system fonts happen to be present.
