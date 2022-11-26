#!/bin/bash
set -e

./main.py
for cmd in "$@"; do
	"./providers/${cmd}.sh"
done
