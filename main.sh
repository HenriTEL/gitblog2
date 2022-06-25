#!/bin/sh
set -e

git clone "${REPO_URL}" blog/
cd blog/
./gen_blog.sh "${OUTPUT_DIR}"

while true; do
	if ! git fetch --dry-run; then
		git pull
		./gen_blog.sh "${OUTPUT_DIR}"
	fi
    sleep 60
done
