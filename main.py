from collections import defaultdict
from datetime import datetime
import os
from tempfile import mkdtemp
from typing import Any, Dict, Generator, List, Tuple
import pygit2
import logging
import re

import jinja2
from markdown import markdown

from utils import listenv


TEMPLATES_DIR_DEFAULT = "templates"
REPO_URL = os.getenv("REPO_URL", "https://codeberg.org/HenriTEL/git-blog.git")
REPO_SUBDIR = os.getenv("REPO_SUBDIR", "").strip("/")
REPO_TEMPLATES_DIR = os.getenv("REPO_TEMPLATES_DIR", TEMPLATES_DIR_DEFAULT).strip("/")
REPO_DIRS_BLACKLIST = listenv("REPO_DIRS_BLACKLIST", ["draft", "media", "templates"])
REPO_FILES_BLACKLIST = listenv("REPO_FILES_BLACKLIST", ["README.md"])
CLONE_PATH = os.getenv("CLONE_PATH", "").rstrip("/")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./www").rstrip("/")
MD_LIB_EXTENSIONS = listenv("MD_LIB_EXTENSIONS", ["extra"])

"""
List of files per section
    Ordered by decreasing time of first commit
regex sub
"""


def main():
    repo = setup_repo()
    # TODO link missing template files in REPO
    # templates_fulldir = f"{CLONE_PATH}/{REPO_TEMPLATES_DIR}"
    # if not os.path.exists(templates_fulldir):
    templates_fulldir = TEMPLATES_DIR_DEFAULT
    j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_fulldir))

    sections = list(gen_sections(repo))
    section_to_paths = defaultdict(list)
    path_to_article = defaultdict(dict)
    for path, commit in gen_commits(repo):
        if "commits" in path_to_article[path]:
            path_to_article[path]["commits"].append(commit)
        else:
            path_to_article[path]["commits"] = [commit]
        if "/" in path:
            section = path.split("/")[0]
            if section in sections:
                section_to_paths[section].append(path)

    last_commit = repo[repo.head.target]
    for path, content in gen_articles_content(last_commit.tree):
        print(path)
        title, description, md_content = parse_md(content)
        path_to_article[path]["title"] = title
        path_to_article[path]["description"] = description
        path_to_article[path]["relative_path"] = path[:-3]
        render_article(
            metadata=path_to_article[path],
            md_content=content,
            target_path=f"{OUTPUT_DIR}/{path.replace('.md', '.html')}",
            sections=sections,
            j2_env=j2_env,
        )
    for section in sections:
        render_index(
            articles_paths=section_to_paths[section],
            path_to_article=path_to_article,
            target_path=f"{OUTPUT_DIR}/{section}/index.html",
            sections=sections,
            j2_env=j2_env,
        )


def setup_repo() -> pygit2.Repository:
    global CLONE_PATH, REPO_URL
    if CLONE_PATH and os.path.exists(f"{CLONE_PATH}/.git/"):
        repo = pygit2.Repository(CLONE_PATH)
    else:
        if not CLONE_PATH:
            CLONE_PATH = mkdtemp()
        os.makedirs(CLONE_PATH, exist_ok=True)
        repo = pygit2.clone_repository(REPO_URL, CLONE_PATH)
        logging.info(f"Cloned into {CLONE_PATH}")
    return repo


def render_article(
    metadata: Dict[str, Any],
    md_content: str,
    target_path: str,
    sections: List[str],
    j2_env: jinja2.Environment,
):
    template = j2_env.get_template("article.html.j2")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    html_content = markdown(md_content, extensions=MD_LIB_EXTENSIONS)
    full_page = template.render(
        title=metadata["title"],
        description=metadata["description"],
        main_content=html_content,
        commits=metadata["commits"],
        sections=sections,
    )
    print(full_page)
    with open(target_path, "w+") as fd:
        fd.write(full_page)
    logging.info(f"{target_path} has been written.")


def render_index(
    articles_paths: List[str],
    path_to_article: Dict[str, Dict[str, Any]],
    target_path: str,
    sections: List[str],
    j2_env: jinja2.Environment,
):
    template = j2_env.get_template("index.html.j2")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    articles = [path_to_article[p] for p in articles_paths]
    full_page = template.render(
        title=articles_paths[0].split("/")[0],
        articles=articles,
        sections=sections,
    )
    print(full_page)
    with open(target_path, "w+") as fd:
        fd.write(full_page)
    logging.info(f"{target_path} has been written.")


def gen_commits(repo: pygit2.Repository) -> Tuple[str, Dict[str, Any]]:
    def clean_ci(commit: pygit2.Commit) -> Dict[str, Any]:
        commit_dt = datetime.fromtimestamp(commit.commit_time)
        return {
            "iso_time": commit_dt.isoformat(),
            "human_time": commit_dt.strftime("%d %B %Y"),
            "author": commit.author,
            "message": commit.message,
        }

    for commit in repo.walk(repo.head.target):
        if commit.parents:
            prev = commit.parents[0]
            diff = prev.tree.diff_to_tree(commit.tree)
            for patch in diff:
                path = patch.delta.new_file.path
                if path.endswith(".md") and path.startswith(f"{REPO_SUBDIR}/"):
                    path = path.removeprefix(f"{REPO_SUBDIR}/")
                    yield path, clean_ci(commit)


def gen_articles_content(
    tree: pygit2.Tree, path=""
) -> Generator[Tuple[str, str], None, None]:
    for obj in tree:
        if obj.type == pygit2.GIT_OBJ_TREE and obj.name not in REPO_DIRS_BLACKLIST:
            path += f"{obj.name}/"
            yield from gen_articles_content(obj, path)

        elif (
            obj.name.endswith(".md")
            and path.startswith(f"{REPO_SUBDIR}/")
            and obj.name not in REPO_FILES_BLACKLIST
        ):
            path = path.removeprefix(f"{REPO_SUBDIR}/")
            yield (path + obj.name, obj.data.decode("utf-8"))


def gen_sections(repo: pygit2.Repository):
    tree = repo[repo.head.target].tree
    # Move to the REPO_SUBDIR location
    for to_match in REPO_SUBDIR.split("/"):
        for obj in tree:
            if obj.type == pygit2.GIT_OBJ_TREE and obj.name == to_match:
                tree = obj
                break
        if obj.name != to_match:
            return

    # Enumerate all valid toplevel dirs
    for obj in tree:
        if obj.type == pygit2.GIT_OBJ_TREE and obj.name not in REPO_DIRS_BLACKLIST:
            yield obj.name


def parse_md(md_content: str) -> Tuple[str, str, str]:
    """Return title, description and main_content of the article
    (without the title ans description).
    """
    title_pattern = r"^# (.+)\n"
    # TODO deal with multi >
    desc_pattern = r"^\> (.+)\n"
    title = re.search(title_pattern, md_content, re.MULTILINE).group(1).rstrip()
    md_content = re.sub(title_pattern, "", md_content, 1, re.MULTILINE)
    print(md_content)
    desc = re.search(desc_pattern, md_content, re.MULTILINE).group(1).rstrip()
    md_content = re.sub(desc_pattern, "", md_content, 1, re.MULTILINE)

    return title, desc, md_content


def get_sections_to_md(
    md_to_commits: Dict[str, List[pygit2.Object]]
) -> Dict[str, List[str]]:
    sections_to_md = defaultdict(list)
    for path in md_to_commits.keys():
        if "/" in path:
            section = path.split("/")[0]
            sections_to_md[section].append(path)
    return sections_to_md


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
