# Medical illustrations and their licences

Use illustrations to explain, not to decorate. Every image goes into `figures/manifest.json`
with its source URL, author, licence and the attribution text you printed on the slide.

| Library | What it has | Licence | Attribution you must show |
|---------|-------------|---------|---------------------------|
| Servier Medical Art (smart.servier.com) | anatomy, organs, cells, pathology, lab equipment | CC BY 4.0 | "Servier Medical Art (smart.servier.com), CC BY 4.0", plus "modified" if you changed it |
| Bioicons (bioicons.com) | molecules, cells, lab icons (SVG) | per icon: CC0, CC BY, CC BY-SA, MIT | as stated on each icon's page |
| NIH BioArt (bioart.niaid.nih.gov) | infectious disease, immunology, lab | mostly public domain; check each item | credit NIAID NIH BioArt |
| Wikimedia Commons | anatomy plates, historical images | per file | as stated on the file page |
| PubMed Central open-access articles | figures from CC BY papers | per article (check the licence line) | citation + licence |

Rules:

- **No licence, no use.** "Found on Google Images" is not a licence.
- CC BY-SA images make the slide that uses them share-alike. Avoid them in decks that will
  be sold.
- AI-generated "medical illustrations" are not evidence. Use them only if the user asks and
  the anatomy has been checked. Never use them for histology, imaging or anything a reader
  could take as a real finding.
- Patient images (clinical photos, radiology, histology) belong to the patient and the
  hospital. Use them only with consent recorded in the brief, with identifiers removed from
  the pixels, including DICOM overlays.

## Drawing your own

Simple schematic shapes (a cell, a receptor, an antibody, a lipid nanoparticle) can be drawn
as SVG. Keep proportions honest: an antibody is not larger than a T cell. Label every part
the talk mentions, and nothing else.
