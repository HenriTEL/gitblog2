from base64 import b64encode
from collections import defaultdict
import logging
import os
import re
import shutil
from tempfile import TemporaryDirectory
from types import TracebackType
from typing import Type, cast, Generator, Optional
from urllib import request
from urllib.parse import ParseResult, urlparse
from functools import cached_property

from feedgen.feed import FeedGenerator
from feedgen.entry import FeedEntry
import jinja2
from markdown import markdown
import requests
from git.repo import Repo
from git import Commit, Tree
from git.types import PathLike

from gitblog2.blog_posts import BlogPosts


MD_LIB_EXTENSIONS = ["extra", "toc"]
MD_LIB_EXTENSION_CONFIGS = {"toc": {"title": " Table of contents"}}
GITHUB_API_HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    "X-GitHub-Api-Version": "2022-11-28",
}


class GitBlog:
    def __init__(
        self,
        source_repo: str,
        clone_dir: str = "",
        repo_subdir: str = "",
        ignore_dirs: list[str] = ["draft", "media", "templates", ".github"],
        ignore_files: list[str] = ["README.md", "LICENSE.md"],
        fetch: bool = True,
    ):
        self.source_repo = source_repo
        self.repo_subdir = repo_subdir.strip("/")
        self.ignore_dirs = ignore_dirs
        self.ignore_files = ignore_files

        self.workdir = TemporaryDirectory()
        if _is_uri(self.source_repo):
            self.clone_dir = clone_dir.rstrip("/") if clone_dir else self.workdir.name
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
        commits = self.repo.iter_commits(self.last_commit, paths=self.repo_subdir)
        self.blog_posts = BlogPosts(
            commits, self.repo_subdir, self.ignore_dirs, self.ignore_files
        )

        self.section_to_paths: defaultdict[str, set[str]] = defaultdict(set)
        self.old_to_new_path: dict[str, str] = {}

    @cached_property
    def sections(self) -> list[str]:
        _sections = list(self.gen_sections())
        logging.debug("Built sections.")
        return _sections

    @property
    def last_commit(self) -> Commit:
        return self.repo.head.commit

    @cached_property
    def repo_uri(self) -> ParseResult:
        if _is_uri(self.source_repo):
            return _parse_uri(self.source_repo)
        with self.repo.config_reader() as config_reader:
            uri = config_reader.get('remote "origin"', "url", fallback="")
        if not uri:
            logging.warning("Remote origin url not found in config.")
        return urlparse(str(uri))

    @cached_property
    def social_accounts(self) -> dict[str, str]:
        _social_accounts = {"syndication": "/atom.xml"}
        if self.repo_uri.hostname == "github.com":
            _social_accounts["github"] = (
                "https://github.com/" + self.repo_uri.path.split("/")[0]
            )
            gh_social_accounts: list[dict[str, str]] = self._github_api_get(
                "/user/social_accounts"
            )
            for account in gh_social_accounts:
                _social_accounts[account["provider"]] = account["url"]
        return _social_accounts

    def write_blog(
        self,
        output_dir: str,
        with_social: bool = True,
        base_url: ParseResult = urlparse(""),
    ):
        if with_social and not base_url.geturl():
            raise ValueError(
                "You need to provide your website base URL in order to generate social feeds."
            )
        if with_social:
            self.download_avatar(output_dir)

        self.write_articles(output_dir, with_social)
        self.write_indexes(output_dir, with_social)
        if with_social:
            self.write_syndication_feeds(output_dir, base_url=base_url)
        self.add_static_assets(output_dir)

    def write_articles(self, output_dir: str, with_social: bool = True):
        template = self.j2env.get_template("article.html.j2")
        for path, content in self.gen_articles_content():
            full_page = self.render_article(content, str(path), template, with_social)
            target_path = output_dir + "/" + str(path).replace(".md", ".html")
            _write_file(full_page, target_path)

    def write_indexes(self, output_dir: str, with_social: bool = True):
        for section in self.sections:
            target_path = f"{output_dir}/{section}/index.html"
            try:
                full_page = self.render_index(section, with_social)
            except Exception as ex:
                logging.error("Failed to render index for section %s", section)
                raise ex
            _write_file(full_page, target_path)

        home_page = self.render_index(with_social=with_social)
        _write_file(home_page, f"{output_dir}/index.html")

    def write_syndication_feeds(self, output_dir: str, base_url: ParseResult):
        url_hash = b64encode(base_url.geturl().encode()).decode()
        feed_id = f"ni://{base_url.hostname}/base64;{url_hash}"
        last_commit_dt = self.last_commit.committed_datetime
        author = str(self.last_commit.author)
        description = f"The latest news from {author}"
        feed = FeedGenerator()
        feed.id(feed_id)
        feed.title(description)
        feed.description(description)
        feed.author(name=author)
        feed.link(href=base_url.geturl())
        feed.logo(base_url.geturl() + "/media/favicon.svg")
        feed.updated(last_commit_dt)
        for _, paths in self.section_to_paths.items():
            for path in paths:
                blog_post = self.blog_posts[path]
                article_url = base_url.geturl() + "/" + blog_post.relative_path
                url_hash = b64encode(article_url.encode()).decode()
                entry_id = f"ni://{base_url.hostname}/base64;{url_hash}"

                feed_entry = FeedEntry()
                feed_entry.id(entry_id)
                feed_entry.title(blog_post.title)
                feed_entry.summary(blog_post.description)
                feed_entry.link(href=article_url, rel="alternate")
                feed_entry.updated(blog_post.last_update_dt)
                feed.add_entry(feed_entry)
        feed.atom_file(output_dir + "/atom.xml")
        feed.rss_file(output_dir + "/rss.xml")
        logging.debug("Wrote syndication feeds.")

    def render_article(
        self,
        content: str,
        path: str,
        template: Optional[jinja2.Template] = None,
        with_social: bool = True,
    ) -> str:
        """content: Markdown content
        Return content in html format based on the jinja2 template"""
        if template is None:
            template = self.j2env.get_template("article.html.j2")
        title, description, md_content = self.parse_md(content)
        # TODO fix indexes not beeing rendered when render_article not previously called
        self.blog_posts[path].title = title
        self.blog_posts[path].description = description
        self.blog_posts[path].read_time_minutes = (
            len(md_content.split(" ")) // 200
        ) or 1
        section = path.removeprefix(self.repo_subdir).lstrip("/").split("/")[0]
        self.section_to_paths[section].add(path)
        html_content = markdown(
            md_content,
            extensions=MD_LIB_EXTENSIONS,
            extension_configs=MD_LIB_EXTENSION_CONFIGS,
        )
        return template.render(
            blog_post=self.blog_posts[path],
            main_content=html_content,
            sections=self.sections,
            avatar_url="/media/avatar" if with_social else None,
            social_accounts=self.social_accounts if with_social else None,
        )

    def render_index(
        self,
        section: str = "Home",
        with_social: bool = True,
    ) -> str:
        template = self.j2env.get_template("index.html.j2")
        if section == "Home":
            # TODO sort by publication date
            section_paths = [p for ps in self.section_to_paths.values() for p in ps]
        else:
            section_paths = self.section_to_paths[section]
        section_posts = [self.blog_posts[p] for p in section_paths]
        if section == "Home" and with_social:
            feeds = {"atom": "/atom.xml", "rss": "/rss.xml"}
        else:
            feeds = {}
        return template.render(
            title=section,
            blog_posts=section_posts,
            sections=self.sections,
            feeds=feeds,
            avatar_url="/media/avatar" if with_social else None,
            social_accounts=self.social_accounts if with_social else None,
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

    def download_avatar(self, output_dir: str) -> None:
        avatar_dst = output_dir + "/media/avatar"
        if os.path.exists(avatar_dst):
            logging.warning("Avatar already downloaded.")
            return
        avatar_url = ""
        if self.repo_uri.hostname == "github.com":
            avatar_url = self._github_api_get("/user")["avatar_url"]

        if avatar_url:
            os.makedirs(os.path.dirname(avatar_dst), exist_ok=True)
            _, response = request.urlretrieve(avatar_url, avatar_dst)
            if response.get("content-type", "").startswith("image/"):
                print("Avatar downloaded.")
            else:
                logging.error("Avatar download response headers:\n%s", response)

    def gen_articles_content(
        self, tree: Optional[Tree] = None
    ) -> Generator[tuple[PathLike, str], None, None]:
        """Traverse repo files an return any (path, content) tuple corresponding to non blacklisted Markdown files.
        The path parameter is recursively constructed as we traverse the tree."""
        if tree is None:
            tree = self.last_commit.tree
            if self.repo_subdir:
                tree = cast(Tree, tree[self.repo_subdir])
        for obj in tree:
            if obj.type == "tree" and obj.name not in self.ignore_dirs:
                yield from self.gen_articles_content(obj)
            elif obj.type == "blob" and obj.name.endswith(".md"):
                if obj.name in self.ignore_files:
                    logging.debug("Skipped %s", obj.path)
                    continue
                yield obj.path, cast(bytes, obj.data_stream.read()).decode("utf-8")

    def gen_sections(self) -> Generator[str, None, None]:
        """Yield all sections found for this blog"""
        blog_root = self.last_commit.tree
        if self.repo_subdir:
            blog_root = cast(Tree, blog_root[self.repo_subdir])
        # Enumerate all valid toplevel dirs
        for tree in blog_root.trees:
            if tree.name not in self.ignore_dirs:
                yield tree.name

    def parse_md(self, md_content: str) -> tuple[str, str, str]:
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

    def _github_api_get(self, resource: str):
        response = requests.get(
            f"https://api.github.com{resource}", headers=GITHUB_API_HEADERS, timeout=10
        )
        response.raise_for_status()
        return response.json()

    def _init_repo(self, fetch: bool = True) -> Repo:
        """Check if there is an existing repo at self.clone_dir and clone the repo there otherwise.
        Optionally fetch changes after that."""

        cloned_already = os.path.exists(self.clone_dir + "/.git/")
        if cloned_already:
            repo = Repo(self.clone_dir)
        else:
            repo = Repo.clone_from(
                self.source_repo,
                self.clone_dir,
                multi_options=["--depth 1", "--no-checkout"],
            )
            logging.debug("Cloned repo with depth 1 into %s", self.clone_dir)
        if fetch:
            # TODO check shallow
            repo.remotes.origin.fetch(
                refspec=None,
                progress=None,
                verbose=True,
                kill_after_timeout=None,
                allow_unsafe_protocols=False,
                allow_unsafe_options=False,
                filter="blob:none",
                no_tags=True,
                unshallow=True,
            )
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

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception: Optional[BaseException],
        traceback: Optional[TracebackType],
    ):
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
            logging.debug("Added %s", dst_file)


def _write_file(content: str, target_path: str):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w+", encoding="utf-8") as file_descriptor:
        file_descriptor.write(content)
    logging.debug("Wrote %s", target_path)


def _is_uri(repo_link: str):
    return repo_link.startswith(("http", "git@"))


def _parse_uri(repo_link: str) -> ParseResult:
    if repo_link.startswith("http"):
        return urlparse(repo_link)
    netloc, path = repo_link.split(":")
    return ParseResult(
        scheme="ssh", netloc=netloc, path=path, params="", query="", fragment=""
    )
