# ![Gitblog2 Logo](https://blog.henritel.com/media/favicon.svg "title") Gitblog2

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)  

Check a [live demo](https://blog.henritel.com).  

## What is this?

A blog generator that keeps things simple:  

* 🏄 **Straightforward** - Just write Markdown.
* ⚡ **Minimal footprint** - about 15KB uncompressed.
* 🌐 **Universal** - No JavaScript, no divs, no css classes, just semantic html.  
* 🛠 **Familiar tooling** - Git, Markdown, Jinja2.

While provinding modern features:

* **Modern look** - with support for other stylesheets
* **RSS and Atom feeds**
* **Avatar and social accounts** - based on your Github profile

## Getting Started

**From zero to a live blog.**

You can see the full setup of a working blog [here](https://github.com/HenriTEL/blog).  
For this tutorial we'll assume that you use **Github** to host your repo and **Cloudflare Pages** to host your blog. You need to have accounts on those platforms as a prerequisite.  

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
              BASE_URL: <YOUR_BLOG_URL>
              GITHUB_TOKEN: ${{ secrets.RO_GITHUB_TOKEN }}
              CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
              CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    ```

    Set `BASE_URL` with your blog's base url.  
    This will automatically publish your blog on Cloudflare Pages when you push changes to your repo.  
    It assumes your cloudflare project is named `blog` but if that's not the case you can add an `CLOUDFLARE_PROJECT` env to the workflow with the correponding name.
3. In your repo's settings, go under `secrets/actions` to set the `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` secrets based on your [Cloudflare API keys](https://developers.cloudflare.com/fundamentals/api/get-started/keys/#view-your-api-key). Also setup a `RO_GITHUB_TOKEN` if you want to add social capabilities like a profile pic and links to social accounts. Go to <https://github.com/settings/tokens/> to generate a token with `read:user` access rights.

## Installation

```bash
pip install gitblog2
```

There's also a [container image](https://hub.docker.com/repository/docker/henritel/gitblog2) available on docker hub.

## Usage

From the command line:

```bash
gitblog2 https://codeberg.org/HenriTEL/gitblog2.git --repo-subdir=example --url-base=https://example.com --no-social
```

From the library:

```python
from gitblog2 import GitBlog

source_repo = "https://codeberg.org/HenriTEL/git-blog.git"
output_dir = "./public"
url_base = "https://example.com"
with GitBlog(source_repo, repo_subdir="example") as gb:
    gb.write_blog(output_dir, base_url=url_base, with_social=False)
```

From the container:

```bash
docker run --rm -v $PWD/public:/public \
    -e SOURCE_REPO=https://github.com/HenriTEL/gitblog2.git \
    -e REPO_SUBDIR=example \
    -e BASE_URL=https://example.com \
    -e NO_SOCIAL=true \
    henritel/gitblog2
```

## Customisation

Gitblog2 just produces static file so it should integrate seamlessly integrate with anything (cron jobs, commit hooks, nginx, apache, you name it.).  
You can use [simplecss](https://simplecss.org/demo) as an alternate stylesheet, support for more stylesheets is planned.

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
./redbean.zip -D ./public
```

## Roadmap

High priority:

* Move the doc to the wiki with different audiences.
* Add image in README like <https://github.com/nextcloud/server>
* reduce python version compatibility
* remove changelog

Low priority:

* Add gitlab support
* Add about page (and link to it from pp) based on user bio and README.md
* Check draft support (set meta publish_date to first `mv`)
* Use user's profile handle first and commit author only as a fallback
* E2E tests
* Deal with TODOs or make issues for newcomers
* Improve score on <https://pagespeed.web.dev/analysis/https-blog-henritel-com/oktd50o2sy?form_factor=desktop>
* Add doc for customisation
  * Change template + accessible variables
  * Add icons
  * Change main color theme
* Make a script to remove unused icons
* Make a better TOC extension (remove div and classes)
* Make markdown renderer set loading="lazy" on img tags
* Unit tests, pagespeed test
* Linting (pylint + pyre?)
* Refactor lib.py into multiple files
* Add contributing section
* Remove div and classes from footnotes

## Golden resources

<https://accessiblepalette.com>
<https://modernfontstacks.com/>  
<https://anthonyhobday.com/sideprojects/saferules/>  
<https://lawsofux.com/>  
<https://developer.mozilla.org/en-US/docs/Web/HTML>  
<https://developer.mozilla.org/en-US/docs/Web/CSS>  
<https://developer.mozilla.org/en-US/docs/Web/SVG>  
<https://icons.getbootstrap.com/>  

## Classless stylesheets candidates

<https://github.com/kevquirk/simple.css/blob/main/simple.css>  

<https://github.com/yegor256/tacit>  
<https://github.com/kognise/water.css>  
<https://github.com/xz/new.css>  
<https://github.com/edwardtufte/tufte-css>  
<https://github.com/programble/writ>  
<https://github.com/oxalorg/sakura>  
<https://github.com/susam/spcss>  
