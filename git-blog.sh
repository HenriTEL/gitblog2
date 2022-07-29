#!/bin/sh
set -e
REPO_URI=$1
SOURCE_DIR="/blog"
TARGET_DIR="/out"

mkdir -p "${TARGET_DIR}"
[[ ! -z "${REPO_URI}" ]] && git clone --depth 1 "${REPO_URI}" "${SOURCE_DIR}"
for md_file in $(find "${SOURCE_DIR}" -name '*.md'); do
	html_file="${TARGET_DIR}/${md_file%%.*}.html"
	# git log formatting explained at https://git-scm.com/docs/pretty-formats
	git -C "${SOURCE_DIR}" log --pretty=format:'%as|%aI|%an|%s' "${md_file}" \
	| gomplate --file "templates/default.tmpl.html" \
		--context page_content="file://${md_file}" \
		--context changelog="stdin:" \
		--out "${html_file}"
done
