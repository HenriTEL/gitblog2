import filecmp
import os
import shutil
import subprocess

import pytest


OUTPUT_DIR = "./public"
GITBLOG_ARGS = [
    "gitblog2",
    "https://github.com/HenriTEL/gitblog2.git",
    "--repo-subdir",
    "example",
    "--base-url",
    "https://example.com",
    "--no-social",
]


@pytest.fixture(scope="session")
def blog_dir():
    subprocess.run(GITBLOG_ARGS, check=True)
    yield OUTPUT_DIR
    shutil.rmtree(OUTPUT_DIR)


def test_content_match(blog_dir):
    expected_content_dir = os.path.dirname(os.path.abspath(__file__)) + "/example_output"
    files = ["index.html", "tech/example.html", "tech/index.html"]
    (match, mismatch, errors) = filecmp.cmpfiles(
        blog_dir, expected_content_dir, files
    )
    assert len(match) == len(files), f"mismatch: {mismatch}, errors: {errors}"


def test_has_static_assets(blog_dir):
    for path in ["media/favicon.svg", "media/icons.svg", "style.css"]:
        assert os.path.exists(blog_dir + "/" + path)
