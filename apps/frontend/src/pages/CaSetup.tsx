import { useEffect, useState } from "react";
import api from "../lib/api";

type Summary = {
  reachable?: boolean;
  step_ca_url?: string;
  root_fingerprint_openssl?: string;
  roots_bytes?: number;
  error?: string;
};

type Bootstrap = {
  summary: string;
  downloads: Record<string, string>;
  external_urls: Record<string, string>;
  manual_init_commands?: string[];
};

export default function CaSetup() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [bootstrap, setBootstrap] = useState<Bootstrap | null>(null);
  const [err, setErr] = useState("");
  const [plan, setPlan] = useState<{ command: string; next_steps: string[]; worker_env_example: string } | null>(null);
  const [form, setForm] = useState({
    name: "My PKI",
    dns_names: "step-ca,localhost",
    address: ":9000",
    provisioner: "admin",
    enable_acme: true,
    enable_remote_management: true,
    enable_ssh: false,
  });

  useEffect(() => {
    Promise.all([api.get("/ca/summary"), api.get("/ca/bootstrap")])
      .then(([s, b]) => {
        setSummary(s.data);
        setBootstrap(b.data);
      })
      .catch((e) => setErr(e?.response?.data?.detail || "Failed to load CA info"));
  }, []);

  const download = async (path: string, filename: string) => {
    const res = await api.get(path, { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const buildPlan = async () => {
    const res = await api.post("/ca/init-plan", form);
    setPlan(res.data);
  };

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-semibold">CA setup & trust material</h1>
      {err && <p className="text-red-400">{err}</p>}

      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-3">
        <h2 className="font-medium text-slate-200">How your CA is initialized</h2>
        <p className="text-sm text-slate-400 whitespace-pre-wrap">{bootstrap?.summary}</p>
        {bootstrap && (
          <div className="rounded bg-slate-950 p-3 text-xs text-slate-300">
            <p className="mb-1 text-slate-400">Manual init commands</p>
            <ul className="space-y-1">
              <li>
                <code>cd infra</code>
              </li>
              <li>
                <code>docker compose run --rm step-ca-init</code>
              </li>
              <li>
                <code>docker compose up --build</code>
              </li>
            </ul>
          </div>
        )}
        <p className="text-xs text-slate-500">
          To run your own CA long-term: keep step-ca data on a volume, initialize with your own parameters, and never commit private keys.
        </p>
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-3">
        <h2 className="font-medium text-slate-200">Build your custom init command</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input
            className="rounded bg-slate-800 px-3 py-2"
            placeholder="PKI Name"
            value={form.name}
            onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
          />
          <input
            className="rounded bg-slate-800 px-3 py-2"
            placeholder="DNS names (comma separated)"
            value={form.dns_names}
            onChange={(e) => setForm((p) => ({ ...p, dns_names: e.target.value }))}
          />
          <input
            className="rounded bg-slate-800 px-3 py-2"
            placeholder="Address (e.g. :9000)"
            value={form.address}
            onChange={(e) => setForm((p) => ({ ...p, address: e.target.value }))}
          />
          <input
            className="rounded bg-slate-800 px-3 py-2"
            placeholder="First provisioner"
            value={form.provisioner}
            onChange={(e) => setForm((p) => ({ ...p, provisioner: e.target.value }))}
          />
        </div>
        <div className="flex flex-wrap gap-4 text-sm text-slate-300">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={form.enable_acme} onChange={(e) => setForm((p) => ({ ...p, enable_acme: e.target.checked }))} />
            ACME
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.enable_remote_management}
              onChange={(e) => setForm((p) => ({ ...p, enable_remote_management: e.target.checked }))}
            />
            Remote management
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={form.enable_ssh} onChange={(e) => setForm((p) => ({ ...p, enable_ssh: e.target.checked }))} />
            SSH certificates
          </label>
        </div>
        <button type="button" className="rounded bg-indigo-600 px-3 py-2 text-sm" onClick={buildPlan}>
          Generate init command
        </button>
        {plan && (
          <div className="rounded bg-slate-950 p-3 text-xs text-slate-300 space-y-2">
            <p className="text-slate-400">Run from `infra`:</p>
            <code className="block whitespace-pre-wrap break-all">{plan.command}</code>
            <p className="text-slate-400">Then set worker password:</p>
            <code className="block whitespace-pre-wrap break-all">{plan.worker_env_example}</code>
            <ul className="list-disc pl-5">
              {plan.next_steps.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-3">
        <h2 className="font-medium text-slate-200">Live CA status</h2>
        {summary && (
          <ul className="text-sm text-slate-300 space-y-1">
            <li>Reachable: {summary.reachable ? "yes" : "no"}</li>
            <li>URL: {summary.step_ca_url}</li>
            <li>roots.pem size: {summary.roots_bytes ?? 0} bytes</li>
            {summary.root_fingerprint_openssl && (
              <li className="break-all">Root fingerprint: {summary.root_fingerprint_openssl}</li>
            )}
            {summary.error && <li className="text-amber-400">Note: {summary.error}</li>}
          </ul>
        )}
        <div className="flex flex-wrap gap-2 pt-2">
          <button
            type="button"
            className="rounded bg-emerald-600 px-3 py-2 text-sm"
            onClick={() => download("/ca/roots.pem", "roots.pem")}
          >
            Download root CA (roots.pem)
          </button>
          <button
            type="button"
            className="rounded bg-blue-600 px-3 py-2 text-sm"
            onClick={() => download("/ca/intermediate.pem", "intermediate.pem")}
          >
            Try download intermediate PEM
          </button>
        </div>
        {bootstrap?.external_urls && (
          <p className="text-xs text-slate-500 pt-2">
            Direct step-ca (browser, skip TLS verify):{" "}
            <a className="text-indigo-400 underline" href={bootstrap.external_urls.step_ca_roots} target="_blank" rel="noreferrer">
              roots.pem
            </a>
          </p>
        )}
      </div>
    </div>
  );
}
