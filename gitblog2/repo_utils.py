from git import Tree


def fast_diff(
    parent: Tree, path_to_hash: dict[str, str]
) -> tuple[list[str], dict[str, str]]:
    new_path_to_hash: dict[str, str] = {}
    changed_paths: list[str] = []
    for path, hash in path_to_hash.items():
        if path not in parent:
            # The file does not appear in parent, we stop tracking its history
            continue
        if hash != parent[path].hexsha:
            changed_paths.append(path)
        new_path_to_hash[path] = hash
    return changed_paths, new_path_to_hash
