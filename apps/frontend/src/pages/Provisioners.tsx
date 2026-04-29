import { useEffect, useState } from "react";
import api from "../lib/api";

type Row = Record<string, unknown>;

export default function Provisioners() {
  const [items, setItems] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [sourcePath, setSourcePath] = useState("");

  useEffect(() => {
    api
      .get("/provisioners")
      .then((res) => {
        setItems(res.data.items || []);
        setSourcePath(res.data.source_path || "");
        setError(res.data.error || "");
      })
      .catch((e) => setError(e?.response?.data?.detail || "Failed to load provisioners"));
  }, []);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-semibold">Provisioners</h1>
      <p className="text-sm text-slate-400">
        Fetched from step-ca via admin token (worker). Requires <code className="text-slate-300">STEP_CA_PASSWORD</code> on the worker
        matching step-ca init.
      </p>
      {error && <p className="text-amber-400 text-sm">{error}</p>}
      {sourcePath && <p className="text-xs text-slate-500">Source: {sourcePath}</p>}
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-slate-400">
              <th className="py-2">Name / type</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row, idx) => (
              <tr key={idx} className="border-t border-slate-800">
                <td className="py-2 align-top font-mono text-xs">
                  {String((row as { name?: string }).name ?? (row as { type?: string }).type ?? `row-${idx}`)}
                </td>
                <td className="font-mono text-xs whitespace-pre-wrap break-all">{JSON.stringify(row)}</td>
              </tr>
            ))}
            {!items.length && !error && <tr><td colSpan={2} className="py-4 text-slate-500">No rows returned.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
