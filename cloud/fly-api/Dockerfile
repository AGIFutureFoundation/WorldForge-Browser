# WorldForge API on Fly.io. Build context = repo root (see fly.toml); paths below are from there.
# Node 24 runs the shared TypeScript route file natively (type stripping) -- same source as the
# Cloudflare Worker, so the two deployments can never drift.
FROM node:24-alpine
WORKDIR /app

# deps first (cached layer)
COPY cloud/fly-api/package.json ./cloud/fly-api/
WORKDIR /app/cloud/fly-api
RUN npm install --omit=dev

# app + the shared marketplace-v2 route file, mirrored at the same relative path as the repo
COPY cloud/fly-api/server.mjs ./
COPY cloud/datasets-api/src/routes/marketplace-v2.ts /app/cloud/datasets-api/src/routes/marketplace-v2.ts

# movement LM artifacts served by /v2/motion/*
COPY site/earth/data/motion/model.json /app/site/earth/data/motion/model.json
COPY site/earth/data/motion/samples.json /app/site/earth/data/motion/samples.json
COPY earth/motion/corpus/corpus-stats.json /app/earth/motion/corpus/corpus-stats.json

ENV PORT=8080
EXPOSE 8080
CMD ["node", "server.mjs"]
