# Nginx Portal Service

This directory backs the lightweight landing page that lives at `http://localhost:7000` when the
`portal` service is running in Docker Compose. It serves `html/index.html` and also proxies the
other containers so you can reach them under tidy sub-paths, all through the stock `nginx:alpine`
image.

## Edit the landing page

Adjust `html/index.html` and restart the container when you want to add links or update copy:

```fish
cd /home/eyas/Projects/PG_DB
docker compose restart portal
```

The container mounts the HTML directory as read-only inside Nginx, so the markup updates whenever
the file changes. The Nginx configuration lives in `conf/default.conf`; edit that if you need to add
or change proxy routes.

## Reverse proxy routes

The portal exposes each UI locally through these paths:

- `http://localhost:7000/graphql-client/` → Vite client (`graphql-client` container)
- `http://localhost:7000/hasura/` → Hasura console (`hasura` container)
- `http://localhost:7000/pgadmin/` → pgAdmin (`pgadmin` container)
- `http://localhost:7000/fastapi/` → Python UI (`PG_UI` container)
