#!/bin/sh
set -e
OUTPUT_DIR=$1

for md_article_path in $(find articles/ -name '*.md'); do
	html_article_path="${OUTPUT_DIR}/${md_article_path%%.*}.html"
	gomplate --file "templating/article.tmpl.html" \
	    --datasource article_md="file://${PWD}/${input_article_path}" \
		--out "${html_article_path}"
done
