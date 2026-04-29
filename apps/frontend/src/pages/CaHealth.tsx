import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../lib/api";

export default function CaHealth() {
  const [status, setStatus] = useState("loading");
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    api
      .get("/ca/health")
      .then((res) => setStatus(res.data.status))
      .catch(() => setStatus("unreachable"));
    api
      .get("/ca/summary")
      .then((res) => setSummary(res.data))
      .catch(() => setSummary(null));
  }, []);

  return (
    <div className="p-6 space-y-4">
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <h2 className="text-lg font-semibold">CA Health</h2>
        <p className="text-slate-300">API health: {status}</p>
        {summary && (
          <pre className="mt-3 max-h-64 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-400">
            {JSON.stringify(summary, null, 2)}
          </pre>
        )}
        <Link className="mt-3 inline-block text-sm text-indigo-400 underline" to="/ca-setup">
          Open CA setup (downloads & init notes)
        </Link>
      </div>
    </div>
  );
}
