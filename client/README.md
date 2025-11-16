# GraphQL Data Explorer

A minimal React + Vite client you can point at your Hasura GraphQL endpoint to experiment with queries and render the first array field as a table.

## Quick start

```fish
cd client
npm install
npm run dev -- --host
```

Then open the printed URL (defaults to `http://localhost:5173`).

### Run inside Docker Compose

The root `docker-compose.yml` now includes this client as `graphql-client`. Start the whole stack:

```fish
cd ..
docker compose up --build graphql-client
```

Visit `http://localhost:5173` once the Vite dev server reports it is ready.

## Configuration

Create a `.env.local` file inside `client/` if you want to set defaults:

```
VITE_HASURA_URL=http://localhost:8080/v1/graphql
VITE_HASURA_ADMIN_SECRET=admin123
```

You can override both inside the UI at any time. Leave the admin secret blank if you are using public roles.

## Using the explorer

- Paste a GraphQL query into the query box. The default is a template; replace `your_table` and column names with ones from your schema.
- Optionally provide JSON variables. The editor will warn you if the JSON cannot be parsed.
- Submit to see the raw response and, if the first field contains an array of records, a table preview.
- Nested objects are stringified so you can keep drilling down with follow-up queries.

This client intentionally stays simple so you can iterate quickly while learning Hasura queries and role-based permissions.
