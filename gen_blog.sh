#!/bin/sh
set -e
OUTPUT_DIR=$1

cp -r media/ "${OUTPUT_DIR}"
for md_article_path in $(find articles/ -name '*.md'); do
	html_article_path="${OUTPUT_DIR}/${md_article_path%%.*}.html"
	gomplate --file "templates/article.tmpl.html" \
		--context article_md="file://${PWD}/${md_article_path}" \
		--out "${html_article_path}"
done
