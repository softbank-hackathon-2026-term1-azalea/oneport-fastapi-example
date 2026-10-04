#!/bin/sh
set -eu

command="${1:-serve}"

case "$command" in
  migrate)
    exec python -m app.prestart
    ;;
  serve)
    python -m app.prestart
    exec uvicorn app.main:app \
      --host 0.0.0.0 \
      --port "${PORT:-8080}" \
      --proxy-headers \
      --forwarded-allow-ips='*' \
      --no-access-log
    ;;
  *)
    echo "unknown command: $command (expected: serve | migrate)" >&2
    exit 2
    ;;
esac
