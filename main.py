#!/usr/bin/env python3
from collections import defaultdict
from datetime import datetime
import os
import pathlib
import shutil
from tempfile import mkdtemp
from typing import Any, Dict, Generator, List, Set, Tuple
import pygit2
import logging
import re

import jinja2
from markdown import markdown


def listenv(envname: str, default: List[str]) -> List[str]:
    if envname in os.environ:
        return os.getenv(envname).split(",")
    return default


TEMPLATES_DIR_DEFAULT = "templates"
REPO_URL = os.getenv("REPO_URL", "https://codeberg.org/HenriTEL/git-blog.git")
REPO_SUBDIR = os.getenv("REPO_SUBDIR", "").strip("/")
REPO_TEMPLATES_DIR = os.getenv("REPO_TEMPLATES_DIR", TEMPLATES_DIR_DEFAULT).strip("/")
REPO_DIRS_BLACKLIST = listenv("REPO_DIRS_BLACKLIST", ["draft", "media", "templates"])
REPO_FILES_BLACKLIST = listenv("REPO_FILES_BLACKLIST", ["README.md", "LICENSE.md"])
CLONE_PATH = os.getenv("CLONE_PATH", "").rstrip("/")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./www").rstrip("/")
MD_LIB_EXTENSIONS = listenv("MD_LIB_EXTENSIONS", ["extra", "toc"])

"""
List of files per section
    Ordered by decreasing time of first commit
regex sub
"""


def main():
    repo = setup_repo()
    templates_fulldir = f"{CLONE_PATH}/{REPO_TEMPLATES_DIR}"
    j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_fulldir))

    sections = list(gen_sections(repo))
    section_to_paths: Dict[str, list] = defaultdict(set)
    path_to_article = defaultdict(dict)
    for path, commit in gen_commits(repo):
        if "commits" in path_to_article[path]:
            path_to_article[path]["commits"].append(commit)
        else:
            path_to_article[path]["commits"] = [commit]
        if "/" in path:
            section = path.split("/")[0]
            if section in sections:
                section_to_paths[section].add(path)

    # Render all html articles
    last_commit = repo[repo.head.target]
    for path, content in gen_articles_content(last_commit.tree):
        title, description, md_content = parse_md(content)
        path_to_article[path]["title"] = title
        path_to_article[path]["description"] = description
        path_to_article[path]["relative_path"] = path[:-3]
        render_article(
            metadata=path_to_article[path],
            md_content=md_content,
            target_path=f"{OUTPUT_DIR}/{path.replace('.md', '.html')}",
            sections=sections,
            j2_env=j2_env,
        )
    # Render sections index.html
    for section in sections:
        render_index(
            articles_paths=section_to_paths[section],
            path_to_article=path_to_article,
            target_path=f"{OUTPUT_DIR}/{section}/index.html",
            sections=sections,
            j2_env=j2_env,
        )

    # Render root index.html
    render_index(
        articles_paths=[p for paths in section_to_paths.values() for p in paths],
        path_to_article=path_to_article,
        target_path=f"{OUTPUT_DIR}/index.html",
        sections=sections,
        j2_env=j2_env,
        title="Home",
    )
    copy_static_assets()


def setup_repo() -> pygit2.Repository:
    global CLONE_PATH, REPO_URL
    cwd = str(pathlib.Path().resolve()).rstrip("/")

    # Clone the repository if necessary
    if CLONE_PATH and os.path.exists(f"{CLONE_PATH}/.git/"):
        repo = pygit2.Repository(CLONE_PATH)
    else:
        if not CLONE_PATH:
            CLONE_PATH = mkdtemp().rstrip("/")
        os.makedirs(CLONE_PATH, exist_ok=True)
        repo = pygit2.clone_repository(REPO_URL, CLONE_PATH)
        logging.info(f"Cloned blog sources into {CLONE_PATH}")

    # Add missing template files
    templates_fulldir_src = f"{cwd}/templates"
    templates_fulldir_dst = f"{CLONE_PATH}/{REPO_TEMPLATES_DIR}"
    os.makedirs(templates_fulldir_dst, exist_ok=True)
    for template_file in os.listdir(templates_fulldir_src):
        dst = f"{templates_fulldir_dst}/{template_file}"
        if not os.path.exists(dst):
            os.symlink(f"{templates_fulldir_src}/{template_file}", dst)
            logging.info(f"Added {dst}")

    # Add missing media
    media_fulldir_src = f"{cwd}/media"
    media_fulldir_dst = (
        f"{CLONE_PATH}/{REPO_SUBDIR}/media" if REPO_SUBDIR else f"{CLONE_PATH}/media"
    )
    os.makedirs(media_fulldir_dst, exist_ok=True)
    for media_file in os.listdir(media_fulldir_src):
        dst = f"{media_fulldir_dst}/{media_file}"
        if not os.path.exists(dst):
            shutil.copyfile(f"{media_fulldir_src}/{media_file}", dst)
            logging.info(f"Added {dst}")

    # Add missing css
    dst = (
        f"{CLONE_PATH}/{REPO_SUBDIR}/style.css"
        if REPO_SUBDIR
        else f"{CLONE_PATH}/style.css"
    )
    if not os.path.exists(dst):
        for css_file in ["layout.css", "style.css"]:
            with open(dst, "a+") as fo, open(f"{cwd}/css/{css_file}", "r") as fi:
                fo.write(fi.read())
        logging.info(f"Added {dst}")

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
    with open(target_path, "w+") as fd:
        fd.write(full_page)
    logging.info(f"Rendered {target_path}")


def render_index(
    articles_paths: Set[str],
    path_to_article: Dict[str, Dict[str, Any]],
    target_path: str,
    sections: List[str],
    j2_env: jinja2.Environment,
    title: str = None,
):
    template = j2_env.get_template("index.html.j2")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    articles = [path_to_article[p] for p in articles_paths]
    if title is None:
        title = next(iter(articles_paths)).split("/")[0]
    full_page = template.render(
        title=title,
        articles=articles,
        sections=sections,
    )
    with open(target_path, "w+") as fd:
        fd.write(full_page)
    logging.info(f"Rendered {target_path}")


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
                if path.endswith(".md") and (
                    not REPO_SUBDIR or path.startswith(f"{REPO_SUBDIR}/")
                ):
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
            and (not REPO_SUBDIR or path.startswith(f"{REPO_SUBDIR}/"))
            and obj.name not in REPO_FILES_BLACKLIST
        ):
            path = path.removeprefix(f"{REPO_SUBDIR}/")
            yield (path + obj.name, obj.data.decode("utf-8"))


def gen_sections(repo: pygit2.Repository):
    tree = repo[repo.head.target].tree
    # Move to the REPO_SUBDIR location
    if REPO_SUBDIR:
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


def copy_static_assets():
    media_src = f"{CLONE_PATH}/{REPO_SUBDIR}/media"
    media_dst = f"{OUTPUT_DIR}/media"
    shutil.copytree(media_src, media_dst, dirs_exist_ok=True)

    css_src = f"{CLONE_PATH}/{REPO_SUBDIR}/style.css"
    css_dst = f"{OUTPUT_DIR}/style.css"
    shutil.copy(css_src, css_dst)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
