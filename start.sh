#!/bin/bash
npx concurrently --kill-others \
  "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000" \
  "NODE_ENV=development npx tsx server/index.ts"
