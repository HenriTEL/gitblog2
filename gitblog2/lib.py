from base64 import b64encode
from collections import defaultdict
import datetime
import logging
import os
import re
import shutil
from tempfile import TemporaryDirectory
from typing import cast, Any, DefaultDict, Dict, Generator, List, Optional, Tuple
from urllib import request
from urllib.parse import ParseResult, urlparse

from feedgen.feed import FeedGenerator
import jinja2
from markdown import markdown
import pygit2
from pygit2 import Blob, Commit, Repository, Tree, GIT_OBJ_TREE


MD_LIB_EXTENSIONS = ["extra", "toc"]


class GitBlog:
    def __init__(
        self,
        source_repo: str,
        clone_dir: Optional[str] = None,
        repo_subdir: str = "",
        dirs_blacklist: List[str] = ["draft", "media", "templates", ".github"],
        files_blacklist: List[str] = ["README.md", "LICENSE.md"],
        fetch: bool = False,
    ):
        self.source_repo = source_repo
        self.repo_subdir = repo_subdir.strip("/")
        self.dirs_blacklist = dirs_blacklist
        self.files_blacklist = files_blacklist

        self.workdir = TemporaryDirectory()
        if _is_uri(self.source_repo):
            self.clone_dir = (
                self.workdir.name if clone_dir is None else clone_dir.rstrip("/")
            )
        else:
            self.clone_dir = source_repo.rstrip("/")
        self.blog_path = (
            self.clone_dir + "/" + self.repo_subdir
            if self.repo_subdir
            else self.clone_dir
        ).rstrip("/")

        self.pkgdir = os.path.dirname(__file__)
        self.repo = self._init_repo(fetch)
        self.j2env = self._init_templating()

        self.section_to_paths: DefaultDict[str, set] = defaultdict(set)
        self._articles_metadata = None
        self._sections = None

    @property
    def sections(self) -> List[str]:
        if self._sections is None:
            self._sections = list(self.gen_sections())
            logging.debug("Built sections.")
        return self._sections

    @property
    def articles_metadata(self) -> DefaultDict[str, Dict[str, Any]]:
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
    def last_commit(self) -> Commit:
        return cast(Commit, self.repo.revparse_single("HEAD"))

    def write_blog(
        self,
        output_dir: str,
        with_feeds=True,
        with_avatar=True,
        url_base: Optional[ParseResult] = None,
    ):
        self.write_articles(output_dir, with_avatar=with_avatar)
        self.write_indexes(output_dir, with_feeds, with_avatar=with_avatar)
        if with_feeds:
            if url_base is None:
                raise ReferenceError(
                    "You need to provide your website base URL in order to generate a feed."
                )
            self.write_syndication_feeds(output_dir, url_base=url_base)
        self.add_static_assets(output_dir)
        if with_avatar:
            self.download_avatar(output_dir)

    def write_articles(self, output_dir: str, with_avatar=True):
        template = self.j2env.get_template("article.html.j2")
        for path, content in self.gen_articles_content():
            full_page = self.render_article(
                content, path, template, with_avatar=with_avatar
            )
            target_path = output_dir + "/" + path.replace(".md", ".html")
            _write_file(full_page, target_path)

    def write_indexes(self, output_dir: str, with_feeds=True, with_avatar=True):
        template = self.j2env.get_template("index.html.j2")
        for section in self.sections:
            target_path = f"{output_dir}/{section}/index.html"
            try:
                full_page = self.render_index(
                    section, template, with_avatar=with_avatar
                )
            except Exception as e:
                logging.error(f"Failed to render index for section {section}")
                raise e
            _write_file(full_page, target_path)

        home_page = self.render_index(
            template=template, with_feeds=with_feeds, with_avatar=with_avatar
        )
        _write_file(home_page, f"{output_dir}/index.html")

    def write_syndication_feeds(self, output_dir: str, url_base: ParseResult):
        url_hash = b64encode(url_base.geturl().encode()).decode()
        feed_id = f"ni://{url_base.hostname}/base64;{url_hash}"
        last_commit_dt = _get_commit_dt(self.last_commit)
        author = self.last_commit.author.name
        description = f"The latest news from {author}"
        fg = FeedGenerator()
        fg.id(feed_id)
        fg.title(description)
        fg.description(description)
        fg.author(name=author)
        fg.link(href=url_base.geturl())
        fg.logo(url_base.geturl() + "/media/favicon.svg")
        fg.updated(last_commit_dt)
        for _, paths in self.section_to_paths.items():
            for path in paths:
                article = self.articles_metadata[path]
                last_commit_dt = article["commits"][0]["iso_time"]
                article_url = f"{url_base.geturl()}/{article['relative_path']}"
                url_hash = b64encode(article_url.encode()).decode()
                entry_id = f"ni://{url_base.hostname}/base64;{url_hash}"
                fe = fg.add_entry()
                fe.id(entry_id)
                fe.title(article["title"])
                fe.summary(article["description"])
                fe.link(href=article_url, rel="alternate")
                fe.updated(last_commit_dt)
        fg.atom_file(output_dir + "/atom.xml")
        fg.rss_file(output_dir + "/rss.xml")
        logging.debug("Wrote syndication feeds.")

    def render_article(
        self,
        content: str,
        path: str,
        template: Optional[jinja2.Template] = None,
        with_avatar=True,
    ) -> str:
        """content: Markdown content
        Return content in html format based on the jinja2 template"""
        if template is None:
            template = self.j2env.get_template("article.html.j2")
        title, description, md_content = self.parse_md(content)
        # TODO fix indexes not beeing rendered when render_article not previously called
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
            avatar_src="/media/avatar" if with_avatar else None,
        )

    def render_index(
        self,
        section: Optional[str] = None,
        template: Optional[jinja2.Template] = None,
        with_feeds=False,
        with_avatar=False,
    ) -> str:
        if template is None:
            template = self.j2env.get_template("index.html.j2")
        if section is None:
            # TODO sort by publication date
            paths = [p for ps in self.section_to_paths.values() for p in ps]
            section = "Home"
        else:
            paths = self.section_to_paths[section]
        articles = [self.articles_metadata[p] for p in paths]
        return template.render(
            title=section,
            articles=articles,
            sections=self.sections,
            feeds={"atom": "/atom.xml", "rss": "/rss.xml"} if with_feeds else {},
            avatar_src="/media/avatar" if with_avatar else None,
        )

    def add_static_assets(self, output_dir: str):
        """Copy static assets from the repo into the outupt dir.
        Use files from the package if not found"""
        media_dst = output_dir + "/media"
        custom_media = self.blog_path + "/media"
        if os.path.exists(custom_media):
            sync_dir(custom_media, media_dst)
        default_media = self.pkgdir + "/media"
        sync_dir(default_media, media_dst)

        css_dst = output_dir + "/style.css"
        default_css = self.pkgdir + "/style.css"
        custom_css = self.blog_path + "/style.css"
        if os.path.exists(custom_css):
            shutil.copyfile(custom_css, css_dst)
        else:
            shutil.copyfile(default_css, css_dst)
        logging.debug("Added static assets.")

    def download_avatar(self, output_dir: str):
        avatar_dst = output_dir + "/media/avatar"
        repo_uri = None
        if os.path.exists(avatar_dst):
            return
        # TODO try to get uri from .git/config as a fallback
        if _is_uri(self.source_repo):
            repo_uri = _parse_uri(self.source_repo)
        else:
            git_config = self.source_repo + "/.git/config"
            if not os.path.exists(git_config):
                return
            # TODO better parse toml and move to a specific function
            url_prefix = "\turl = "
            with open(git_config) as gc:
                for line in gc:
                    if line.startswith(url_prefix):
                        print(line)
                        repo_uri = _parse_uri(line.lstrip(url_prefix))
                        break
        if not repo_uri:
            return
        avatar_url = None
        if repo_uri.hostname == "github.com":
            username = repo_uri.path.split("/")[0]
            avatar_url = "https://avatars.githubusercontent.com/" + username
        elif repo_uri.hostname == "codeberg.org":
            # TODO move to a specific function
            username = repo_uri.path.split("/")[0]
            user_page = (
                request.urlopen("https://codeberg.org/" + username).read().decode()
            )
            meta_pattern = r'<meta .+"(https://codeberg.org/avatars/\w+)">'
            avatar_url = (
                re.search(meta_pattern, user_page, re.MULTILINE).group(1).rstrip()
            )

        if avatar_url:
            request.urlretrieve(avatar_url, avatar_dst)
            logging.debug("Downloaded avatar.")

    def gen_commits(self) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        def clean_commit(commit: Commit) -> Dict[str, Any]:
            commit_dt = _get_commit_dt(commit)
            # TODO use a proper data class here
            return {
                "iso_time": commit_dt.isoformat(),
                "human_time": commit_dt.strftime("%d %b %Y"),
                "author": commit.author,
                "message": commit.message,
            }

        for commit in self.repo.walk(self.last_commit.id):
            if commit.parents:
                prev = commit.parents[0]
                diff = prev.tree.diff_to_tree(commit.tree)
                for patch in diff:
                    path = patch.delta.new_file.path
                    if path.endswith(".md"):
                        if not self.repo_subdir or (
                            self.repo_subdir and path.startswith(self.repo_subdir + "/")
                        ):
                            path = path.removeprefix(self.repo_subdir + "/")
                            yield path, clean_commit(commit)

    def gen_articles_content(
        self, tree: Optional[Tree] = None, path=""
    ) -> Generator[Tuple[str, str], None, None]:
        """Traverse repo files an return any (path, content) tuple corresponding to non blacklisted Markdown files.
        The path parameter is recursively constructed as we traverse the tree."""
        if tree is None:
            tree = self.last_commit.tree
        for obj in tree:
            if obj.type == GIT_OBJ_TREE and obj.name not in self.dirs_blacklist:
                obj_relpath = f"{path}{obj.name}/"
                yield from self.gen_articles_content(cast(Tree, obj), obj_relpath)
            elif (
                cast(str, obj.name).endswith(".md")
                and (not self.repo_subdir or path.startswith(self.repo_subdir + "/"))
                and obj.name not in self.files_blacklist
            ):
                obj_relpath = f"{path.removeprefix(self.repo_subdir + '/')}{obj.name}"
                yield (obj_relpath, cast(Blob, obj).data.decode("utf-8"))
            elif cast(str, obj.name).endswith(".md"):
                logging.debug(f"Skipped {path}{obj.name}")

    def gen_sections(self) -> Generator[str, None, None]:
        """Yield all sections found for this blog"""
        tree = self.last_commit.tree
        # Move to the self.repo_subdir location
        if self.repo_subdir:
            for to_match in self.repo_subdir.split("/"):
                obj = None
                for obj in tree:
                    if obj.type == GIT_OBJ_TREE and obj.name == to_match:
                        tree = cast(Tree, obj)
                        break
                if obj is None or obj.name != to_match:
                    return
        # Enumerate all valid toplevel dirs
        for obj in tree:
            if obj.type == GIT_OBJ_TREE and obj.name not in self.dirs_blacklist:
                yield cast(str, obj.name)

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

    def _init_repo(self, fetch: bool = False) -> Repository:
        """Check if there is an existing repo at self.clone_dir and clone the repo there otherwise.
        Optionally fetch changes after that."""

        cloned_already = os.path.exists(self.clone_dir + "/.git/")
        if cloned_already:
            repo = Repository(self.clone_dir)
        else:
            repo = pygit2.clone_repository(self.source_repo, self.clone_dir)
            logging.debug(f"Cloned repo into {self.clone_dir}")
        repo = cast(Repository, repo)
        if fetch:
            repo.remotes["origin"].fetch()
            logging.debug("Fetched last changes.")
        return repo

    def _init_templating(self) -> jinja2.Environment:
        """Copy missing templates into the template dir if necessary
        and return a Jinja2Environment"""
        templates_dst = self.workdir.name + "/templates"
        custom_templates = self.blog_path + "/templates"
        if os.path.exists(custom_templates):
            sync_dir(custom_templates, templates_dst, symlink=True)
        default_templates = self.pkgdir + "/templates"
        sync_dir(default_templates, templates_dst, symlink=True)
        return jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dst))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.workdir.cleanup()


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


def _parse_uri(repo_link: str) -> ParseResult:
    if repo_link.startswith("http"):
        return urlparse(repo_link)
    netloc, path = repo_link.split(":")
    return ParseResult(
        scheme="ssh", netloc=netloc, path=path, params="", query="", fragment=""
    )


def _get_commit_dt(commit: Commit):
    # TODO double check the comuted datetime
    tz = datetime.timezone(datetime.timedelta(minutes=commit.commit_time_offset))
    dt = datetime.datetime.fromtimestamp(commit.commit_time, tz=tz)
    return dt
