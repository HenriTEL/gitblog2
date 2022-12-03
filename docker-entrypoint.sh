#!/bin/bash
set -e

rm -r "${OUTPUT_DIR:-www}/"*
echo "Cleaned content under ${OUTPUT_DIR:-www}/"
./main.py
for cmd in "$@"; do
	"./providers/${cmd}.sh"
done
