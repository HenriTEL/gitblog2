#!/usr/bin/env python3
import logging
import tempfile
from enum import StrEnum, auto
from pathlib import Path
from urllib.parse import urlparse

import typer
from typing_extensions import Annotated

from gitblog2.lib import GitBlog


class LogLevel(StrEnum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()


def main(
    source_repo: Annotated[
        str,
        typer.Argument(
            envvar="SOURCE_REPO",
            help="The URL of the git repository to use as source for the blog.",
        ),
    ] = "./",
    clone_dir: Annotated[Path | None, typer.Option()] = None,
    repo_subdir: Annotated[str, typer.Option()] = "",
    output_dir: Annotated[Path, typer.Argument()] = Path("./public"),
    loglevel: Annotated[
        LogLevel,
        typer.Option("--loglevel", "-l", show_default="info", envvar="BASE_URL"),
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
            logging.info(f"The output directory `{output_dir}` is not empty.")

    with tempfile.TemporaryDirectory() as workdir:
        if source_repo.startswith(("http", "git@")):
            clone_dir = clone_dir or Path(workdir)
        else:
            clone_dir = Path(source_repo)
        git_blog = GitBlog(source_repo)
        git_blog.init_repo(clone_dir, no_fetch=no_fetch)
        git_blog.write_blog(
            output_dir,
            repo_subdir=repo_subdir,
            base_url=urlparse(base_url),
            with_social=(not no_social),
        )
    print("Done.")


if __name__ == "__main__":
    typer.run(main)
