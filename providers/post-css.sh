#!/bin/sh

OUTPUT_DIR="${OUTPUT_DIR:-/public}"
CSS_PATH="${OUTPUT_DIR}/style.css"

purgecss --css "${CSS_PATH}" --content "${OUTPUT_DIR}/**/*.html" --output "${CSS_PATH}"
postcss --no-map --use autoprefixer --use cssnano --replace "${CSS_PATH}"
echo "Optimized css with purgecss, autoprefixer and cssnano."
