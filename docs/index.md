# ![Gitblog2 Logo](https://blog.henritel.com/media/favicon.svg "title") Gitblog2

> Git + Markdown = Blog

![Package version](
https://img.shields.io/pypi/v/gitblog2?color=%2334D058&label=pypi%20package)

Gitblog2 is a blog generator focused on speed and simplicity.
Blog posts are written in Markdown and that's it. Here is a [live example](https://blog.henritel.com) solely based on [this repository](https://github.com/HenriTEL/blog). See? It's just Markdown with a bunch or images.   

## Features

* Build static HTML files from Markdown files. No JavaScript, no divs, no css classes.
* Low footprint (about 10kB compressed).
* Profile picture and social accounts included based on your Github profile.
* RSS and Atom feeds.

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

## Roadmap

High priority:

* Move the doc to the wiki with different audiences.
* Add image in README like <https://github.com/nextcloud/server>

Low priority:

* If avatar already present, don't attempt to download it and include it in the blog.
* Add gitlab support
* Add about page (and link to it from pp) based on user bio and README.md
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
