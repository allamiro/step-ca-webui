import { useEffect, useState } from "react";
import api from "../lib/api";

export default function Acme() {
  const [info, setInfo] = useState<Record<string, string>>({});
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get("/acme")
      .then((res) => setInfo(res.data))
      .catch((e) => setErr(e?.response?.data?.detail || "Failed to load ACME info"));
  }, []);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-semibold">ACME</h1>
      {err && <p className="text-red-400">{err}</p>}
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-2 text-sm">
        <p className="text-slate-400">{info.note}</p>
        <ul className="space-y-2 text-slate-300">
          {Object.entries(info)
            .filter(([k]) => k.endsWith("_url"))
            .map(([k, v]) => (
              <li key={k}>
                <span className="text-slate-500">{k}: </span>
                <a className="text-indigo-400 underline break-all" href={v} target="_blank" rel="noreferrer">
                  {v}
                </a>
              </li>
            ))}
        </ul>
      </div>
    </div>
  );
}
