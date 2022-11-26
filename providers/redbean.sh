#!/bin/bash

wget "https://redbean.dev/redbean-tiny-${REDBEAN_VERSION:-2.2}.com" -O redbean.zip
chmod +x redbean.zip
zip -r redbean.zip assets/.init.lua "${OUTPUT_DIR:-www/}"
rm -r "${OUTPUT_DIR:-www}/*"
mv redbean.zip "${OUTPUT_DIR:-www/}"
