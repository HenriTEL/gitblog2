#!/bin/bash

wget --quiet "https://redbean.dev/redbean-tiny-${REDBEAN_VERSION:-2.2}.com" -O redbean.zip
chmod +x redbean.zip
zip redbean.zip -j providers/assets/.init.lua
zip -r redbean.zip "${OUTPUT_DIR:-www/}"
rm -r "${OUTPUT_DIR:-www}/"*
mv redbean.zip "${OUTPUT_DIR:-www/}"
