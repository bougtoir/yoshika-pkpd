# Software Impacts submission — yoshika

Original Software Publication (OSP) package for submitting **yoshika** to
Elsevier *Software Impacts*.

## Contents

| File | Description |
|------|-------------|
| `yoshika_software_impacts.docx` | Manuscript (OSP template: title, abstract, keywords, code-metadata C1–C9, body, 2 inline figures, references) |
| `yoshika_software_impacts_figures.pptx` | Editable figures, one per slide (Fig. 1–2) |
| `highlights.txt` | Highlights (3–5 bullets, ≤85 chars each) |
| `cover_letter.docx` / `cover_letter.md` | Cover letter |
| `build_si.py` | Regenerates the manuscript + highlights from code and validation data |
| `build_figures_pptx.py` | Regenerates the figures pptx |
| `SIMPAC_OSP_Template.docx` | Reference: the official Software Impacts template |
| `elsevier-vancouver.csl` | Reference citation style |

## Reproducing the manuscript (one command)

From the repository root, with the package installed (`pip install -e .`):

```bash
python paper/software_impacts/build_si.py          # manuscript + highlights
python paper/software_impacts/build_figures_pptx.py # figures pptx
```

All quantitative results (validation GMFE, within-two-fold %, Pearson r) and both
figures are regenerated at build time from `paper/run_validation.py` and
`paper/validation_data.py`; nothing is hard-coded in the manuscript builder.
References are generated in Vancouver style directly from `paper/paper.bib`.

## Submission inputs — status

- **Corresponding-author email + full postal address** (title page and code
  metadata C9): set in `build_si.py` (`EMAIL` / `AFFIL` / `TEL`). Done.
- **Reproducible archive DOI** (code-metadata C3): archived on Zenodo —
  concept DOI `10.5281/zenodo.21816213` (latest), v0.1.0
  `10.5281/zenodo.21816214`. Done. The bundled
  `reproducible_capsule/` also runs as-is on Code Ocean if an executable
  capsule is later preferred.
- **Enabling publication citation** (the *Array* article): published,
  Array 2026;31:101106, DOI `10.1016/j.array.2026.101106`
  (`MANUAL_REFS["onishi2026array"]`). Done.
