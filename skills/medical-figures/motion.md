# Motion graphics for medical decks (HTML)

Motion earns its place when it shows something a still cannot: the order of events in a
mechanism, a curve unfolding over time, a step in a pathway being blocked. Each motion
should answer "what happens next?". If it only says "look at me", delete it.

## Performance rules (these prevent stutter on presenter laptops)

- Animate only `transform` and `opacity`. They run on the compositor. Never animate
  `width`, `height`, `top`, `left`, `filter: blur()` or SVG attributes frame by frame
  with JavaScript (`setAttribute` in `requestAnimationFrame` on a large SVG stutters).
- `stroke-dashoffset` drawing is fine for **small** paths (connectors, arrows) with
  `pathLength="1"`. For large figures use the wipe reveal below.
- Slide transitions: a short opacity cross-fade (300–450 ms). No clip-path irises, no 3-D
  flips, no blur.
- Keep the slide's content visible until its fade-out ends (remove the "playing" class
  after the transition, not before), or the slide flashes empty.
- Respect `prefers-reduced-motion`: show the final state.
- Measure: a 3-second capture of `requestAnimationFrame` intervals during the animation
  should give a median near 16.7 ms and a 95th percentile under 20 ms.

## Wipe reveal (Kaplan–Meier curves, any large SVG layer)

Two nested boxes translate in opposite directions, so the clipping edge sweeps while the
content stays put. Both transforms are composited, so the reveal stays smooth.

```html
<div class="km">                       <!-- position:relative; fixed aspect ratio -->
  <svg class="base">…axes, labels, risk table…</svg>
  <div class="wipe"><div class="wipe-in"><svg class="curves">…arms…</svg></div></div>
  <svg class="overlay">…24-month marker (a fragment)…</svg>
</div>
```

```css
.km svg, .wipe, .wipe-in { position:absolute; inset:0; width:100%; height:100% }
.wipe    { overflow:hidden; transform:translateX(-71%); will-change:transform }
.wipe-in { transform:translateX(71%); will-change:transform }
.slide.play .wipe, .slide.play .wipe-in {
  transform:none; transition:transform 2.4s cubic-bezier(.45,.05,.3,1) .5s }
```

71 % is the share of the figure's width to the left of time zero. Start the wipe there so
there is no empty pause before the curves appear.

## Step-wise mechanisms

Build the mechanism as one SVG scene. Give each step a class, and advance with the deck's
fragment steps (`data-frag="1"`, `"2"`…), so the presenter controls the pace and can talk
over each step.

```css
.scene .ab   { transform:translate(-220px,-140px); opacity:0; transition:transform .9s, opacity .4s }
.scene.s3 .ab{ transform:none; opacity:1 }          /* antibody docks onto PD-1 at step 3 */
```

A worked example, PD-1/PD-L1 checkpoint blockade in four steps, is in
`examples/checkpoint-blockade.html`. Open it and press → to step.

## Scientific accuracy in motion

- Every arrow, binding and movement corresponds to a sentence in a cited source; put that
  sentence in the speaker notes.
- Keep the relative sizes and compartments right: cytoplasm vs membrane vs extracellular.
  Ligands bind receptors on the correct cell.
- Show the drug at its real site of action (anti-PD-1 binds PD-1 on the T cell; anti-PD-L1
  binds PD-L1 on the tumour or myeloid cell).
- Do not imply a time scale. Add "schematic, not to scale" in the notes, not on the slide.

## PPTX

PowerPoint animations are not portable between versions. For PPTX, show a mechanism as
2–4 static panels on one slide, or one step per slide, and let the presenter's clicks
stand in for motion.
