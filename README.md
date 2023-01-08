# ![Gitblog2 Logo](https://blog.henritel.com/media/favicon.svg "title") Gitblog2

Git + Markdown = Blog

## TODO

High priority:

* Add bio and picture from github
* Draft support (set publish_date to first `mv`)
* E2E tests

Low priority:

* Unit tests
* Fix root index.html not served by redbean
* Make it work on non-unix systems (mainly dealing with windows file system separator)

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

## Internals

Stylesheet is based on water.css
