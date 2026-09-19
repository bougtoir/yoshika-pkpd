"""Produce a change-highlighted copy of the revised manuscript.

Compares the revised docx against the previously submitted manuscript
(manuscript_array_corrected.docx) at the paragraph level and applies a yellow
highlight to any paragraph in the revised version whose normalized text does not
appear verbatim in the previous version (i.e. new or edited paragraphs). This
gives the editor a clear "what changed" view without hand-tracking every edit.
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_COLOR_INDEX

HERE = Path(__file__).parent
OLD = HERE / "manuscript_array_corrected.docx"
NEW = HERE / "manuscript_array_revised.docx"
OUT = HERE / "manuscript_array_revised_highlighted.docx"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def main() -> None:
    old_paras = {norm(p.text) for p in Document(OLD).paragraphs if p.text.strip()}

    doc = Document(NEW)
    changed = 0
    total = 0
    for para in doc.paragraphs:
        if not para.text.strip():
            continue
        total += 1
        if norm(para.text) not in old_paras:
            changed += 1
            for run in para.runs:
                run.font.highlight_color = WD_COLOR_INDEX.YELLOW

    table_cells = 0
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                table_cells += 1
                for cell_para in cell.paragraphs:
                    for run in cell_para.runs:
                        run.font.highlight_color = WD_COLOR_INDEX.YELLOW

    doc.save(OUT)
    print(
        f"Wrote {OUT}: {changed}/{total} body paragraphs and "
        f"{table_cells} table cells highlighted as changed"
    )


if __name__ == "__main__":
    main()
