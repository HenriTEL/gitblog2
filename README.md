# ![Gitblog2 Logo](gitblog2/media/favicon.svg "title") Gitblog2

Git + Markdown = Blog

## TODO

High priority:

* if nb_commits > 1: last_commit else "Updated on last_commit < info_tooltip hover='published on first_commit'>"
* Add bio and picture from github
* Look at cool HTML elements: <https://tapajyoti-bose.medium.com/7-cool-html-elements-nobody-uses-436598d85668>
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
    gb.write_articles(output_dir)
    gb.write_indexes(output_dir)
    gb.copy_static_assets(output_dir)
```

As a container:

```bash
docker run --rm -v $PWD/www:/www \
    -e SOURCE_REPO=https://codeberg.org/HenriTEL/gitblog2.git \
    -e REPO_SUBDIR=example \
    henritel/gitblog2
```

## Deploy to Cloudflare-pages using Github action

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

## Internals

Stylesheet is based on water.css
