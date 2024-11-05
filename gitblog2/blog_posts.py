import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator

from git import Commit, Tree

from gitblog2.repo_utils import ChangeType, fast_diff


@dataclass
class BlogPost:
    creation_dt: datetime
    last_update_dt: datetime
    author: str
    relative_path: Path
    title: str = ""
    description: str = ""

    @property
    def human_time(self):
        return self.last_update_dt.strftime("%b %d, %Y")


class BlogPosts(dict):
    def __init__(
        self,
        commits: Iterator[Commit],
        repo_subdir: str = "",
        ignore_dirs: tuple[str, ...] = (),
        ignore_files: tuple[str, ...] = (),
    ):
        super().__init__()
        self.ignore_dirs = ignore_dirs
        self.ignore_files = ignore_files
        self._init_path_to_blog_post(commits, repo_subdir)

    def _init_path_to_blog_post(self, commits: Iterator[Commit], repo_subdir: str):
        path_to_hash: dict[Path, str] = {}
        latest_commit = next(commits)

        for path, hash in self._gen_path_and_hashes(latest_commit.tree, repo_subdir):
            path_to_hash[path] = hash
            self[path] = BlogPost(
                creation_dt=latest_commit.committed_datetime,
                last_update_dt=datetime.min.replace(
                    tzinfo=latest_commit.committed_datetime.tzinfo
                ),
                author=str(latest_commit.author),
                relative_path=path.relative_to(repo_subdir).with_suffix(""),
            )
        parent_commit = latest_commit
        # Traverse commit history to find posts creation an last update dates
        for commit in commits:
            changed_paths = fast_diff(path_to_hash, commit.tree)
            for path, (change_type, hash) in changed_paths.items():
                blog_post = self[path]
                blog_post.last_update_dt = max(
                    blog_post.last_update_dt, parent_commit.committed_datetime
                )
                match change_type:
                    case ChangeType.DELETED:
                        blog_post.creation_dt = min(
                            blog_post.creation_dt, parent_commit.committed_datetime
                        )
                        del path_to_hash[path]
                    case ChangeType.MODIFIED:
                        path_to_hash[path] = hash
            if not path_to_hash:
                break
            parent_commit = commit
        for path in path_to_hash:
            blog_post = self[path]
            blog_post.last_update_dt = max(
                blog_post.last_update_dt, parent_commit.committed_datetime
            )
            blog_post.creation_dt = min(
                blog_post.creation_dt, parent_commit.committed_datetime
            )

    def _gen_path_and_hashes(
        self, tree: Tree, repo_subdir: str
    ) -> Iterator[tuple[Path, str]]:
        for obj in tree:
            if obj.type == "tree" and obj.name not in self.ignore_dirs:
                yield from self._gen_path_and_hashes(obj, repo_subdir)
            elif obj.type == "blob" and obj.name.endswith(".md"):
                path = Path(obj.path)
                if repo_subdir and not path.is_relative_to(repo_subdir):
                    logging.debug("Skipped `%s`", path)
                    continue
                if obj.name in self.ignore_files:
                    logging.debug("Skipped `%s`", path)
                    continue
                yield Path(obj.path), obj.hexsha
