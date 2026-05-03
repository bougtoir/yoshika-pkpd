# v1 — CMPB Update Submission Materials

This directory contains the final manuscript and reproduction code for the
CMPB Update (Computer Methods and Programs in Biomedicine Update) submission.

## Contents

```
v1/
├── README.md                  # This file
├── paper.md                   # Manuscript source (Pandoc Markdown, Vancouver citations)
├── paper.bib                  # Bibliography (BibTeX)
├── generate_manuscript.py     # Script to generate .docx and .pptx from figures
├── figures/                   # All manuscript figures (PNG)
│   ├── fig1_compartment_diagram_plasma.png
│   ├── fig2_bupivacaine_comparison.png
│   ├── fig3_all_drugs_comparison.png
│   ├── fig4_bupivacaine_effect.png
│   ├── fig5_bupivacaine_bpt_full.png
│   └── fig6_summary_table.png
└── output/                    # Generated deliverables
    ├── yoshika_CMPB_Update_manuscript.docx
    └── yoshika_CMPB_Update_figures.pptx
```

## Reproducing the .docx and .pptx

```bash
pip install python-docx python-pptx Pillow
cd v1
python generate_manuscript.py
```

This generates:
- `output/yoshika_CMPB_Update_manuscript.docx` — Full manuscript with inline figures and Vancouver-style numbered references (superscript)
- `output/yoshika_CMPB_Update_figures.pptx` — Editable figures (one per slide, widescreen 13.333 x 7.5 in)
