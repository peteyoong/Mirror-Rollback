# GENE KEYS IP POLICY — The Mirror
Author: Product owner sign-off, Session-2 (2026-07-22)
Applies to: All Gene Keys content shipped inside The Mirror
Build marker: gene-keys-ip-policy-v1

---

## Position

The Mirror will present a Gene Keys lens using **original interpretive
copy only**. We reuse the underlying gate-activation calculation (which
Gene Keys shares with Human Design as astronomical fact, not proprietary
authorship) but we do **not** reproduce, paraphrase, or scrape any
copyrighted or proprietary Gene Keys source material.

Reasoning: the Gene Keys system was authored by Richard Rudd. The gene
key numbers, the Shadow/Gift/Siddhi triad structure, and the sphere-
sequence names (Activation / Venus / Pearl) are conventional structural
labels used across the tradition and are usable descriptively. The
specific interpretive text for each key, sphere, and sequence in his
published works is copyrighted.

---

## Permitted

- Structural terminology needed to identify what the user is looking at:
  - Gene Key numbers (1..64)
  - Sphere names: Life's Work, Evolution, Radiance, Purpose,
    Attraction, IQ, EQ, SQ, Core, Vocation, Culture, Brand, Pearl
  - Sequence names: Activation Sequence, Venus Sequence, Pearl Sequence,
    Golden Path
  - Shadow / Gift / Siddhi labels
  - Line 1..6 labels
- Personal-Mirror-authored interpretations of each key, sphere, and line
- Personal-Mirror-authored reflection questions
- Personal-Mirror-authored grounded contemplations and experiments
- Attribution of the framework to the Gene Keys tradition (without quoting)
- Cross-references to the shared HD activation calculation

## Not permitted

- Copying source descriptions verbatim from `genekeys.com`, published
  books, or any Gene Keys product
- Long verbatim quotations from copyrighted materials
- Close paraphrases that reproduce the specific literary phrasing of
  proprietary source passages
- Scraped or imported commercial Gene Keys content, including PDFs,
  audio transcriptions, or third-party summaries derived from those
- Presenting proprietary wording as Mirror-authored material

---

## Enforcement

- Every Gene Keys interpretive claim ships with a `content_provenance`
  field on its `EvidenceRef` set to one of:
  - `mirror_original` — written from scratch inside The Mirror
  - `structural_label` — a permitted structural term (e.g. "Shadow of Gene Key 25")
- A CI-side content-similarity test (Session-4) will flag any Mirror
  copy whose Jaccard-token overlap with a small held-out corpus of
  publicly-available Gene Keys source text exceeds 0.35.
- Reviewers must reject PRs that add Gene Keys copy without
  `content_provenance: "mirror_original"`.

---

## Attribution

Where the Gene Keys tradition is referenced, use language such as:

  "Gene Keys is a contemplative framework developed within the Gene Keys
  tradition. The interpretations below are The Mirror's own reading
  of your calculated activations and sphere placements — they are not a
  reproduction of the published Gene Keys material."

Do not use trademark or ® symbols with "Gene Keys" — descriptive use
only.

---

## Review

This policy is reviewed on the following triggers:
- Any user report of derivative Mirror copy
- Any change to the Gene Keys tradition's public licensing terms
- Session-4 (Gene Keys lens rebuild) — final review before deploy
