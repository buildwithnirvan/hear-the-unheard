# NOT YET RUN AGAINST A REAL DOCKER DAEMON — see backend/Dockerfile's note
# and docs/STATUS.md. Written carefully against the actual package.json
# this repo has, but unverified.
FROM node:22-slim AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .

# NEXT_PUBLIC_* vars are baked into the client bundle at BUILD time, not
# read at container start — they must be passed as build args, not just
# environment variables on the running container, or the frontend will
# silently keep pointing at localhost:8000 regardless of what you set at
# `docker run` / compose runtime.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/recognize
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]
