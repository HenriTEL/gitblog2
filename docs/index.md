# ![Gitblog2 Logo](https://blog.henritel.com/media/favicon.svg "title") Gitblog2

> Git + Markdown = Blog

[![PyPI Version][pypi-v-image]][pypi-v-link]

Gitblog2 is a blog generator focused on speed and simplicity.  
Blog posts are written in Markdown and that's it.  
Look at it yourself: this [live example](https://blog.henritel.com) is solely based on [this repository](https://github.com/HenriTEL/blog).

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
gitblog2 https://github.com/HenriTEL/gitblog2.git --repo-subdir=example --base-url=https://example.com --no-social
```

From the library:

```python
from gitblog2 import GitBlog

source_repo = "https://github.com/HenriTEL/gitblog2.git"
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

* support frontmatter
* git comments
* strike through not working (both ~ and ~~)

Improve the CLI using tips from <https://clig.dev>:

* Once installed, show what commands to run to actually start using it
* Comprehensive help texts
* Provide lots of examples
* Suggest what command to run next
* Suggest what to do when there is an error.
* Provide useful commands to debug nd explore, maybe `gitblog2 tree` to have a look at what the generated blog would look like, `gitblog config` to find what options are enabled/disabled. Think about ways to show metadata on articles like the updated/created at fields, maybe also list the custom templates and what articles would make use of them.
* Add a dry-run option
* Think about detecting misconfigurations, providing helpful message that point toward the right direction (e.g. line number in the faulty template).
* On the other hand, say when everything looks good (`gitblog troublesoot`?).
* Autocompletion?
* Not printing scary-looking stack traces, explain errors instead.
* Link the docs and code on the help page
* Link the code from the docs
* Make sure to exit with 0 for success and non-zero otherwise
* Make sure only machine readable content goes to stdout
* Messaging goes to stderr
* Provide terminal-based documentation (and maybe a man page)
* Use colors and ASCII art (like in ls -l) when relevant (output stream == TTY -> human), also ckeck the NO_COLOR or FORCE_COLOR envs.
* Think about `--json`, `--plain` and `--jsonl` to format the output for computers
* Provide `-q` to avoid all text output
* Use emojis to catch the user’s attention on critical things
* When stderr is a TTY, add criticity in logs only in verbose mode, and write the catched error in red at the end + a solution
* When stderr is not a TTY it's ok to output log levels, also tracebacks for unexpected or unexplainable error
* Add progress indicators for long operations (progress bar like docker pull?)
* Have some cache capabilities and make long operations recoverable
* Defer cleanup operations to the next run (exit faster on first error encountered)
* Make sure that env vars are only for user-specific config, settings that are likely to change on a run basis should be flag-only (e.g. -v, --quiet, --dry-run)
* Don't read secrets from env. Only via credential files, pipes, AF_UNIX sockets, secret management services, or another IPC mechanism.
* Make it a standalone executable with something like <https://github.com/pyinstaller/pyinstaller>
* Have a command to uninstall it, print it at the end of the installation process.

Low priority:

* If avatar already present, don't attempt to download it and include it in the blog.
* Add gitlab support
* Add about page (and link to it from pp) based on user bio and README.md
* Use user's profile handle first and commit author only as a fallback
* E2E tests
* Deal with code's TODOs or make issues for newcomers
* Improve score on <https://pagespeed.web.dev/analysis/https-blog-henritel-com/oktd50o2sy?form_factor=desktop>
* Add doc for customisation
  * Change template + accessible variables
  * Add icons
  * Change main color theme
* Make a script to remove unused icons
* Make a better TOC extension (remove div and classes)
* Make markdown renderer set loading="lazy" on img tags
* Unit tests, pagespeed test
* Refactor lib.py
* Add contributing section
* Remove div and classes from footnotes

## Great content

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


<!-- Badges -->
[pypi-v-image]: https://img.shields.io/pypi/v/gitblog2.svg
[pypi-v-link]: https://pypi.org/project/gitblog2/
