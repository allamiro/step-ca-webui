import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../lib/api";
import keycloak from "../lib/auth";

type Me = {
  preferred_username: string;
  roles: string[];
};

type CaSummary = {
  reachable?: boolean;
  step_ca_url?: string;
  root_fingerprint_openssl?: string;
};

export default function Dashboard() {
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState("");
  const [ca, setCa] = useState<CaSummary | null>(null);

  useEffect(() => {
    api
      .get("/auth/me")
      .then((res) => setMe(res.data))
      .catch((err) => setError(err?.response?.data?.detail || "Failed to load user profile"));
    api
      .get("/ca/summary")
      .then((res) => setCa(res.data))
      .catch(() => setCa({ reachable: false }));
  }, []);

  return (
    <div className="p-6 space-y-4">
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <h1 className="text-xl font-semibold">PKI Dashboard</h1>
        <p className="text-slate-400">Issue and manage certificates through the API and async jobs. Initialize and download trust material under CA Setup.</p>
        <div className="mt-4 flex flex-wrap gap-2 text-sm">
          <Link className="rounded bg-emerald-700 px-3 py-2" to="/issue">Issue certificate</Link>
          <Link className="rounded bg-slate-700 px-3 py-2" to="/ca-setup">CA setup & downloads</Link>
          <Link className="rounded bg-slate-700 px-3 py-2" to="/certificates">Certificates</Link>
          <Link className="rounded bg-slate-700 px-3 py-2" to="/provisioners">Provisioners</Link>
        </div>
      </div>
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <p>User: {me?.preferred_username ?? "loading..."}</p>
        <p>Roles: {me?.roles?.join(", ") ?? "loading..."}</p>
        {error && <p className="mt-2 text-red-400">{error}</p>}
        <button
          className="mt-3 rounded bg-indigo-600 px-3 py-2 text-sm"
          onClick={() => keycloak.logout()}
        >
          Logout
        </button>
      </div>
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <h2 className="font-medium text-slate-200 mb-2">step-ca</h2>
        {ca && (
          <ul className="text-sm text-slate-300 space-y-1">
            <li>Reachable: {ca.reachable ? "yes" : "no"}</li>
            <li>URL: {ca.step_ca_url}</li>
            {ca.root_fingerprint_openssl && (
              <li className="break-all text-xs">Root fingerprint: {ca.root_fingerprint_openssl}</li>
            )}
          </ul>
        )}
      </div>
    </div>
  );
}
