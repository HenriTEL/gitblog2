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
REPO_SUBDIR = os.getenv("REPO_SUBDIR", "example/").lstrip("/").rstrip("/")
REPO_TEMPLATES_DIR = os.getenv("REPO_TEMPLATES_DIR", TEMPLATES_DIR_DEFAULT).lstrip("/").rstrip("/")
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
    md_to_commits = get_commits_per_md(repo)
    sections_to_md = get_sections_to_md(md_to_commits)
    last_commit = repo[repo.head.target]

    # TODO link missing template files in REPO
    # templates_fulldir = f"{CLONE_PATH}/{REPO_TEMPLATES_DIR}"
    # if not os.path.exists(templates_fulldir):
    templates_fulldir = TEMPLATES_DIR_DEFAULT
    j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_fulldir))
    template = j2_env.get_template("article.html.j2")
    md_to_td = make_articles(last_commit, md_to_commits, sections_to_md, template)

    template = j2_env.get_template("index.html.j2")
    make_indexes(sections_to_md, md_to_commits, md_to_td, template)


def make_articles(
    last_commit: pygit2.Object,
    md_to_commits: Dict[str, List[pygit2.Object]],
    sections_to_md: Dict[str, List[str]],
    template: jinja2.Template,
) -> Dict[str, Tuple[str, str]]:
    md_to_td = {}
    for path, blob in gen_md_blobs(last_commit.tree):
        base_name = f"{OUTPUT_DIR}/{path}"
        html_path = base_name + blob.name.replace(".md", ".html")
        os.makedirs(os.path.dirname(base_name), exist_ok=True)
        commits = md_to_commits[path + blob.name]
        title, desc, md_content = parse_md(blob.data.decode("utf-8"))
        html_content = markdown(md_content, extensions=MD_LIB_EXTENSIONS)
        full_page = template.render(
            title=title,
            description=desc,
            main_content=html_content,
            commits=commits,
            sections=list(sections_to_md.keys()),
        )
        print(full_page)
        with open(html_path, "w+") as fd:
            fd.write(full_page)
        logging.info(f"Updated {html_path}")
        md_to_td[path + blob.name] = (title, desc)


def make_indexes(sections_to_md, md_to_commits, md_to_td, template):
        full_page = template.render(
            title=title,
            description=desc,
            main_content=html_content,
            commits=commits,
            sections=list(sections_to_md.keys()),
        )


def get_commits_per_md(repo: pygit2.Repository):
    def commit_to_dict(commit: pygit2.Commit) -> Dict[str, Any]:
        return {
            attr: getattr(commit, attr) for attr in dir(commit) if not attr[0] == "_"
        }

    md_to_commits = defaultdict(list)
    for commit in repo.walk(repo.head.target):
        commit = commit_to_dict(commit)
        if commit["parents"]:
            prev = commit["parents"][0]
            diff = prev.tree.diff_to_tree(commit["tree"])
            for patch in diff:
                path = patch.delta.new_file.path
                if path.endswith(".md") and path.startswith(f"{REPO_SUBDIR}/"):
                    path = path.removeprefix(f"{REPO_SUBDIR}/")
                    commit_dt = datetime.fromtimestamp(commit["commit_time"])
                    commit["iso_time"] = commit_dt.isoformat()
                    commit["human_time"] = commit_dt.strftime("%d %B %Y")
                    md_to_commits[path].append(commit)
    return md_to_commits


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


def gen_md_blobs(
    tree: pygit2.Tree, path=""
) -> Generator[Tuple[str, pygit2.Object], None, None]:
    for obj in tree:
        if obj.type == pygit2.GIT_OBJ_TREE and obj.name not in REPO_DIRS_BLACKLIST:
            path += f"{obj.name}/"
            yield from gen_md_blobs(obj, path)

        elif (
            obj.name.endswith(".md")
            and path.startswith(f"{REPO_SUBDIR}/")
            and obj.name not in REPO_FILES_BLACKLIST
        ):
            path = path.removeprefix(f"{REPO_SUBDIR}/")
            yield (path, obj)


def get_sections_to_md(md_to_commits: Dict[str, List[pygit2.Object]]) -> Dict[str, List[str]]:
    sections_to_md = defaultdict(list)
    for path in md_to_commits.keys():
        if "/" in path:
            section = path.split("/")[0]
            sections_to_md[section].append(path)
    return sections_to_md


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


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
