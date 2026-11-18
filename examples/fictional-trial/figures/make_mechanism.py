#!/usr/bin/env python3
"""Compose the PD-1/PD-L1 motion graphic from Bioicons cells and antibody.

Cells and antibody are Bioicons SVGs (figures/icons/, fetched with
skills/medical-figures/scripts/bioicons.py; credits in figures/icons/ATTRIBUTION.md).
The receptors are small glyphs drawn here, *underneath* the cell icons, so their stalks
disappear under the membrane and only the heads show in the synapse.

Writes s02-checkpoint.svg. Re-run after changing positions; check frames with check_render.py.
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
ICONS = HERE / "icons"


def icon(name: str, x: float, y: float, w: float, cls: str = "") -> str:
    svg = (ICONS / f"{name}.svg").read_text(encoding="utf-8")
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    h = w * vb[3] / vb[2]
    head = f'<svg x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}"' + (f' class="{cls}"' if cls else "")
    return re.sub(r"<svg\b", head, svg, count=1)


# geometry (viewBox units)
T_X, T_Y, T_W = 160, 190, 470          # T cell icon: centre ≈ (395, 430), right membrane ≈ x 625
U_X, U_Y, U_W = 690, 150, 520          # tumour icon: left membrane ≈ x 705–740
ROW_TCR, ROW_PD = 330, 540

STYLE = """
<style>
  /* Looping motion graphic (16 s). Only transform and opacity animate. Runs while an
     ancestor has class "play" (the deck engine sets it on the active slide). The static
     state is the poster frame: antibody bound, T cell active. */
  .mech .lbl { font-size:24px; fill:#4A5563 }
  .mech .lead { stroke:#9AA3AE; stroke-width:1.5; fill:none }
  .mech .cap { font-size:34px; text-anchor:middle; fill:#1B2430; opacity:0 }
  .mech .c3 { opacity:1 }
  .mech .credit { font-size:15px; fill:#8C96A3 }
  .mech .tumor, .mech .tcell, .mech .ab, .mech .pdl1, .mech .brake, .mech .glow, .mech .gran, .mech .bleb,
  .mech .flash, .mech .inh, .mech .scene, .mech .cap, .mech .prog, .mech .tumor-cell { transform-box:fill-box }
  .mech .brake, .mech .flash, .mech .inh, .mech .gran, .mech .bleb { opacity:0 }
  .mech .prog { transform-origin:left center; transform:scaleX(.6) }
  .mech .tumor-cell, .mech .brake, .mech .flash { transform-origin:center }

  .play .mech .scene      { animation: m-scene 16s linear infinite }
  .play .mech .tumor      { animation: m-tumor 16s cubic-bezier(.25,.7,.25,1) infinite }
  .play .mech .tumor-cell { animation: m-death 16s ease infinite }
  .play .mech .pdl1       { animation: m-pdl1 16s ease infinite }
  .play .mech .glow       { animation: m-glow 16s ease infinite }
  .play .mech .tcell      { animation: m-dim 16s ease infinite }
  .play .mech .brake      { animation: m-brake 16s ease infinite }
  .play .mech .flash      { animation: m-flash 16s ease-out infinite }
  .play .mech .inh        { animation: m-inh 16s linear infinite }
  .play .mech .inh.i2     { animation-name: m-inh2 }
  .play .mech .inh.i3     { animation-name: m-inh3 }
  .play .mech .ab         { animation: m-ab 16s cubic-bezier(.25,.7,.25,1) infinite }
  .play .mech .gran       { animation: m-gran 16s cubic-bezier(.4,0,.2,1) infinite }
  .play .mech .gran.g2    { animation-name: m-gran2 }
  .play .mech .gran.g3    { animation-name: m-gran3 }
  .play .mech .bleb       { animation: m-bleb 16s ease-out infinite }
  .play .mech .c1 { animation: m-c1 16s linear infinite }
  .play .mech .c2 { animation: m-c2 16s linear infinite }
  .play .mech .c3 { animation: m-c3 16s linear infinite }
  .play .mech .c4 { animation: m-c4 16s linear infinite }
  .play .mech .prog { animation: m-prog 16s linear infinite }

  @keyframes m-scene { 0%{opacity:0} 3%{opacity:1} 96%{opacity:1} 100%{opacity:0} }
  @keyframes m-tumor { 0%,6%{transform:translateX(260px)} 20%,100%{transform:none} }
  @keyframes m-death { 0%,74%{transform:none;opacity:1} 86%,100%{transform:scale(.88);opacity:.38} }
  @keyframes m-pdl1  { 0%,32%{transform:none} 36%,52%{transform:translateX(-14px)} 56%,100%{transform:none} }
  @keyframes m-glow  { 0%,20%{opacity:0} 26%,36%{opacity:1} 40%,54%{opacity:0} 58%,92%{opacity:1} 96%,100%{opacity:0} }
  @keyframes m-dim   { 0%,38%{opacity:1} 42%,53%{opacity:.45} 57%,100%{opacity:1} }
  @keyframes m-brake { 0%,38%{opacity:0;transform:scale(.6)} 41%,52%{opacity:1;transform:none} 55%,100%{opacity:0;transform:none} }
  @keyframes m-flash { 0%,19%{opacity:0;transform:scale(.4)} 21%{opacity:1} 27%,100%{opacity:0;transform:scale(1.8)} }
  @keyframes m-inh   { 0%,37%{opacity:0;transform:none} 38%{opacity:1} 46%{opacity:1;transform:translate(-150px,-70px)} 47%,100%{opacity:0;transform:translate(-150px,-70px)} }
  @keyframes m-inh2  { 0%,40%{opacity:0;transform:none} 41%{opacity:1} 49%{opacity:1;transform:translate(-150px,-70px)} 50%,100%{opacity:0;transform:translate(-150px,-70px)} }
  @keyframes m-inh3  { 0%,43%{opacity:0;transform:none} 44%{opacity:1} 52%{opacity:1;transform:translate(-150px,-70px)} 53%,100%{opacity:0;transform:translate(-150px,-70px)} }
  @keyframes m-ab    { 0%,49%{opacity:0;transform:translate(40px,260px)} 52%{opacity:1} 57%,95%{opacity:1;transform:none} 98%,100%{opacity:0;transform:none} }
  @keyframes m-gran  { 0%,67%{opacity:0;transform:none} 68%{opacity:1} 76%{opacity:1;transform:translateX(250px)} 79%,100%{opacity:0;transform:translateX(250px)} }
  @keyframes m-gran2 { 0%,69%{opacity:0;transform:none} 70%{opacity:1} 78%{opacity:1;transform:translateX(240px)} 81%,100%{opacity:0;transform:translateX(240px)} }
  @keyframes m-gran3 { 0%,71%{opacity:0;transform:none} 72%{opacity:1} 80%{opacity:1;transform:translateX(255px)} 83%,100%{opacity:0;transform:translateX(255px)} }
  @keyframes m-bleb  { 0%,78%{opacity:0;transform:none} 82%{opacity:1} 92%{opacity:.8;transform:translate(var(--bx),var(--by))} 96%,100%{opacity:0;transform:translate(var(--bx),var(--by))} }
  @keyframes m-c1 { 0%,3%{opacity:0} 5%,29%{opacity:1} 31%,100%{opacity:0} }
  @keyframes m-c2 { 0%,31%{opacity:0} 33%,53%{opacity:1} 55%,100%{opacity:0} }
  @keyframes m-c3 { 0%,55%{opacity:0} 57%,67%{opacity:1} 69%,100%{opacity:0} }
  @keyframes m-c4 { 0%,69%{opacity:0} 71%,94%{opacity:1} 96%,100%{opacity:0} }
  @keyframes m-prog { from{transform:scaleX(0)} to{transform:scaleX(1)} }
  @media (prefers-reduced-motion:reduce) { .mech *, .mech { animation:none !important } }
</style>"""

parts = [f'<svg viewBox="115 90 1345 815" class="mech" data-poster="0.6" role="img" font-family="Arial, Helvetica, sans-serif" '
         f'aria-label="Animated schematic of PD-1/PD-L1 checkpoint blockade: antigen recognition, PD-L1 inhibition, '
         f'anti-PD-1 blockade, tumour cell killing">', STYLE, '<g class="scene">']

# T-cell side: receptors first (under the cell), then the activation ring, then the cell
parts.append(f'<path d="M560 {ROW_TCR}h88M648 {ROW_TCR}l24 -16M648 {ROW_TCR}l24 16" stroke="#0F7C8A" stroke-width="9" '
             f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
parts.append(f'<path d="M560 {ROW_PD}h86" stroke="#3D5A99" stroke-width="11" stroke-linecap="round"/>'
             f'<circle cx="660" cy="{ROW_PD}" r="14" fill="#3D5A99"/>')
parts.append(f'<circle class="glow" cx="395" cy="430" r="262" fill="none" stroke="#0F7C8A" stroke-width="5" '
             f'stroke-dasharray="4 12" stroke-linecap="round"/>')
parts.append('<g class="tcell">' + icon("t-lymphocyte", T_X, T_Y, T_W) +
             '<text x="372" y="452" text-anchor="middle" font-size="32" font-weight="700" fill="#fff">T cell</text></g>')
parts.append('<g class="brake"><circle cx="470" cy="300" r="38" fill="#fff" stroke="#D9731F" stroke-width="6"/>'
             '<path d="M446 300h48" stroke="#D9731F" stroke-width="9" stroke-linecap="round"/></g>')
for c in ("", " i2", " i3"):
    parts.append(f'<circle class="inh{c}" cx="610" cy="{ROW_PD - 4}" r="9" fill="#D9731F"/>')
for c, (gx, gy, r) in zip(("", " g2", " g3"), ((560, 390, 12), (548, 440, 10), (560, 480, 11))):
    parts.append(f'<circle class="gran{c}" cx="{gx}" cy="{gy}" r="{r}" fill="#0F7C8A" stroke="#fff" stroke-width="2"/>')

# tumour side (moves in as one group): receptors under the cell, then the cell, then its labels
parts.append('<g class="tumor">')
parts.append(f'<path d="M820 {ROW_TCR}h-104M716 {ROW_TCR}v-18M716 {ROW_TCR}v18" stroke="#B8475A" stroke-width="9" '
             f'fill="none" stroke-linecap="round"/><circle cx="688" cy="{ROW_TCR}" r="10" fill="#B8475A"/>')
parts.append(f'<g class="pdl1"><path d="M820 {ROW_PD}h-114" stroke="#D9822B" stroke-width="11" stroke-linecap="round"/>'
             f'<path d="M696 {ROW_PD - 18}a18 18 0 0 1 0 36" stroke="#D9822B" stroke-width="9" fill="none" stroke-linecap="round"/></g>')
parts.append('<g class="tumor-cell">' + icon("cancerous-cell-1", U_X, U_Y, U_W) +
             '<text x="1012" y="472" text-anchor="middle" font-size="32" font-weight="700" fill="#fff">Tumour cell</text></g>')
for bx, by, cx, cy, r in ((120, -90, 1150, 260, 16), (150, 40, 1215, 460, 13), (80, 110, 1120, 650, 15)):
    parts.append(f'<circle class="bleb" style="--bx:{bx}px;--by:{by}px" cx="{cx}" cy="{cy}" r="{r}" fill="#E8B57A"/>')
parts.append('<path class="lead" d="M790 116L700 316"/><text class="lbl" x="796" y="116">MHC + tumour antigen</text>')
parts.append(f'<path class="lead" d="M800 708L700 {ROW_PD + 16}"/><text class="lbl" x="806" y="722">PD-L1</text>')
parts.append('</g>')
parts.append(f'<circle class="flash" cx="670" cy="{ROW_TCR}" r="34" fill="none" stroke="#0F7C8A" stroke-width="5"/>')

# antibody docks on PD-1 from below
parts.append('<g class="ab">' + icon("immuneglobuline_igG_blue", 574, ROW_PD + 8, 100) +
             '<path class="lead" d="M560 790L610 712"/><text class="lbl" x="554" y="804" text-anchor="end" '
             'style="fill:#2A6FB0">anti-PD-1 antibody</text></g>')

# fixed labels on the T-cell side
parts.append(f'<path class="lead" d="M590 116L650 {ROW_TCR - 14}"/><text class="lbl" x="584" y="116" text-anchor="end">T-cell receptor (TCR)</text>')
parts.append(f'<path class="lead" d="M470 708L640 {ROW_PD + 8}"/><text class="lbl" x="464" y="722" text-anchor="end">PD-1</text>')

parts.append('</g>')

# captions and progress line
for i, txt in enumerate(("The T-cell receptor recognises a tumour antigen on MHC",
                         "PD-L1 binds PD-1 and switches the T cell off",
                         "Anti-PD-1 occupies PD-1, so PD-L1 cannot bind",
                         "Released, the T cell kills the tumour cell"), 1):
    parts.append(f'<text class="cap c{i}" x="800" y="850">{txt}</text>')
parts.append('<line x1="500" x2="1100" y1="880" y2="880" stroke="#E3E6EA" stroke-width="4" stroke-linecap="round"/>')
parts.append('<line class="prog" x1="500" x2="1100" y1="880" y2="880" stroke="#0F7C8A" stroke-width="4" stroke-linecap="round"/>')
parts.append("</svg>")

(HERE / "s02-checkpoint.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")
print("s02-checkpoint.svg written")
