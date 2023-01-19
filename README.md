# ![Gitblog2 Logo](https://blog.henritel.com/media/favicon.svg "title") Gitblog2

Git + Markdown = Blog  

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## What is this?

This is a blog generator that keeps things simple...  

- It's easy to use (see the 3 lines documentation below).
- It produce pages of minimal complexity (no JavaScript, no divs, no class attributes, just semantic html)

...Yet there's a lot going behind the scene.  
Thanks to all the metada produced with git, it can find the author, publication date and changelog for your articles.

That way you can focus on writing instead of reading the documentation to setup >insert static site generator here<.
You still have a lot of flexibility if you want to publish with another provider, add some analytics, use another theme or whatever. The advantage of this minimal complexity is that it's easy to customise, and in the end it just produce static file so it should integrate with any stack you're familiar with (cron jobs, commit hooks, nginx, Apache, you name it.).

## Documentation

Create a repo, its root folders will be your blog sections, Markdown files in those folders will be your blog posts.  
Use a `draft` folder to save posts that are not ready for publication.
Common unrelated files are ignored by default, e.g. `.github/`, `README.md`, `LICENSE.md`.

## Installation

```bash
pip install gitblog2
```

## Usage

As a command line:

```bash
gitblog https://codeberg.org/HenriTEL/git-blog.git --repo-subdir=example
```

As a library:

```python
from gitblog2 import GitBlog

source_repo = "https://codeberg.org/HenriTEL/git-blog.git"
output_dir = "./www"
with GitBlog(source_repo, repo_subdir="example") as gb:
    gb.write_blog(output_dir)
```

As a container:

```bash
docker run --rm -v $PWD/www:/www \
    -e SOURCE_REPO=https://codeberg.org/HenriTEL/gitblog2.git \
    -e REPO_SUBDIR=example \
    henritel/gitblog2
```

## Deploy to Cloudflare Pages using Github Actions

You can write your blog on GitHub and automatically push changes to Cloudflare Pages using this GitHub Action:

```yaml
name: Publish Blog
on:
  push:
    branches: [ main ]
jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: docker://henritel/gitblog2
        with:
          args: post-css cloudflare-pages
        env:
          SOURCE_REPO: https://github.com/${{ github.repository }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

Don't forget to set your cloudflare secrets.

## Dev quickstart

Make sure to have [poetry](https://python-poetry.org/) installed, then  
Setup your local web server:

```bash
wget "https://redbean.dev/redbean-tiny-2.2.com" -O redbean.zip
zip redbean.zip -j providers/assets/.init.lua
chmod +x redbean.zip
```

In one terminal, update the blog as needed:

```bash
poetry run gitblog2 --repo-subdir example -l debug
```

In another terminal, serve the blog:

```bash
./redbean.zip -D ./www
```

## Roadmap

High priority:

- make a script to publish new releases on git, pip and docker hub (also update the Dockerfile)
- Add bio and picture from github
- Add RSS feed
- Add doc for customisation
- Check draft support (set publish_date to first `mv`)
- E2E tests

Low priority:

- Unit tests
- Add contributing section
- Add bio and picture from codeberg
- Remove div and classes from TOC and footnotes
- Fix root index.html not served by redbean
- Make it work on non-unix systems (mainly dealing with windows file system separator)

## Internals

Stylesheet is based on water.css
