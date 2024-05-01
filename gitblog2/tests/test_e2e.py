import filecmp
import os
from pathlib import Path
import subprocess

GITBLOG_CMD = [
    "python3", "-m", "gitblog2.cli",
    "--repo-subdir", "example",
    "--base-url", "https://example.com",
    "--no-social",
    "https://github.com/HenriTEL/gitblog2.git",
]


def test_content_match(tmp_path: Path):
    cmd = GITBLOG_CMD + [str(tmp_path)]
    subprocess.run(cmd, check=True)

    expected_content_dir = Path(__file__).resolve().parent / "example_output"
    files = ["index.html", "tech/example.html", "tech/index.html"]
    (match, mismatch, errors) = filecmp.cmpfiles(
        tmp_path, expected_content_dir, files
    )

    assert len(match) == len(files), f"mismatch: {mismatch}, errors: {errors}"


def test_has_static_assets(tmp_path: Path):
    cmd = GITBLOG_CMD + [str(tmp_path)]
    subprocess.run(cmd, check=True)

    for path in ["media/favicon.svg", "media/icons.svg", "style.css"]:
        assert os.path.exists(tmp_path / path)
