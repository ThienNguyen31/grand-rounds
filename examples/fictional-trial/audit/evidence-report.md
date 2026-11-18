# Evidence audit: nova1-journal-club.html (2026-11-18)
Result: PASS (0 blocking, 1 advisory)

## Scripts

```
# check_claims: dom.html, 7 slides, 14 claims
No findings.

# phi_scan: nova1-journal-club.html
0 text hit(s). Review each; dates in a paper's methods are usually fine, dates of care are not.

# verify_refs: 1 references
- nova1: NO_IDENTIFIER
    · no PMID or DOI: cannot be checked automatically
```

## Advisory
- E-REF · all slides · the only source is a fictional report without PMID/DOI, so
  `verify_refs` returns NO_IDENTIFIER. Expected for this demonstration; a real deck would
  block here.

## Read against the source
Every claim in `evidence/claims.json` was compared with `sources/nova1-fictional-report.md`
at its locator: values, endpoint (RFS), population (ITT), time point (24 months) and the
OS wording ("immature", CI crossing 1) match.

## Not checked
- Nothing.
