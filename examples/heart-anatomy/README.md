# Example: heart anatomy teaching slides

Three ways to put good medical illustrations on a slide, each with labels added as editable
text and with motion where it helps.

| Slide | Illustration | Technique |
|-------|--------------|-----------|
| 2 Four chambers | Servier Medical Art drawing, exported at full resolution from the vector PowerPoint kit | `label_figure.py`: labels in columns with leader lines, fading in one by one |
| 3 Cardiac cycle | The four Servier drawings of the cycle | A 12 s CSS loop highlights each step in turn, like a GIF, with a progress line |
| 4 Ventricular walls | AI-generated with ChatGPT through the browser, then checked against Servier | Same labelling; the check found one anatomical error, which is left unlabelled and noted |

Files: `figures/*.labels.json` (label specs), `figures/manifest.json` (sources, licences,
the AI prompt and what the anatomy check found), `build/slides.html`, `build/deck.css`.

```bash
python ../../skills/medical-figures/scripts/label_figure.py figures/four-chambers.labels.json -o figures/four-chambers.labelled.svg
python ../../skills/medical-figures/scripts/label_figure.py figures/heart-chatgpt.labels.json -o figures/heart-chatgpt.labelled.svg
python ../../skills/html-deck-building/scripts/compose_deck.py --slides build/slides.html --css build/deck.css --title "Heart anatomy (teaching example)" --lang en --cite "Teaching example" -o build/index.src.html
python ../../skills/html-deck-building/scripts/build_deck.py build/index.src.html out/heart-anatomy.html
```

Licences: the Servier Medical Art images are © Servier, licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (credited on each slide). The
AI-generated image is released with this repository under MIT.
