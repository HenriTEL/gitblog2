#!/usr/bin/env python3
from enum import StrEnum, auto
from typing import Optional
import logging

import typer

from .lib import GitBlog


class LogLevel(StrEnum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()


def main():
    typer.run(cli)


def cli(
    source_repo: str = typer.Argument(
        "./",
        envvar="SOURCE_REPO",
    ),
    output_dir: str = typer.Argument("./www", envvar="OUTPUT_DIR"),
    clone_dir: Optional[str] = typer.Option(None, envvar="CLONE_DIR"),
    repo_subdir: str = typer.Option("", envvar="REPO_SUBDIR"),
    fetch: bool = typer.Option(False, envvar="FETCH"),
    loglevel: LogLevel = typer.Option(
        LogLevel.INFO, "--loglevel", "-l", envvar="LOG_LEVEL"
    ),
):
    logging.basicConfig(level=loglevel.upper(), format="%(message)s")
    logging.info(f"Generating blog into '{output_dir}'...")
    with GitBlog(source_repo, clone_dir, repo_subdir, fetch=fetch) as gb:
        gb.write_blog(output_dir)
    logging.info("Done.")


if __name__ == "__main__":
    main()
