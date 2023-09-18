#!/usr/bin/env python3
from enum import Enum
import logging
from urllib.parse import urlparse

import typer
from typing_extensions import Annotated

from .lib import GitBlog


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def main():
    typer.run(cli)


def cli(
    source_repo: Annotated[
        str,
        typer.Argument(
            envvar="SOURCE_REPO",
        ),
    ] = "./",
    output_dir: Annotated[str, typer.Argument(envvar="OUTPUT_DIR")] = "./public",
    clone_dir: Annotated[str, typer.Option(envvar="CLONE_DIR")] = "",
    repo_subdir: Annotated[str, typer.Option(envvar="REPO_SUBDIR")] = "",
    loglevel: Annotated[
        LogLevel, typer.Option("--loglevel", "-l", envvar="LOG_LEVEL")
    ] = LogLevel.INFO,
    no_feeds: Annotated[bool, typer.Option(envvar="NO_FEEDS")] = False,
    no_social: Annotated[bool, typer.Option(envvar="NO_SOCIAL")] = False,
    no_fetch: Annotated[bool, typer.Option(envvar="NO_FETCH")] = False,
    base_url: Annotated[str, typer.Option(envvar="BASE_URL")] = "",
):  # TODO add arguments descriptions
    logging.basicConfig(level=loglevel.upper(), format="%(message)s")
    logging.info("Generating blog into '%s'...", output_dir)
    with GitBlog(source_repo, clone_dir, repo_subdir, fetch=(not no_fetch)) as git_blog:
        git_blog.write_blog(
            output_dir,
            with_feeds=(not no_feeds),
            with_social=(not no_social),
            base_url=urlparse(base_url),
        )
    logging.info("Done.")


if __name__ == "__main__":
    main()
