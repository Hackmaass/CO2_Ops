#!/bin/sh
set -e

# Render env.js from the template using real container env vars, so the static
# frontend knows the backend URL and API key without hardcoding them at build time.
envsubst '${CO2OPS_API_URL} ${CO2OPS_API_KEY}' \
  < /usr/share/nginx/html/env.js.template \
  > /usr/share/nginx/html/env.js

exec nginx -g "daemon off;"
