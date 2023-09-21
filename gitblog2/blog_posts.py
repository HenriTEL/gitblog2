from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Generator, Iterator
from git import Commit, Tree

from gitblog2.repo_utils import fast_diff


@dataclass
class BlogPost:
    creation_dt: datetime
    last_update_dt: datetime
    author: str
    relative_path: str
    title: str = ""
    description: str = ""
    read_time_minutes: int = 1

    @property
    def human_time(self):
        return self.last_update_dt.strftime("%d %b %Y")


class BlogPosts:
    def __init__(
        self,
        commits: Iterator[Commit],
        repo_subdir: str = "",
        ignore_dirs: list[str] = [],
        ignore_files: list[str] = [],
    ):
        self.ignore_dirs = ignore_dirs
        self.ignore_files = ignore_files
        self._init_path_to_blog_post(commits, repo_subdir)

    def _init_path_to_blog_post(self, commits: Iterator[Commit], repo_subdir: str):
        self.path_to_blog_post: dict[str, BlogPost] = {}
        latest_commit = next(commits)
        root = latest_commit.tree
        path_to_hash: dict[str, str] = {}
        for path, hash in self._gen_path_and_hashes(root):
            path_to_hash[path] = hash
            self.path_to_blog_post[path] = BlogPost(
                latest_commit.committed_datetime,
                latest_commit.committed_datetime,
                str(latest_commit.author),
                path[:-3].removeprefix(repo_subdir),
            )

        # Traverse commit history to find posts creation dates
        for commit in commits:
            if not path_to_hash:
                break
            root = commit.tree
            changed_paths, path_to_hash = fast_diff(root, path_to_hash)
            for path in changed_paths:
                self.path_to_blog_post[path].creation_dt = commit.committed_datetime

    def _gen_path_and_hashes(
        self, tree: Tree
    ) -> Generator[tuple[str, str], None, None]:
        for obj in tree:
            if obj.type == "tree" and obj.name not in self.ignore_dirs:
                yield from self._gen_path_and_hashes(obj)
            elif obj.type == "blob" and obj.name.endswith(".md"):
                if obj.name in self.ignore_files:
                    logging.debug("Skipped %s", obj.path)
                    continue
            yield str(obj.path), obj.hexsha

    def __getitem__(self, path: str) -> BlogPost:
        return self.path_to_blog_post[path]

    def values(self):
        return self.path_to_blog_post.values()
