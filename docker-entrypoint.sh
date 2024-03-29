#!/bin/sh
set -e

OUTPUT_DIR="${OUTPUT_DIR:-/public}"
rm -rf "${OUTPUT_DIR}/"*
echo "Cleaned content under ${OUTPUT_DIR}"

gitblog2 "${SOURCE_REPO}" "${OUTPUT_DIR}"

for cmd in "$@"; do
	"/providers/${cmd}.sh"
done
