# v1 — CMPB Update Submission Materials

This directory contains the final manuscript and figure reproduction code for the
CMPB Update (Computer Methods and Programs in Biomedicine Update) submission.

## Contents

```
v1/
├── README.md                  # This file
├── paper.md                   # Manuscript source (Pandoc Markdown)
├── paper.bib                  # Bibliography (BibTeX)
├── reproduce_figures.py       # Reproduce all manuscript figures using yoshika
├── figures/                   # Manuscript figures (PNG, 300 dpi)
│   ├── fig1_compartment_diagram_plasma.png
│   ├── fig2_bupivacaine_comparison.png
│   ├── fig3_all_drugs_comparison.png
│   ├── fig4_bupivacaine_effect.png
│   ├── fig5_bupivacaine_bpt_full.png
│   └── fig6_summary_table.png
└── output/                    # Pre-generated submission files
    ├── yoshika_CMPB_Update_manuscript.docx
    └── yoshika_CMPB_Update_figures.pptx
```

## Reproducing the figures

```bash
pip install yoshika matplotlib pandas
cd v1
python reproduce_figures.py
```

This regenerates all six figures in `figures/` using the yoshika PKPD package
with bupivacaine 150 mg / 70 kg as the reference scenario.
