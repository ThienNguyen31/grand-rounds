# Example: heart anatomy teaching slide

A medical illustration drawn in code rather than pasted as a picture or a video:
`figures/heart.svg` is a schematic frontal section with the four chambers, the tricuspid and
mitral valves with chordae and papillary muscles, the semilunar valves, the venae cavae,
pulmonary trunk and arteries, aorta and pulmonary veins. The left ventricular wall is drawn
thicker than the right.

Two loops run while the slide is shown:

- **blood flow**: blue (deoxygenated) and red (oxygenated) dots move along the vessel centre
  lines with `offset-path`, 8 s per circuit;
- **cardiac cycle**: atria contract, then ventricles, and the atrioventricular leaflets
  close during ventricular systole, once per second.

Labels sit outside the heart with leader lines. The static state is a poster frame, so
PDF export and reduced-motion viewers still get a complete diagram.

```bash
python ../../skills/html-deck-building/scripts/compose_deck.py --slides build/slides.html --css build/deck.css --title "Heart anatomy (teaching example)" --lang en --cite "Teaching example. Illustration drawn in code for MedSlides." -o build/index.src.html
python ../../skills/html-deck-building/scripts/build_deck.py build/index.src.html out/heart-anatomy.html
```

Schematic, not to scale. Before teaching from it, have the anatomy checked by a colleague,
as you would any figure you draw yourself.
