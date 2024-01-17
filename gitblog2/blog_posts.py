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

    @property
    def human_time(self):
        return self.last_update_dt.strftime("%b %d, %Y")


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
        path_to_hash: dict[str, str] = {}
        latest_commit = next(commits)

        for path, file_hash in self._gen_path_and_hashes(latest_commit.tree):
            path_to_hash[path] = file_hash
            self.path_to_blog_post[path] = BlogPost(
                datetime.min,
                datetime.min,
                str(latest_commit.author),
                path[:-3].removeprefix(repo_subdir),
            )
        parent_commit = latest_commit
        # Traverse commit history to find posts creation dates
        for commit in commits:
            changed_paths, new_path_to_hash = fast_diff(path_to_hash, commit.tree)
            for path in changed_paths:
                blog_post = self.path_to_blog_post[path]
                if blog_post.last_update_dt == datetime.min:
                    blog_post.last_update_dt = parent_commit.committed_datetime
                if path not in new_path_to_hash:
                    blog_post.creation_dt = parent_commit.committed_datetime
            if not new_path_to_hash:
                break
            parent_commit = commit
            path_to_hash = new_path_to_hash

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
