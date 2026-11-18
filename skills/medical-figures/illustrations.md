# Medical illustrations and their licences

Use illustrations to explain, not to decorate. Every image goes into `figures/manifest.json`
with its source URL, author, licence and the attribution text you printed on the slide.

## Which route

| Need | First choice | Then |
|------|--------------|------|
| Standard anatomy, organs, physiology, cells | **Servier Medical Art** (accurate, drawn by medical illustrators, CC BY 4.0) | AI-generated, if Servier has nothing suitable (`ai-images.md`) |
| A specific view, style or composition no library has | **AI-generated**, checked against a reference (`ai-images.md`) | Commission or draw |
| Molecules, receptors, lab icons | Bioicons, Servier | Simple SVG drawn yourself |
| Schematic shapes (a cell, a receptor, an antibody) | Simple SVG drawn yourself | — |

Don't draw organs freehand in SVG: hand-coded anatomy looks crude next to illustrator
artwork. Code is for labels, arrows, highlights and motion on top of a good illustration.

## Libraries

| Library | What it has | Licence | Attribution you must show |
|---------|-------------|---------|---------------------------|
| Servier Medical Art (smart.servier.com) | anatomy, organs, cells, pathology, physiology sequences, lab equipment | CC BY 4.0, including commercial use | "Servier Medical Art (smart.servier.com), CC BY 4.0", plus "labels added" or "modified" |
| Bioicons (bioicons.com) | molecules, cells, lab icons (SVG) | per icon: CC0, CC BY, CC BY-SA, MIT | as stated on each icon's page |
| NIH BioArt (bioart.niaid.nih.gov) | infectious disease, immunology, lab | mostly public domain; check each item | credit NIAID NIH BioArt |
| Wikimedia Commons | anatomy plates, historical images | per file | as stated on the file page |
| PubMed Central open-access articles | figures from CC BY papers | per article (check the licence line) | citation + licence |

## Servier Medical Art at full resolution

The PNGs on each image page are small (about 400–600 px). Each page also links a themed
PowerPoint kit (`SMART-Heart-physiology.pptx`, `SMART-Heart-pathophysiology.pptx`, …) in
which every drawing is a **vector group** of native shapes. Export the group you need at any
size:

1. Search `https://smart.servier.com/?s=<term>`. Open an image page and find the `.pptx`
   link under it, then download the kit.
2. List the groups on the slide with python-pptx (`slide.shapes`: name, position, size).
3. Export one group, keeping its aspect ratio. With PowerPoint (Windows), copy the group
   into a new presentation whose slide size equals the group's size, and export that slide
   at 2400 px wide. With LibreOffice, render the slide to PDF and crop it with
   `pdf_figures.py raster`. Do not use `Shape.Export`: it ignores the aspect ratio.
4. Convert to JPEG (white background) or keep PNG (transparent), at about twice the
   display size.
5. Add labels with `scripts/label_figure.py`, not inside the image.

Servier sequences (the cardiac cycle in four drawings, for example) make good motion
graphics: show them side by side and highlight each step in turn with a CSS loop
(see the heart-anatomy example in the MedSlides repository).

## Rules

- **No licence, no use.** "Found on Google Images" is not a licence.
- CC BY-SA images make the slide that uses them share-alike. Avoid them in decks that will
  be sold.
- AI-generated illustrations are drafts until their anatomy has been checked. Never use
  them for histology, imaging or anything a reader could take as a real finding
  (`ai-images.md`).
- Patient images (clinical photos, radiology, histology) belong to the patient and the
  hospital. Use them only with consent recorded in the brief, with identifiers removed from
  the pixels, including DICOM overlays.
- Keep proportions honest in anything you draw yourself: an antibody is not larger than a
  T cell. Label every part the talk mentions, and nothing else.
