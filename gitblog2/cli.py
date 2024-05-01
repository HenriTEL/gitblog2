#!/usr/bin/env python3
from enum import Enum
import logging
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import typer
from typing_extensions import Annotated

from gitblog2.lib import GitBlog
from gitblog2.utils import NONE_PATH, NonePath


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def main(
    clone_dir: Annotated[Optional[Path], typer.Option()] = None,
    repo_subdir: Annotated[Optional[Path], typer.Option()] = None,
    source_repo: Annotated[
        str,
        typer.Argument(
            envvar="SOURCE_REPO",
        ),
    ] = "./",
    output_dir: Annotated[Path, typer.Argument()] = Path("./public"),
    loglevel: Annotated[
        LogLevel, typer.Option("--loglevel", "-l", show_default="info", envvar="BASE_URL")
    ] = LogLevel.INFO,
    force: Annotated[bool, typer.Option("--force", "-f")] = False,
    no_social: Annotated[bool, typer.Option("--no-social")] = False,
    no_fetch: Annotated[bool, typer.Option("--no-fetch")] = False,
    base_url: Annotated[str, typer.Option(envvar="BASE_URL")] = "",
):  # TODO add arguments descriptions
    logging.basicConfig(level=loglevel.upper(), format="%(levelname)s: %(message)s")
    if output_dir.exists():
        if not output_dir.is_dir():
            raise FileNotFoundError(f"`{output_dir}` is not a valid directory")
        if any(output_dir.iterdir()):
            if not force:
                raise FileExistsError(
                    f"The output directory `{output_dir}` is not empty, use --force to overwrite."
                )
            logging.warning(f"The output directory `{output_dir}` is not empty.")

    print(f"Generating blog into `{output_dir}`...")
    clone_dir = clone_dir or NONE_PATH
    repo_subdir = repo_subdir or NONE_PATH
    logging.debug(f"clone_dir `{clone_dir}`")
    logging.debug(f"repo_subdir `{repo_subdir}`")
    logging.debug(f"base_url `{base_url}`")
    with GitBlog(source_repo, clone_dir, repo_subdir, fetch=(not no_fetch)) as git_blog:
        git_blog.write_blog(
            output_dir,
            with_social=(not no_social),
            base_url=urlparse(base_url),
        )
    print("Done.")


if __name__ == "__main__":
    typer.run(main)
