# ![Git-blog Logo](gitblog2/media/favicon.svg "title") Git-blog

Git + Markdown = Blog

## TODO

High priority:
* Set output_dir for copy_static_assets
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
