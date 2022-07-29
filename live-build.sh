#!/bin/sh

build() {
  change=$@
  ./git-blog.sh
  [[ ! -z "${change}" ]] && echo "Did rebuild after ${change}"
  cp -r example/media /out/blog
}

if [ -z "$(which docker)" ]; then
  # Container context
  build
  inotifywait --recursive --monitor --format "%e %w%f" \
      --exclude '/\.' \
      --event modify,move,create,delete ./ \
      | while read change; do
          build "${change}"
        done
else
  # Host context
  docker run -it --rm --name git-blog-builder \
    -v "${PWD}":/live:ro \
    -v "${PWD}/example":/blog:ro \
    -v "${PWD}/.out":/out \
    --workdir /live \
    --entrypoint ./live-build.sh \
    henritel/git-blog
fi
