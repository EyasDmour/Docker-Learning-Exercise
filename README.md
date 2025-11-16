# Postgres + Hasura + YouthInvestments Playground

A full‑stack playground for experimenting with a modern data‑driven app:

- **PostgreSQL** as the primary database
- **Hasura GraphQL Engine** to auto-generate a real-time GraphQL API
- **Auth0** for authentication and JWT-based authorization (failed/gave up)
- **React (YouthInvestments)** as the main front-end
- **Vite-based GraphQL client** for testing queries and mutations
- **Python UI service** for simple DB admin views
- Everything wired together with **Docker Compose**

## Why this project exists

This repo is a learning sandbox to:

- Practice modelling data in **PostgreSQL** and writing SQL
- Explore how **Hasura** exposes a Postgres schema via GraphQL with permissions
- Understand **JWT flows** end-to-end using **Auth0** and Hasura's JWT config :(
- Build a **React** front-end that talks securely to a GraphQL backend
- Get hands-on with **Docker**, multi-service dev environments, and environment-based config

It’s meant for anyone who wants to inspect the stack, run it locally, and extend it.

## Repository layout

- `docker-compose.yml` – Orchestrates all services (Postgres, Hasura, pgAdmin, UIs)
- `schema/` – Database schema / SQL (e.g. users table)
- `Insertions.sql`, `Queries.sql` – Example data and query scripts
- `ui/` – Python (FastAPI/Uvicorn) admin-style UI
- `client/` – Vite React GraphQL client for Hasura
- `YouthInvestments/` – Main React + Auth0 front-end app
- `portal/` – Nginx config / HTML portal
- `postgresData/` – Local Postgres data volume (ignored by Git)

## Stack & tools

**Backend & data**
- PostgreSQL
- Hasura GraphQL Engine
- SQL (schema, queries, inserts)

**APIs & auth**
- GraphQL (queries, mutations, roles)
- Auth0 (SPA auth, access tokens, JWKS / JWT configuration) :(
- Hasura JWT + role-based permissions :(

**Front-end**
- React + Vite (`YouthInvestments/` and `client/`)
- `@auth0/auth0-react` for authentication in React :(

**DevOps / tooling**
- Docker & Docker Compose
- Local `.env` configuration
- Git & GitHub

## Getting started

### Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ (only needed if you want to run the React apps outside Docker)

### Clone the repo

```bash
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>
```

### Configure Auth0 (local only, and it probably wont work, but do try anyways) 

Create an Auth0 application (Single Page Application) and API, then set up these values in local env files (these files are **ignored by Git**; do not commit them):

In `YouthInvestments/.env.local`:

```bash
VITE_AUTH0_DOMAIN=your-tenant.eu.auth0.com
VITE_AUTH0_CLIENT_ID=your_spa_client_id
VITE_AUTH0_AUDIENCE=https://your-api-identifier
VITE_HASURA_GRAPHQL_URL=http://localhost:8080/v1/graphql
```

If your `client/` app also needs Auth0/Hasura settings, use similar `VITE_...` vars in `client/.env.local`.

> Note: All secrets / keys should live in `.env` / `.env.local` files only. The repo never needs your real credentials.

### Configure Hasura JWT (Auth0)

In `docker-compose.yml`, the Hasura service is configured with:

```yaml
HASURA_GRAPHQL_JWT_SECRET: '{"jwk_url":"https://youthinvestments.eu.auth0.com/.well-known/jwks.json"}'
```

For your own Auth0 tenant, change the domain to match your Auth0 domain:

```yaml
HASURA_GRAPHQL_JWT_SECRET: '{"jwk_url":"https://<your-tenant>.eu.auth0.com/.well-known/jwks.json"}'
```

For production or shared environments, you should override this and other secrets via real environment variables / secret management, not hard-code them.

## Running the stack with Docker

From the repo root:

```bash
docker compose up --build
```

This will start:

- **Postgres** on `localhost:5432`
- **pgAdmin** on `http://localhost:5050`
- **Hasura** on `http://localhost:8080`
- **Python UI** on `http://localhost:8000`
- **GraphQL client** (Vite) on `http://localhost:5173`
- **YouthInvestments React app** on `http://localhost:5174`

All services share a Docker network defined by `docker-compose.yml`.

To stop everything:

```bash
docker compose down
```

## Running apps individually (optional)

You can also run apps outside Docker for faster dev loops.

### YouthInvestments React app

```bash
cd YouthInvestments
npm install
npm run dev
```

Then open `http://localhost:5174` (or the port Vite prints).

### GraphQL client

```bash
cd client
npm install
npm run dev
```

Open `http://localhost:5173`.

### Python UI

```bash
cd ui
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Security & secrets

- **Do not commit** `.env`, `.env.local`, or any real API keys or secrets – in this repo they are already gitignored. (i learned this the hard way previously)
- Values like `admin123` in `docker-compose.yml` are **dev-only placeholders**. Replace them with secure values via env vars in real deployments.
- For Auth0 + Hasura integration, use:
  - Auth0 JWKS URL in `HASURA_GRAPHQL_JWT_SECRET`
  - Access tokens from Auth0 (via `@auth0/auth0-react`) sent as `Authorization: Bearer <token>` to Hasura. (didnt reach this point to due to invalid JWTs and gave up... i gave up because i already learned so much in this project, this was a good time to stop and recap and begin something new)

## Extending the project

Ideas for extending this playground:

- Add more tables and relations to the Postgres schema
- Configure Hasura roles and row-level permissions
- Build richer React views (lists, detail pages, mutations)
- Add tests or CI workflows for the frontend and backend

PRs, forks, and experiments are all welcome – this repo is meant to be a place to tinker and learn, ecspeacially if you are able to figure out where my JWTs went wrong.
