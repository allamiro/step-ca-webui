import { FormEvent, useEffect, useState } from "react";
import api from "../lib/api";

export default function Settings() {
  const [settings, setSettings] = useState<any>(null);
  const [saved, setSaved] = useState("");

  useEffect(() => {
    api.get("/settings").then((res) => setSettings(res.data));
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const res = await api.put("/settings", settings);
    setSaved(`Saved by ${res.data.updated_by}`);
  };

  return (
    <div className="p-6">
      <h2 className="mb-4 text-lg font-semibold">Settings</h2>
      {settings && (
        <form onSubmit={submit} className="space-y-3 rounded-lg border border-slate-800 bg-slate-900 p-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.security.require_approval}
              onChange={(e) =>
                setSettings((prev: any) => ({
                  ...prev,
                  security: { ...prev.security, require_approval: e.target.checked },
                }))
              }
            />
            Require approval for certificate issuance
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.security.allow_wildcard_certificates}
              onChange={(e) =>
                setSettings((prev: any) => ({
                  ...prev,
                  security: { ...prev.security, allow_wildcard_certificates: e.target.checked },
                }))
              }
            />
            Allow wildcard certificates
          </label>
          <button type="submit" className="rounded bg-indigo-600 px-3 py-2 text-sm">
            Save settings
          </button>
          {saved && <p className="text-emerald-400">{saved}</p>}
        </form>
      )}
    </div>
  );
}
