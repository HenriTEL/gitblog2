from pathlib import Path
from git import Tree


def fast_diff(
    path_to_hash: dict[Path, str], target: Tree
) -> tuple[list[Path], dict[Path, str]]:
    new_path_to_hash: dict[Path, str] = {}
    changed_paths: list[Path] = []
    for path, file_hash in path_to_hash.items():
        try:
            blob = target[str(path)]
        except KeyError:
            changed_paths.append(path)
            continue
        if file_hash != blob.hexsha:
            changed_paths.append(path)
        new_path_to_hash[path] = file_hash
    return changed_paths, new_path_to_hash
