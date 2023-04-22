# ![Gitblog2 Logo](https://blog.henritel.com/media/favicon.svg "title") Gitblog2

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)  

**Git + Markdown = Blog**  
**Check the [live demo](https://blog.henritel.com)**  

## What is this?

A blog generator that keeps things simple:  

* 🏄 **Easy to use** - Just write Markdown, no need for a metadata header.
* ⚡ **Minimal footprint** - No JavaScript, no divs, no class attributes, just semantic html.  
* 🛠 **Familiar tech** - Git, Markdown, Jinja2 templating.

With many features:

* **RSS feeds** - Atom also provided
* **Profile card** - based on your Github profile

## Getting Started

**From zero to a live blog.**

You can see the full setup of a working blog [here](https://github.com/HenriTEL/blog).  
For this tutorial we assume you'll use **Github** to host your repo and **Cloudflare Pages** to host your blog. You need to have account on those platforms as a prerequisite.  

1. Create a repo, add a folder of your first section, add a Markdown file in it for your first blog post.  
Use a `draft/` folder to save posts that are not ready for publication.  
Non Markdown files and common irrelevant content is ignored by default, e.g. `.github/`, `README.md`, `LICENSE.md`.

2. Add a `.github/workflows/publish.yaml` file to your repo with the following content:

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
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              BASE_URL: <YOUR_BLOG_URL>
              CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
              CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    ```

    Set `BASE_URL` with your blog's base url.  
    This will automatically publish your blog on Cloudflare Pages when you push changes to your repo.  
    It assumes your cloudflare project is named `blog` but if that's not the case you can add an `CLOUDFLARE_PROJECT` env to the workflow with the correponding name.
3. In your repo's settings, go under `secrets/actions` to set the `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` secrets based on your [Cloudflare API keys](https://developers.cloudflare.com/fundamentals/api/get-started/keys/#view-your-api-key).  
You don't need to setup `GITHUB_TOKEN` as it will be provided a run time by GitHub.

## Installation

```bash
pip install gitblog2
```

## Usage

From the command line:

```bash
gitblog2 https://codeberg.org/HenriTEL/gitblog2.git --repo-subdir=example --url-base=https://example.com --no-social
```

From the library:

```python
from gitblog2 import GitBlog

source_repo = "https://codeberg.org/HenriTEL/git-blog.git"
output_dir = "./www"
url_base = "https://example.com"
with GitBlog(source_repo, repo_subdir="example") as gb:
    gb.write_blog(output_dir, base_url=url_base, with_social=False)
```

From the container:

```bash
docker run --rm -v $PWD/www:/www \
    -e SOURCE_REPO=https://github.com/HenriTEL/gitblog2.git \
    -e REPO_SUBDIR=example \
    -e URL_BASE=https://example.com \
    -e NO_SOCIAL=true \
    henritel/gitblog2
```

## Customisation

Gitblog2 just produces static file so it should easily integrate with the stack you're familiar with (cron jobs, commit hooks, nginx, apache, you name it.).  
You can use <https://simplecss.org/demo> as an alternate stylesheet.

## Dev quickstart

Make sure to have [poetry](https://python-poetry.org/) installed, then  
Setup your local web server:

```bash
poetry install
wget "https://redbean.dev/redbean-tiny-2.2.com" -O redbean.zip
zip redbean.zip -j providers/assets/.init.lua
chmod +x redbean.zip
```

In one terminal, update the blog as needed:

```bash
poetry run gitblog2 -l debug --repo-subdir=example --base-url=https://example.com --no-social
```

In another terminal, serve the blog:

```bash
./redbean.zip -D ./www
```

## Roadmap

High priority:

* Fix gh workflow
* Add image in README like <https://github.com/nextcloud/server>

Low priority:

* Check draft support (set meta publish_date to first `mv`)
* E2E tests
* Deal with TODOs or make issues for newcomers
* Add doc for customisation
* Make a better TOC extension (remove div and classes)
* Unit tests
* Add contributing section
* Remove div and classes from footnotes

## Golden resources

<https://modernfontstacks.com/>
<https://anthonyhobday.com/sideprojects/saferules/>
<https://lawsofux.com/>
<https://developer.mozilla.org/en-US/docs/Web/HTML>
<https://developer.mozilla.org/en-US/docs/Web/CSS>
<https://developer.mozilla.org/en-US/docs/Web/SVG>
<https://icons.getbootstrap.com/>
