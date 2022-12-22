#!/usr/bin/env python3
from enum import StrEnum
from typing import Optional
import logging

import typer

from .lib import GitBlog

LogLevel = StrEnum("LogLevel", list(logging._nameToLevel.keys()))


def main():
    typer.run(cli)


def cli(
    source_repo: str = typer.Argument(
        "./",
        envvar="SOURCE_REPO",
    ),
    output_dir: Optional[str] = typer.Argument("./www", envvar="OUTPUT_DIR"),
    clone_dir: Optional[str] = typer.Option(
        None,
        envvar="CLONE_DIR",
    ),
    repo_subdir: str = typer.Option("", envvar="REPO_SUBDIR"),
    fetch: Optional[bool] = typer.Option(False, envvar="FETCH"),
    loglevel: Optional[LogLevel] = typer.Option(
        LogLevel.INFO, "--loglevel", "-l", envvar="LOG_LEVEL"
    ),
):
    logging.basicConfig(level=loglevel.upper(), format="%(message)s")
    with GitBlog(source_repo, clone_dir, str(repo_subdir), fetch=fetch) as gb:
        logging.info(f"Writing into '{output_dir}'...")
        gb.write_articles(output_dir)
        gb.write_indexes(output_dir)
        gb.copy_static_assets()
    logging.info("Done.")


if __name__ == "__main__":
    main()
