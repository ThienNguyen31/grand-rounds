# Slop audit: nova1-journal-club.html (2026-11-18)
Result: PASS (0 blocking, 3 advisory)

Linter on the rendered DOM (`build/render/dom.html`):

```
# lint_slop: dom.html: 0 blocking, 3 advisory
- S18 [advisory] slide 3: 82 words of body text (limit 40, en)
- S18 [advisory] slide 4: 43 words of body text (limit 40, en)
- S18 [advisory] slide 7: 48 words of body text (limit 40, en)
```

| ID | Slide | What is on the slide | Fix |
|----|-------|----------------------|-----|
| S18 | 3 | 82 words, mostly labels inside the trial schema | Kept: diagram labels, not paragraphs |
| S18 | 4 | 43 words in the CONSORT boxes | Kept: required by CONSORT |
| S18 | 7 | 48 words in three take-home statements | Kept: closing slide, read aloud |

Visual pass over `build/render/contact.html`: no eyebrows, no presenter cues, no card grids,
no decorative icons; source credit in the footer only.
