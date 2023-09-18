import logging
import shutil
import subprocess

from pygit2 import clone_repository
from pygit2.repository import Repository


def git_clone(url: str, path: str) -> Repository:
    git_installed = shutil.which("git") is None
    if git_installed:
        # Clone with a depth of 1
        cmd = ["git", "clone", "--depth", "1", url, path]
        subprocess.run(cmd, check=True)
        logging.debug("Cloned repo with depth 1 into %s", path)
        repo = Repository(path)
    else:
        # Run a full clone
        repo = clone_repository(url, path)
        logging.debug("Full cloned repo into %s", path)
    return repo


def git_fetch(repo: Repository) -> None:
    git_path = shutil.which("git")
    if git_path is not None:
        # The git cli is accessible, try to fetch only commit objects
        cmd = "git fetch --no-tags --filter=blob:none"
        if repo.is_shallow:
            cmd += " --unshallow"
        subprocess.run(cmd, shell=True, check=True)
        logging.info("Fetched commits.")
    else:
        repo.remotes["origin"].fetch()
        logging.info("Fetch all completed.")
