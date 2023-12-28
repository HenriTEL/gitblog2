from git import Tree


def fast_diff(
    path_to_hash: dict[str, str], target: Tree
) -> tuple[list[str], dict[str, str]]:
    new_path_to_hash: dict[str, str] = {}
    changed_paths: list[str] = []
    for path, hash in path_to_hash.items():
        try:
            blob = target[path]
        except KeyError:
            changed_paths.append(path)
            continue
        if hash != blob.hexsha:
            changed_paths.append(path)
        new_path_to_hash[path] = hash
    return changed_paths, new_path_to_hash
