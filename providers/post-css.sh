#!/bin/bash

CSS_PATH="${OUTPUT_DIR:-www}/style.css"

purgecss --css "${CSS_PATH}" --content "${OUTPUT_DIR:-www}/**/*.html" --output "${CSS_PATH}"
postcss --no-map --use autoprefixer --use cssnano --replace "${CSS_PATH}"
echo "Optimized css with purgecss, autoprefixer and cssnano."
