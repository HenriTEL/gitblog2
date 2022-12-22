from collections import defaultdict
from datetime import datetime
import os
import shutil
from tempfile import TemporaryDirectory
from typing import Any, Dict, Generator, List, Tuple
import pygit2
import logging
import re

import jinja2
from markdown import markdown


MD_LIB_EXTENSIONS = ["extra", "toc"]


class GitBlog:
    def __init__(
        self,
        source_repo: str,
        clone_dir: str = None,
        repo_subdir: str = "",
        dirs_blacklist: List[str] = ["draft", "media", "templates"],
        files_blacklist: List[str] = ["README.md", "LICENSE.md"],
        fetch: bool = False,
    ):
        self.source_repo = source_repo
        self.repo_subdir = repo_subdir.strip("/")
        self.dirs_blacklist = dirs_blacklist
        self.files_blacklist = files_blacklist

        if _is_uri(self.source_repo):
            self.clone_dir = (
                TemporaryDirectory() if clone_dir is None else clone_dir.rstrip("/")
            )
        else:
            self.clone_dir = source_repo
        self.blog_path = (
            self.clone_dir + "/" + self.repo_subdir
            if self.repo_subdir
            else self.clone_dir
        ).rstrip("/")

        self.pkgdir = os.path.dirname(__file__)
        self.repo = self._init_repo(fetch)
        self.j2env = self._init_templating()

        self.section_to_paths: Dict[str, list] = defaultdict(set)
        self._articles_metadata = None
        self._sections = None

    @property
    def sections(self) -> List[str]:
        if self._sections is None:
            self._sections = list(self.gen_sections())
            logging.debug("Built sections.")
        return self._sections

    @property
    def articles_metadata(self) -> defaultdict[str, Dict[str, Any]]:
        if self._articles_metadata is None:
            self._articles_metadata = defaultdict(dict)
            for path, commit in self.gen_commits():
                if "commits" in self._articles_metadata[path]:
                    self._articles_metadata[path]["commits"].append(commit)
                else:
                    self._articles_metadata[path]["commits"] = [commit]
            logging.debug("Built articles_metadata.")
        return self._articles_metadata

    @property
    def last_commit(self) -> pygit2.Commit:
        return self.repo[self.repo.head.target]

    def copy_static_assets(self):
        """Copy static assets from the repo into the outupt dir.
        Use files from the package if not found"""
        # TODO Only use package files as a fallback
        media_src = self.pkgdir + "/media"
        media_dst = self.blog_path + "/media"
        sync_dir(media_src, media_dst)

        css_src = self.pkgdir + "/style.css"
        css_dst = self.blog_path + "/style.css"
        if not os.path.exists(css_dst):
            shutil.copyfile(css_src, css_dst)
            logging.debug(f"Added {css_dst}")

    def write_articles(self, output_dir: str):
        template = self.j2env.get_template("article.html.j2")
        for path, content in self.gen_articles_content():
            full_page = self.render_article(content, path, template)
            target_path = output_dir + "/" + path.replace(".md", ".html")
            _write_file(full_page, target_path)

    def render_article(
        self,
        content: str,
        path: str = None,
        template: jinja2.Template = None,
    ) -> str:
        """content: Markdown content
        Return content in html format based on the jinja2 template"""
        if template is None:
            template = self.j2env.get_template("article.html.j2")
        title, description, md_content = self.parse_md(content)
        if path is not None:
            self.articles_metadata[path]["relative_path"] = path[:-3]
            self.articles_metadata[path]["title"] = title
            self.articles_metadata[path]["description"] = description
            section = path.split("/")[0]
            self.section_to_paths[section].add(path)
        html_content = markdown(md_content, extensions=MD_LIB_EXTENSIONS)
        return template.render(
            title=title,
            description=description,
            main_content=html_content,
            commits=self.articles_metadata[path]["commits"],
            sections=self.sections,
        )

    def write_indexes(self, output_dir: str):
        template = self.j2env.get_template("index.html.j2")
        for section in self.sections:
            target_path = f"{output_dir}/{section}/index.html"
            try:
                full_page = self.render_index(section, template)
            except Exception as e:
                logging.error(f"Failed to render index for section {section}")
                raise e
            _write_file(full_page, target_path)

        home_page = self.render_index(template=template)
        _write_file(home_page, f"{output_dir}/index.html")

    def render_index(
        self,
        section: str = None,
        template: jinja2.Template = None,
    ) -> str:
        if template is None:
            template = self.j2env.get_template("index.html.j2")

        if section is None:
            paths = [p for ps in self.section_to_paths.values() for p in ps]
            section = "Home"
        else:
            paths = self.section_to_paths[section]
        articles = [self.articles_metadata[p] for p in paths]
        return template.render(
            title=section,
            articles=articles,
            sections=self.sections,
        )

    def gen_commits(self) -> Tuple[str, Dict[str, Any]]:
        def clean_commit(commit: pygit2.Commit) -> Dict[str, Any]:
            commit_dt = datetime.fromtimestamp(commit.commit_time)
            return {
                "iso_time": commit_dt.isoformat(),
                "human_time": commit_dt.strftime("%d %b %Y"),
                "author": commit.author,
                "message": commit.message,
            }

        for commit in self.repo.walk(self.repo.head.target):
            if commit.parents:
                prev = commit.parents[0]
                diff = prev.tree.diff_to_tree(commit.tree)
                for patch in diff:
                    path = patch.delta.new_file.path
                    if path.endswith(".md"):
                        if self.repo_subdir and path.startswith(self.repo_subdir + "/"):
                            path = path.removeprefix(self.repo_subdir + "/")
                        else:
                            continue
                        yield path, clean_commit(commit)

    def gen_articles_content(
        self, tree: pygit2.Tree = None, path=""
    ) -> Generator[Tuple[str, str], None, None]:
        """Traverse repo files an return any (path, content) tuple corresponding to non blacklisted Markdown files.
        The path parameter is recursively constructed as we traverse the tree."""
        if tree is None:
            tree = self.last_commit.tree
        for obj in tree:
            if obj.type == pygit2.GIT_OBJ_TREE and obj.name not in self.dirs_blacklist:
                obj_relpath = path + obj.name + "/"
                yield from self.gen_articles_content(obj, obj_relpath)
            elif (
                obj.name.endswith(".md")
                and (not self.repo_subdir or path.startswith(self.repo_subdir + "/"))
                and obj.name not in self.files_blacklist
            ):
                obj_relpath = path.removeprefix(self.repo_subdir + "/") + obj.name
                yield (obj_relpath, obj.data.decode("utf-8"))
            elif obj.name.endswith(".md"):
                logging.debug(f"Skipped {path + obj.name}")

    def gen_sections(self) -> Generator[str, None, None]:
        tree = self.last_commit.tree
        # Move to the self.repo_subdir location
        if self.repo_subdir:
            for to_match in self.repo_subdir.split("/"):
                for obj in tree:
                    if obj.type == pygit2.GIT_OBJ_TREE and obj.name == to_match:
                        tree = obj
                        break
                if obj.name != to_match:
                    return

        # Enumerate all valid toplevel dirs
        for obj in tree:
            if obj.type == pygit2.GIT_OBJ_TREE and obj.name not in self.dirs_blacklist:
                yield obj.name

    def parse_md(self, md_content: str) -> Tuple[str, str, str]:
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

    def _init_repo(self, fetch: bool = False) -> pygit2.Repository:
        """Check if there is an existing repo at self.clone_dir and clone the repo there otherwise.
        Optionally fetch changes after that."""

        cloned_already = os.path.exists(self.clone_dir + "/.git/")
        if cloned_already:
            repo = pygit2.Repository(self.clone_dir)
        else:
            repo = pygit2.clone_repository(self.source_repo, self.clone_dir, bare=True)
            logging.debug(f"Cloned repo into {self.clone_dir}")
        if fetch:
            repo.remotes["origin"].fetch()
            logging.debug("Fetched last changes.")
        return repo

    def _init_templating(self) -> jinja2.Environment:
        """Copy missing templates into the template dir if necessary
        and return a Jinja2Environment"""
        # TODO move files in a temp dir to keep the cloned repo clean
        templates_src = self.pkgdir + "/templates"
        templates_dst = self.blog_path + "/templates"
        sync_dir(templates_src, templates_dst, symlink=True)
        return jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dst))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if isinstance(self.clone_dir, TemporaryDirectory):
            self.clone_dir.cleanup()


def sync_dir(src: str, dst: str, symlink: bool = False):
    """Add files that are missing from src into dst, optionally using symlinks"""
    os.makedirs(dst, exist_ok=True)
    for file in os.listdir(src):
        dst_file = f"{dst}/{file}"
        if not os.path.exists(dst_file):
            if symlink:
                os.symlink(f"{src}/{file}", dst_file)
            else:
                shutil.copyfile(f"{src}/{file}", dst_file)
            logging.debug(f"Added {dst_file}")


def _write_file(content: str, target_path: str):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w+") as fd:
        fd.write(content)
    logging.debug(f"Wrote {target_path}")


def _is_uri(repo_link: str):
    return repo_link.startswith(("http", "git@"))
