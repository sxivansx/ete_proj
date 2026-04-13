# syntax=docker/dockerfile:1.7
# ---------- stage 1: build with Bun ----------
FROM oven/bun:1.3 AS builder

WORKDIR /app

# Copy manifest + lockfile first for better cache hits.
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# Copy the rest of the source and build the SPA.
COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src
RUN bun run build

# ---------- stage 2: nginx runtime ----------
FROM nginx:1.27-alpine AS runtime

# Replace the default site config with ours: SPA fallback + /api proxy.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Ship the built static assets.
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# nginx:alpine's entrypoint already starts nginx in the foreground.
