---
name: medical-figures
description: Use when a medical slide needs a figure: reusing a Kaplan–Meier curve, forest plot or diagram from a paper PDF, drawing a CONSORT/PRISMA flow, trial schema, timeline or algorithm, charting trial data, finding a licensed anatomical or molecular illustration, or animating a mechanism, pathophysiology or drug action.
---

# Medical figures

## Overview

A figure is evidence. Its numbers come from `evidence/claims.json`, its shapes from a
source, and its provenance goes into `figures/manifest.json`. Choose the cheapest route
that keeps it exact:

| Need | Route | Reference |
|------|-------|-----------|
| A figure that exists in the source PDF (KM, forest plot, CONSORT) | **Lift the vectors**, recolour to the theme; never redraw a curve | `reuse-from-pdf.md` |
| A diagram the paper describes but doesn't draw well (trial schema, flow, timeline, algorithm) | **Rebuild as SVG** from claims only | `diagrams.md` |
| A comparison of numbers (rates, subgroup effects) | **Chart** from claims: dot/dumbbell, bars, forest | `diagrams.md` |
| Anatomy, cells, molecules, devices | **Licensed library** (Servier Medical Art, Bioicons, NIH BioArt), or a **schematic drawn in SVG** with labels outside the structures | `illustrations.md`, `examples/heart-chambers.html` |
| A mechanism or physiology that unfolds over time (binding, signalling, blood flow) | **Motion graphic** coded in SVG/CSS (HTML only): click-stepped or looping like a video; static step panels for PPTX | `motion.md`, `examples/checkpoint-blockade.html` |

## Rules

- **No invented data.** A curve, bar or box number that is not in `claims.json` is not
  drawn. A CONSORT box with an unknown number shows "not reported".
- **Reused figures keep their content.** You may recolour, crop to one panel, and add
  overlays (a marker at 24 months, a shaded interval). You may not delete censor ticks,
  numbers at risk or axis labels. Overlays use values from claims.
- **Credit every figure** with a short source line in the deck (`Source: Long GV et al.
  N Engl J Med 2026; Fig. 1A`). Do not describe what you did to it on the slide
  ("recoloured", "redrawn"): that goes in the manifest.
- **Colours follow the entity.** Intervention and control keep one colour each throughout
  the deck. Take colours from `theme/theme.json`.
- **Format.** HTML decks inline SVG (animate with transforms; see `motion.md`). PPTX decks
  take SVG (PowerPoint 2019+) with a PNG fallback at 300 dpi.

## Manifest: `figures/manifest.json`

```json
{"figures": [{
  "file": "s05-km-rfs.svg", "slide": 5, "kind": "reused-vector",
  "source": "long2026", "locator": "p. 6, Fig. 1A",
  "licence": "© NEJM; reused for non-commercial education with citation",
  "modifications": "cropped to panel A; arm colours mapped to theme; curves split into a separate layer",
  "claims": ["c07", "c08"]
}]}
```

`kind` is one of `reused-vector`, `reused-raster`, `rebuilt`, `chart`, `illustration`,
`animation`. A licence field that is empty or "unknown" is a finding for the audit.

## Script

`scripts/pdf_figures.py` (PyMuPDF). Run `--help`. Commands: `list`, `extract`, `raster`,
`colors`, `split`.
