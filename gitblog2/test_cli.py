import filecmp
import os
import tempfile
from pathlib import Path

import pytest

from gitblog2 import cli

EXPECTED_OUTPUT_DIR = Path(__file__).resolve().parent / "tests/example_output"


@pytest.fixture(scope="session")
def output_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        cli.main(
            repo_subdir="example",
            base_url="https://example.com",
            no_social=True,
            source_repo="https://github.com/HenriTEL/gitblog2.git",
            output_dir=tmp_path,
            loglevel=cli.LogLevel.DEBUG,
        )
        yield tmp_path


def test_content_match(output_dir: Path):
    files = ["index.html", "tech/example.html", "tech/index.html"]
    (match, mismatch, errors) = filecmp.cmpfiles(output_dir, EXPECTED_OUTPUT_DIR, files)
    print(f"{(output_dir / 'index.html').read_text()}")
    assert len(match) == len(files), f"mismatch: {mismatch}, errors: {errors}"


def test_has_static_assets(output_dir: Path):
    for path in [
        "media/favicon.svg",
        "media/icons.svg",
        "css/theme.css",
        "css/layout.css",
    ]:
        assert os.path.exists(output_dir / path)
