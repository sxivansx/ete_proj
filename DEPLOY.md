# Deploying the CO Attainment app

Target: a single Linux server you SSH into. HTTP only for now (TLS
comes later when a domain is ready). Single public port: whatever you
set for `PORT` in `.env` (defaults to `80`).

## Prerequisites on the server
- Docker Engine ≥ 24 and the Docker Compose plugin
  (`docker compose version` should work — not the old `docker-compose`).
- Port 80 (or your chosen `PORT`) open in the firewall.
- Git, so you can pull updates.

Quick install on Ubuntu/Debian:
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER    # log out and back in for this to take effect
```

## First-time bring-up

```bash
# 1. Get the code onto the server
git clone https://github.com/sxivansx/ete_proj.git
cd ete_proj

# 2. Copy the env template and tweak if needed
cp .env.example .env
# edit .env — set PORT if you don't want 80

# 3. Build and start
docker compose up -d --build

# 4. Sanity check
curl http://localhost/api/v1/health     # -> {"status":"ok"}
curl -I http://localhost/               # -> HTTP/1.1 200 OK
```

Open `http://<server-ip>/` in a browser and upload an xlsx.

## Updating
```bash
cd ete_proj
git pull
docker compose up -d --build
```

`--build` re-runs the image builds; the Vite + wheel layers get cached
so most pulls take under a minute on a small VPS.

## Inspecting / debugging
```bash
docker compose ps                # see container state + health
docker compose logs -f api       # tail FastAPI logs
docker compose logs -f web       # tail nginx access/error logs
docker compose exec api sh       # shell inside the API container
```

## Stopping
```bash
docker compose down              # stop + remove containers
docker compose down --volumes    # + wipe any volumes (none yet; harmless)
```

## What's on the network
- `web` container (nginx + the SPA) publishes to the host on `PORT`.
- `api` container (uvicorn + FastAPI) is **not** published to the host.
  Only `web` can reach it, via the docker-internal DNS name `api:8000`.
- Compose creates a private bridge network per project — no other
  containers on the server can talk to `api` without joining that
  network explicitly.

## HTTPS (when you're ready)
Two reasonable options:
1. **Terminate TLS on the host.** Keep the compose as-is but set
   `PORT=127.0.0.1:8080` in `.env` so the stack only listens on
   localhost, then front it with Caddy / nginx on the host that has
   a certificate (Let's Encrypt via Caddy is the lowest-effort path).
2. **Add a Caddy service to the compose.** One more service in
   `docker-compose.yml`, bind `:80` and `:443` on it, point it at
   `web:80` internally. Caddy auto-issues certs for a domain. Ask
   and I'll wire this up when you've got the domain pointed at
   the server.

## Rolling back to a known-good build
```bash
# find the last green commit on origin/main
git log --oneline
git checkout <sha>
docker compose up -d --build
```

All state (uploads, DB) is ephemeral today — Phase 4 will add a
persistent volume for `data/uploads/` and postgres.
