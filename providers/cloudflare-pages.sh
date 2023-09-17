#!/bin/sh

# TODO fail when CLOUDFLARE_PROJECT not set
wrangler pages publish --project-name "${CLOUDFLARE_PROJECT:-blog}" "${OUTPUT_DIR:-/public/}"
