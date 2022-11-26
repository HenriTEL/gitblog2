#!/bin/bash

wrangler pages publish --project-name "${CLOUDFLARE_PROJECT:-blog}" "${OUTPUT_DIR:-www/}"
