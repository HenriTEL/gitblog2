#!/bin/bash
set -e

if [[ $# -ne 1 ]]; then
	echo "ERROR: Illegal number of parameters" >&2
	echo 'Usage: ./release.sh "Your release title"' >&2
	exit 2
fi

poetry publish --build

GITBLOG2_VERSION=$(poetry version | awk '{print $2}')

docker build --build-arg GITBLOG2_VERSION=${GITBLOG2_VERSION} . \
	-t henritel/gitblog2:${GITBLOG2_VERSION} \
	-t henritel/gitblog2
docker push henritel/gitblog2:${GITBLOG2_VERSION}
docker push henritel/gitblog2

git commit -m "$1"
git pull
git push
git tag -a "v${GITBLOG2_VERSION}" -m "$1"
git push origin "v${GITBLOG2_VERSION}"
