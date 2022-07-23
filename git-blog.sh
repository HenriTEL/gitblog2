#!/bin/sh
set -e
SOURCE_DIR="/blog"
TARGET_DIR="/out"

mkdir -p "${TARGET_DIR}"
for md_article in $(find "${SOURCE_DIR}/articles" -name '*.md'); do
	html_article="${TARGET_DIR}/${md_article%%.*}.html"
	# git log formatting explained at https://git-scm.com/docs/pretty-formats
	git -C "${SOURCE_DIR}" log --pretty=format:'%as|%aI|%an|%s' "${md_article}" \
	| gomplate --file "templates/article.tmpl.html" \
		--context article_content="file://${PWD}/${md_article}" \
		--context changelog="stdin:" \
		--out "${html_article}"
done
