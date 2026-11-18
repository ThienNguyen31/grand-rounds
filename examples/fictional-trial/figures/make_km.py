#!/usr/bin/env python3
"""Generate the demo deck's Kaplan–Meier figure from FICTIONAL, deterministic data.

Real decks lift the published figure from the paper (medical-figures → reuse-from-pdf.md).
This demo has no paper, so it simulates two arms, computes the Kaplan–Meier estimate and
numbers at risk, and writes two layers (base + curves) for the wipe reveal.

Writes one figure per end point (recurrence-free and overall survival), each as
s05-km-<name>.base.svg + s05-km-<name>.curves.svg, and prints the values the claims ledger uses.
"""
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).parent
INT, CTL, INK, MUTED, GRID = "#C8372D", "#56677F", "#1B2430", "#66707C", "#E3E6EA"
W, H = 900, 640
X0, X1, Y0, Y1 = 120, 860, 440, 40        # plot box: x at 0 and 36 months; y at 0 % and 100 %
MAXM = 36
xm = lambda m: X0 + (X1 - X0) * m / MAXM
yp = lambda p: Y0 - (Y0 - Y1) * p


def simulate(n, hazards, seed):
    """Piecewise-exponential event times (hazards: [(until_month, rate)]) + uniform censoring 18–36 mo."""
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        u = (i + 0.5) / n
        target = -math.log(u)           # cumulative hazard at the event
        t, cum, prev = None, 0.0, 0.0
        for until, rate in hazards:
            seg = (until - prev) * rate
            if cum + seg >= target:
                t = prev + (target - cum) / rate
                break
            cum, prev = cum + seg, until
        t = t if t is not None else 1e9
        c = 18 + 18 * rnd.random()
        out.append((min(t, c), t <= c))
    return sorted(out)


def km(data):
    n, s, steps, censors = len(data), 1.0, [(0.0, 1.0)], []
    at_risk = n
    i = 0
    while i < len(data):
        t = data[i][0]
        d = c = 0
        while i < len(data) and data[i][0] == t:
            d += data[i][1]
            c += not data[i][1]
            i += 1
        if d:
            s *= 1 - d / at_risk
            steps.append((t, s))
        if c:
            censors.append((t, s))
        at_risk -= d + c
    return steps, censors


def s_at(steps, m):
    return [s for t, s in steps if t <= m][-1]


def at_risk(data, m):
    return sum(1 for t, _ in data if t >= m)


def path(steps):
    d = f"M{xm(0):.1f} {yp(1):.1f}"
    for (t0, s0), (t1, s1) in zip(steps, steps[1:]):
        if t1 > MAXM:
            break
        d += f"H{xm(t1):.1f}V{yp(s1):.1f}"
    return d + f"H{xm(min(MAXM, 34.5)):.1f}"


def figure(name, arms, ylabel):
    res = {k: km(v) for k, v in arms.items()}
    base = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Arial, sans-serif">']
    for p in (0, .25, .5, .75, 1):
        base.append(f'<line x1="{X0}" x2="{X1}" y1="{yp(p):.1f}" y2="{yp(p):.1f}" stroke="{GRID}" stroke-width="1.5"/>')
        base.append(f'<text x="{X0 - 14}" y="{yp(p) + 7:.1f}" font-size="20" fill="{MUTED}" text-anchor="end">{int(p * 100)}</text>')
    for m in range(0, MAXM + 1, 6):
        base.append(f'<line x1="{xm(m):.1f}" x2="{xm(m):.1f}" y1="{Y0}" y2="{Y0 + 8}" stroke="{MUTED}" stroke-width="1.5"/>')
        base.append(f'<text x="{xm(m):.1f}" y="{Y0 + 32}" font-size="20" fill="{MUTED}" text-anchor="middle">{m}</text>')
    base.append(f'<line x1="{X0}" x2="{X1}" y1="{Y0}" y2="{Y0}" stroke="{MUTED}" stroke-width="1.5"/>')
    base.append(f'<text x="{(X0 + X1) / 2}" y="{Y0 + 62}" font-size="20" fill="{MUTED}" text-anchor="middle">Months since randomisation</text>')
    base.append(f'<text transform="translate(34 {(Y0 + Y1) / 2}) rotate(-90)" font-size="20" fill="{MUTED}" text-anchor="middle">{ylabel}</text>')
    base.append(f'<text x="8" y="{H - 64}" font-size="18" fill="{INK}" font-weight="700">At risk</text>')
    for row, (k, col, label) in enumerate((("int", INT, "Vaccine"), ("ctl", CTL, "Placebo"))):
        y = H - 34 + row * 28
        base.append(f'<text x="8" y="{y}" font-size="18" fill="{col}" font-weight="700">{label}</text>')
        for m in range(0, MAXM + 1, 6):
            base.append(f'<text x="{xm(m):.1f}" y="{y}" font-size="18" fill="{INK}" text-anchor="middle">{at_risk(arms[k], m)}</text>')
    base.append("</svg>")

    curves = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Arial, sans-serif">']
    for k, col, label in (("ctl", CTL, "Placebo + anti-PD-1"), ("int", INT, "Vaccine + anti-PD-1")):
        steps, cens = res[k]
        curves.append(f'<path d="{path(steps)}" fill="none" stroke="{col}" stroke-width="4"/>')
        for t, s in cens[::max(1, len(cens) // 14)]:   # a readable sample of censor ticks
            if t <= MAXM:
                curves.append(f'<line x1="{xm(t):.1f}" x2="{xm(t):.1f}" y1="{yp(s) - 6:.1f}" y2="{yp(s) + 6:.1f}" stroke="{col}" stroke-width="2"/>')
        # direct labels where they cannot touch a curve: intervention above its curve early on,
        # control below the lowest point its curve reaches under the label (months 25-35)
        if k == "int":
            curves.append(f'<text x="{xm(8):.1f}" y="{yp(s_at(steps, 8)) - 18:.1f}" font-size="21" font-weight="700" fill="{col}">{label}</text>')
        else:
            lowest = min(s_at(steps, m / 2) for m in range(50, 71))
            curves.append(f'<text x="{xm(35):.1f}" y="{yp(lowest) + 38:.1f}" font-size="21" font-weight="700" fill="{col}" text-anchor="end">{label}</text>')
    curves.append("</svg>")
    (HERE / f"s05-km-{name}.base.svg").write_text("\n".join(base), encoding="utf-8")
    (HERE / f"s05-km-{name}.curves.svg").write_text("\n".join(curves), encoding="utf-8")
    vals = {k: {"s24": round(100 * s_at(res[k][0], 24), 1), "events": sum(e for _, e in arms[k]),
                "at_risk": {m: at_risk(arms[k], m) for m in range(0, 37, 6)}} for k in arms}
    for k in arms:
        vals[k]["y24"] = round(yp(vals[k]["s24"] / 100), 1)
    return vals


out = {
    "rfs": figure("rfs", {"int": simulate(575, [(6, 0.0160), (99, 0.0075)], seed=11),
                          "ctl": simulate(287, [(99, 0.0160)], seed=12)}, "Recurrence-free (%)"),
    "os": figure("os", {"int": simulate(575, [(99, 0.0048)], seed=11),
                        "ctl": simulate(287, [(99, 0.0060)], seed=12)}, "Alive (%)"),
    "geometry": {"x_month0": X0, "px_per_month": (X1 - X0) / MAXM, "x_24": xm(24), "y_0pct": Y0, "y_100pct": Y1},
}
print(json.dumps(out, indent=1))
