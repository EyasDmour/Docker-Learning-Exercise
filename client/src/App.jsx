import { useMemo, useState } from "react";
import DataTable from "./components/DataTable.jsx";
import { extractFirstArray } from "./utils/extractFirstArray.js";

const defaultEndpoint = import.meta.env.VITE_HASURA_URL || "http://localhost:8080/v1/graphql";
const defaultSecret = import.meta.env.VITE_HASURA_ADMIN_SECRET || "";

const exampleQuery = `query Example($limit: Int = 5) {
  your_table(limit: $limit) {
    id
    column_a
    column_b
  }
}`;

const exampleVariables = `{
  "limit": 5
}`;

export default function App() {
  const [endpoint, setEndpoint] = useState(defaultEndpoint);
  const [adminSecret, setAdminSecret] = useState(defaultSecret);
  const [query, setQuery] = useState(exampleQuery);
  const [variablesText, setVariablesText] = useState(exampleVariables);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRunQuery = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    let parsedVariables;

    if (variablesText.trim()) {
      try {
        parsedVariables = JSON.parse(variablesText);
      } catch (parseError) {
        setLoading(false);
        setError("Variables JSON is invalid");
        return;
      }
    }

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(adminSecret ? { "x-hasura-admin-secret": adminSecret } : {})
        },
        body: JSON.stringify({ query, variables: parsedVariables })
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const body = await response.json();

      if (body.errors) {
        throw new Error(body.errors.map((entry) => entry.message).join(" | "));
      }

      setResult(body.data || null);
    } catch (fetchError) {
      setResult(null);
      setError(fetchError.message);
    } finally {
      setLoading(false);
    }
  };

  const rows = useMemo(() => extractFirstArray(result), [result]);

  return (
    <div className="app-shell">
      <h1>GraphQL Data Explorer</h1>
      <p>
        Paste any GraphQL query targeting your Hasura instance, tweak the variables, and render the
        first array response below as a table.
      </p>
      <form onSubmit={handleRunQuery}>
        <label>
          Endpoint
          <input
            value={endpoint}
            onChange={(event) => setEndpoint(event.target.value)}
            placeholder="http://localhost:8080/v1/graphql"
          />
        </label>

        <label>
          Admin secret (optional)
          <input
            value={adminSecret}
            onChange={(event) => setAdminSecret(event.target.value)}
            placeholder="admin123"
          />
        </label>

        <label>
          Query
          <textarea
            rows={10}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>

        <label>
          Variables (JSON)
          <textarea
            rows={6}
            value={variablesText}
            onChange={(event) => setVariablesText(event.target.value)}
            placeholder="{}"
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Running..." : "Run query"}
        </button>
      </form>

      <div className="status-bar">
        {error && <span>Error: {error}</span>}
        {!error && loading && <span>Loading...</span>}
        {!error && !loading && result && <span>Success: {Object.keys(result).length} field(s) returned.</span>}
        {!error && !loading && !result && <span>Nothing fetched yet.</span>}
      </div>

      {rows && rows.length > 0 ? (
        <div className="table-wrapper">
          <DataTable rows={rows} />
        </div>
      ) : (
        <div className="empty-state">
          The first array field in the response will appear here as a table.
        </div>
      )}

      {result && (
        <section style={{ marginTop: "2rem" }}>
          <h2>Raw response</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </section>
      )}
    </div>
  );
}
