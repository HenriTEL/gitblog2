#!/bin/sh
set -e

if [ ! -d blog/ ]; then
	git clone "${REPO_URL}" blog/
fi
cd blog/
./gen_blog.sh "${OUTPUT_DIR}"

while true; do
	if git fetch --dry-run 2>&1 | grep origin; then
		git pull
		./gen_blog.sh "${OUTPUT_DIR}"
	fi
	sleep 60
done
