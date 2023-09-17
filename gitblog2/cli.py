#!/usr/bin/env python3
from enum import Enum
import logging
from typing import Optional
from urllib.parse import urlparse

import typer

from .lib import GitBlog


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def main():
    typer.run(cli)


def cli(
    source_repo: str = typer.Argument(
        "./",
        envvar="SOURCE_REPO",
    ),
    output_dir: str = typer.Argument("./public", envvar="OUTPUT_DIR"),
    clone_dir: Optional[str] = typer.Option(None, envvar="CLONE_DIR"),
    repo_subdir: str = typer.Option("", envvar="REPO_SUBDIR"),
    loglevel: LogLevel = typer.Option(
        LogLevel.INFO, "--loglevel", "-l", envvar="LOG_LEVEL"
    ),
    no_feeds: bool = typer.Option(False, envvar="NO_FEED"),
    no_social: bool = typer.Option(False, envvar="NO_SOCIAL"),
    no_fetch: bool = typer.Option(True, envvar="NO_FETCH"),
    base_url: str = typer.Option(None, envvar="BASE_URL"),
):  # TODO add arguments descriptions
    logging.basicConfig(level=loglevel.upper(), format="%(message)s")
    logging.info("Generating blog into '%s'...", output_dir)
    with GitBlog(source_repo, clone_dir, repo_subdir, fetch=not no_fetch) as git_blog:
        parsed_url = urlparse(base_url) if base_url is not None else None
        git_blog.write_blog(
            output_dir,
            with_feeds=(not no_feeds),
            with_social=(not no_social),
            base_url=parsed_url,
        )
    logging.info("Done.")


if __name__ == "__main__":
    main()
