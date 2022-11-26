#!/bin/bash
set -e

./main.py
for cmd in "$@"; do
	"./provider/${cmd}.sh"
done
