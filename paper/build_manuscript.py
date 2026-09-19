"""Build the Array manuscript docx from paper.md.

Resolves LaTeX-style \\autoref{}/\\label{} cross-references into literal
"Figure N" / "Table N" numbering (figures and tables numbered separately, in
order of first appearance of their label), then runs pandoc with citeproc so
references are formatted in Elsevier (Vancouver) numbered style.

Usage:
    python build_manuscript.py            # clean version
    python build_manuscript.py --tag      # also emit change-tagged version
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from format_manuscript_tables import replace_flattened_tables

HERE = Path(__file__).parent
SRC = HERE / "paper.md"
BIB = HERE / "paper.bib"
CSL = HERE / "elsevier-vancouver.csl"

LABEL_RE = re.compile(r"\\label\{((?:fig|tab):[a-z_0-9]+)\}")
AUTOREF_RE = re.compile(r"\\autoref\{((?:fig|tab):[a-z_0-9]+)\}")


def assign_numbers(text: str) -> dict[str, str]:
    """Map each label to 'Figure N' / 'Table N' by first-appearance order."""
    numbers: dict[str, str] = {}
    fig_n = tab_n = 0
    for m in LABEL_RE.finditer(text):
        label = m.group(1)
        if label in numbers:
            continue
        if label.startswith("fig:"):
            fig_n += 1
            numbers[label] = f"Figure {fig_n}"
        else:
            tab_n += 1
            numbers[label] = f"Table {tab_n}"
    return numbers


def resolve(text: str, numbers: dict[str, str]) -> str:
    # inline references: "Fig. N" / "Table N"
    def _ref(m: re.Match) -> str:
        label = m.group(1)
        full = numbers[label]
        return full.replace("Figure", "Fig.") if label.startswith("fig:") else full

    text = AUTOREF_RE.sub(_ref, text)

    # image captions: prepend "**Figure N.** " and strip the label
    def _imgcap(m: re.Match) -> str:
        caption, label, tail = m.group(1), m.group(2), m.group(3)
        return f"![**{numbers[label]}.** {caption}]{tail}"

    text = re.sub(
        r"!\[(.*?)\\label\{((?:fig|tab):[a-z_0-9]+)\}\](\(figures/[^)]+\)(?:\{[^}]*\})?)",
        _imgcap,
        text,
    )

    # markdown table captions: ": caption \label{tab:x}" -> ": **Table N.** caption"
    def _tabcap(m: re.Match) -> str:
        caption, label = m.group(1).strip(), m.group(2)
        return f": **{numbers[label]}.** {caption}"

    text = re.sub(
        r"^: (.*?)\s*\\label\{((?:fig|tab):[a-z_0-9]+)\}\s*$",
        _tabcap,
        text,
        flags=re.MULTILINE,
    )
    return text


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    numbers = assign_numbers(text)
    resolved = resolve(text, numbers)

    leftover = LABEL_RE.findall(resolved) + AUTOREF_RE.findall(resolved)
    if leftover:
        raise SystemExit(f"Unresolved cross-references remain: {leftover}")

    build_md = HERE / "_build.md"
    build_md.write_text(resolved, encoding="utf-8")

    out = HERE / "manuscript_array_revised.docx"
    cmd = [
        "pandoc", str(build_md),
        "--filter", "pandoc-citeproc",
        "--bibliography", str(BIB),
        "--csl", str(CSL),
        "--resource-path", str(HERE),
        "-o", str(out),
    ]
    subprocess.run(cmd, check=True)
    replace_flattened_tables(out, out, highlight=False)
    n_fig = sum(1 for v in numbers.values() if v.startswith("Figure"))
    n_tab = sum(1 for v in numbers.values() if v.startswith("Table"))
    print(f"Wrote {out}  ({n_fig} figures, {n_tab} tables)")


if __name__ == "__main__":
    main()
