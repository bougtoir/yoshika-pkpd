"""Execute the Python examples in README.md so the documentation stays runnable."""

import re
from pathlib import Path

import pytest

README = Path(__file__).resolve().parents[1] / "README.md"


def _python_blocks() -> list[str]:
    text = README.read_text(encoding="utf-8")
    return re.findall(r"```python\n(.*?)```", text, re.S)


@pytest.mark.parametrize("code", _python_blocks())
def test_readme_python_block_runs(code, capsys):
    exec(compile(code, str(README), "exec"), {})
