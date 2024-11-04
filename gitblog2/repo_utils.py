from enum import Enum, auto
from pathlib import Path

from git import Tree


class ChangeType(Enum):
    DELETED = auto()
    MODIFIED = auto()


def fast_diff(
    path_to_hash: dict[Path, str], commit_tree: Tree
) -> dict[Path, tuple[ChangeType, str]]:
    changed_paths: dict[Path, tuple[ChangeType, str]] = {}
    for path, file_hash in path_to_hash.items():
        try:
            blob = commit_tree[str(path)]
        except KeyError:
            changed_paths[path] = (ChangeType.DELETED, "")
            continue
        if file_hash != blob.hexsha:
            changed_paths[path] = (ChangeType.MODIFIED, blob.hexsha)
    return changed_paths
