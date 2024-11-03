import logging
import os
import re
import subprocess
from base64 import b64encode
from collections import defaultdict
from functools import cached_property
from pathlib import Path
from types import TracebackType
from typing import Generator, Optional, cast
from urllib import request
from urllib.parse import ParseResult, urlparse

import jinja2
import requests
from feedgen.entry import FeedEntry
from feedgen.feed import FeedGenerator
from git import Commit, Tree
from git.repo import Repo
from markdown import markdown

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
    ):
        self.source_repo = source_repo
        self.pkgdir = Path(__file__).parent
        logging.debug("pkgdir is`%s`", self.pkgdir)

        self.section_to_paths: defaultdict[str, set[Path]] = defaultdict(set)
        self.old_to_new_path: dict[str, str] = {}

    @cached_property
    def sections(self) -> list[str]:
        _sections = list(self.gen_sections())
        return _sections

    @property
    def last_commit(self) -> Commit:
        return self.repo.head.commit

    @cached_property
    def repo_uri(self) -> ParseResult:
        def make_uri(uri: str) -> ParseResult:
            if uri.startswith("http"):
                return urlparse(self.source_repo)
            if uri.startswith("git@"):
                netloc, path = self.source_repo.split(":")
                return ParseResult(
                    scheme="ssh", netloc=netloc, path=path, params="", query="", fragment=""
                )
            raise ValueError("Invalid URI")
    
        try:
            return make_uri(self.source_repo)
        except ValueError:
            with self.repo.config_reader() as config_reader:
                uri = config_reader.get('remote "origin"', "url", fallback="")
                if not uri:
                    logging.warning("Remote origin url not found in config.")
            return make_uri(uri)

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

    def init_repo(self, clone_dir: Path, no_fetch: bool = False):
        """Check if there is an existing repo at self.clone_dir and clone the repo there otherwise.
        Optionally fetch changes after that."""

        cloned_already = (clone_dir / ".git").exists()
        if cloned_already:
            self.repo = Repo(clone_dir)
        else:
            self.repo = Repo.clone_from(
                self.source_repo,
                clone_dir,
                multi_options=["--depth 1", "--no-checkout"],
            )
            logging.debug("Cloned repo with depth 1 into %s", clone_dir)
        if not no_fetch:
            cmd = "git rev-parse --is-shallow-repository"
            is_shallow = subprocess.check_output(cmd, shell=True).decode().startswith("true")
            self.repo.remotes.origin.fetch(
                refspec=None,
                progress=None,
                verbose=True,
                kill_after_timeout=None,
                allow_unsafe_protocols=False,
                allow_unsafe_options=False,
                filter="blob:none",
                no_tags=True,
                unshallow=is_shallow,
            )

    def write_blog(
        self,
        output_dir: Path,
        *,
        repo_subdir: str = "",
        ignore_dirs: tuple[str, ...] = ("draft", "media", "templates", ".github"),
        ignore_files: tuple[str, ...] = ("README.md", "LICENSE.md"),
        with_social: bool = True,
        # TODO user pydantic URL
        base_url: ParseResult = urlparse(""),
    ):
        # TODO remove the following attribute affecttions to make this method more modular
        self.repo_subdir = repo_subdir
        self.blog_path = Path(self.repo.git_dir) / self.repo_subdir
        self.ignore_dirs = ignore_dirs
        self.ignore_files = ignore_files

        if with_social:
            if not base_url.geturl():
                raise ValueError(
                    "You need to provide your website base URL in order to generate social feeds."
                )
            self.download_avatar(output_dir)

        self.j2env = self._init_templating()
        commits = self.repo.iter_commits(self.last_commit, paths=repo_subdir)
        self.blog_posts = BlogPosts(
            commits, repo_subdir, self.ignore_dirs, self.ignore_files
        )

        self.write_articles(output_dir, with_social)
        self.write_indexes(output_dir, with_social)
        if with_social:
            self.write_syndication_feeds(output_dir, base_url=base_url)
        self.add_static_assets(output_dir)

    def write_articles(self, output_dir: Path, with_social: bool = True):
        template = self.j2env.get_template("article.html.j2")
        for path, content in self.gen_articles_content():
            rel_path = self.blog_posts[path].relative_path
            full_page = self.render_article(content, path, template, with_social)
            target_path = (output_dir / rel_path).with_suffix(".html")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(full_page)
            logging.debug("Added `%s`", target_path)

    def write_indexes(self, output_dir: Path, with_social: bool = True):
        for section in self.sections:
            target_path = output_dir / section / "index.html"
            try:
                full_page = self.render_index(section, with_social)
            except Exception as ex:
                logging.error("Failed to render index for section %s", section)
                raise ex
            target_path.write_text(full_page)
            logging.debug("Added `%s`", target_path)

        home_page = self.render_index(with_social=with_social)
        home_path = output_dir / "index.html"
        home_path.write_text(home_page)
        logging.debug("Added `%s`", home_path)

    def write_syndication_feeds(self, output_dir: Path, base_url: ParseResult):
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
                article_url = base_url.geturl() + f"/{blog_post.relative_path}"
                url_hash = b64encode(article_url.encode()).decode()
                entry_id = f"ni://{base_url.hostname}/base64;{url_hash}"

                feed_entry = FeedEntry()
                feed_entry.id(entry_id)
                feed_entry.title(blog_post.title)
                feed_entry.summary(blog_post.description)
                feed_entry.link(href=article_url, rel="alternate")
                feed_entry.updated(blog_post.last_update_dt)
                feed.add_entry(feed_entry)
        feed.atom_file(str(output_dir / "atom.xml"))
        feed.rss_file(str(output_dir / "rss.xml"))
        logging.debug("Wrote syndication feeds.")

    def render_article(
        self,
        content: str,
        path: Path,
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
        section = path.relative_to(self.repo_subdir).parts[0]
        self.section_to_paths[section].add(path)
        html_content = markdown(
            md_content,
            extensions=MD_LIB_EXTENSIONS,
            extension_configs=MD_LIB_EXTENSION_CONFIGS,
        )
        try:
            final_html = template.render(
                blog_post=self.blog_posts[path],
                main_content=html_content,
                sections=self.sections,
                avatar_url="/media/avatar" if with_social else None,
                social_accounts=self.social_accounts if with_social else None,
            )
        except Exception as e:
            logging.error("Failed to render `%s`", path)
            raise e
        return final_html

    def render_index(
        self,
        section: str = "Home",
        with_social: bool = True,
    ) -> str:
        template = self.j2env.get_template("index.html.j2")
        if section == "Home":
            section_paths = {p for ps in self.section_to_paths.values() for p in ps}
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

    def add_static_assets(self, output_dir: Path):
        """Copy static assets from the repo into the outupt dir.
        Use files from the package if not found"""
        media_dst = output_dir / "media"
        custom_media = self.blog_path / "media"
        if custom_media.exists():
            sync_dir(custom_media, media_dst)
        default_media = self.pkgdir / "media"
        sync_dir(default_media, media_dst)

        (output_dir / "css").mkdir(parents=True, exist_ok=True)
        for css in ("css/layout.css", "css/theme.css"):
            css_dst = output_dir / css
            default_css = self.pkgdir / css
            custom_css = self.blog_path / css
            css_content = custom_css.read_bytes() if custom_css.is_file() else default_css.read_bytes()
            css_dst.write_bytes(css_content)
        logging.debug("Added static assets.")

    def download_avatar(self, output_dir: Path) -> None:
        avatar_dst = output_dir / "media/avatar"
        if avatar_dst.exists():
            logging.warning("Avatar already downloaded.")
            return
        avatar_url = ""
        if self.repo_uri.hostname == "github.com":
            avatar_url = self._github_api_get("/user")["avatar_url"]

        if avatar_url:
            avatar_dst.parent.mkdir(parents=True, exist_ok=True)
            _, response = request.urlretrieve(avatar_url, avatar_dst)
            if response.get("content-type", "").startswith("image/"):
                print("Avatar downloaded.")
            else:
                logging.error("Avatar download response headers:\n%s", response)

    def gen_articles_content(
        self, tree: Optional[Tree] = None
    ) -> Generator[tuple[Path, str], None, None]:
        """Traverse repo files an return any (path, content) tuple corresponding to non blacklisted Markdown files.
        The path parameter is recursively constructed as we traverse the tree."""
        if tree is None:
            tree = self.last_commit.tree
            if self.repo_subdir:
                tree = tree[str(self.repo_subdir)]
        for obj in tree:
            if obj.type == "tree" and obj.name not in self.ignore_dirs:
                yield from self.gen_articles_content(obj)
            elif obj.type == "blob" and obj.name.endswith(".md"):
                if obj.name in self.ignore_files:
                    logging.debug("Skipped `%s`", obj.path)
                    continue
                yield Path(obj.path), cast(bytes, obj.data_stream.read()).decode("utf-8")

    def gen_sections(self) -> Generator[str, None, None]:
        """Yield all sections found for this blog"""
        blog_root = self.last_commit.tree
        if self.repo_subdir:
            blog_root = cast(Tree, blog_root[str(self.repo_subdir)])
        # Enumerate all valid toplevel dirs
        for tree in blog_root.trees:
            if tree.name not in self.ignore_dirs:
                yield tree.name

    def parse_md(self, md_content: str) -> tuple[str, str, str]:
        """Return title, description and main_content of the article
        (md_content minus the title and description).
        """
        res: list[str] = []
        title_pattern = r"^# (.+)\n"
        desc_pattern = r"^>\s*(.*(?:\n>\s*.*)*)"
        for pattern in (title_pattern, desc_pattern):
            match = re.search(pattern, md_content, re.MULTILINE)
            if match:
                res.append(match.group(1).rstrip().replace("\n> ", "\n"))
                md_content = re.sub(pattern, "", md_content, 1, re.MULTILINE)
            else:
                res.append("")
        return res[0], res[1], md_content

    def _github_api_get(self, resource: str):
        response = requests.get(
            f"https://api.github.com{resource}", headers=GITHUB_API_HEADERS, timeout=10
        )
        response.raise_for_status()
        return response.json()

    def _init_templating(self) -> jinja2.Environment:
        """Copy missing templates into the template dir if necessary
        and return a Jinja2Environment"""
        templates_dst = Path(self.repo.git_dir) / "templates"
        custom_templates = self.blog_path / "templates"
        if custom_templates.exists():
            sync_dir(custom_templates, templates_dst, symlink=True)
        default_templates = self.pkgdir / "templates"
        sync_dir(default_templates, templates_dst, symlink=True)
        return jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dst))


def sync_dir(src: Path, dst: Path, symlink: bool = False):
    """Add files that are missing from src into dst, optionally using symlinks"""
    dst.mkdir(parents=True, exist_ok=True)
    for file in src.iterdir():
        src_file = src / file.name
        dst_file = dst / file.name
        if dst_file.is_dir():
            raise FileExistsError(f"Cannot create file `{dst_file}` as it is an existing directory.")
        if not dst_file.exists():
            if symlink:
                dst_file.symlink_to(src_file)
            else:
                dst_file.write_bytes(src_file.read_bytes())
            logging.debug("Added `%s` to `%s`", src_file, dst)


