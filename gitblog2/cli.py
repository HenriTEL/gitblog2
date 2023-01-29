#!/usr/bin/env python3
from enum import StrEnum, auto
import logging
from typing import Optional
from urllib.parse import urlparse

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
    no_feeds: bool = typer.Option(False, envvar="NO_FEED"),
    no_avatar: bool = typer.Option(False, envvar="NO_AVATAR"),
    url_base: str = typer.Option(None, envvar="URL_BASE"),
):  # TODO add arguments descriptions
    logging.basicConfig(level=loglevel.upper(), format="%(message)s")
    logging.info(f"Generating blog into '{output_dir}'...")
    with GitBlog(source_repo, clone_dir, repo_subdir, fetch=fetch) as gb:
        parsed_url = urlparse(url_base) if url_base is not None else None
        gb.write_blog(
            output_dir,
            with_feeds=(not no_feeds),
            with_avatar=(not no_avatar),
            url_base=parsed_url,
        )
    logging.info("Done.")


if __name__ == "__main__":
    main()
