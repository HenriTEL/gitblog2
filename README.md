# ![Gitblog2 Logo](gitblog2/media/favicon.svg "title") Gitblog2

Git + Markdown = Blog

## TODO

High priority:
* Set output_dir for copy_static_assets
* Sync template and static assets in a temp dir to keep repo clean
* if nb_commits > 1: last_commit else "Updated on last_commit < info_tooltip hover='published on first_commit'>"
* Add bio and picture from github
* Look at cool HTML elements: <https://tapajyoti-bose.medium.com/7-cool-html-elements-nobody-uses-436598d85668>
* Draft support (set publish_date to first `mv`)

Low priority:
* Fix root index.html not served by redbean

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

## Internals

Stylesheet is based on water.css
