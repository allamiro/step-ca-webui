import { useEffect, useState } from "react";
import api from "../lib/api";

type Cert = {
  id: number;
  common_name: string;
  sans: string;
  status: string;
};

export default function Certificates() {
  const [certs, setCerts] = useState<Cert[]>([]);
  const [message, setMessage] = useState("");

  const refresh = () => api.get("/certificates").then((res) => setCerts(res.data));

  useEffect(() => {
    refresh();
  }, []);

  const runAction = async (type: "renew" | "revoke", certificateId: number) => {
    setMessage("Submitting job...");
    const body = type === "renew" ? { certificate_id: certificateId } : { certificate_id: certificateId, reason: "manual revoke" };
    const res = await api.post(`/certificates/${type}`, body);
    setMessage(`Queued ${type} job #${res.data.job_id}`);
    refresh();
  };

  return (
    <div className="p-6">
      <h2 className="mb-4 text-lg font-semibold">Certificates</h2>
      {message && <p className="mb-3 text-sm text-emerald-400">{message}</p>}
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-slate-400">
              <th>ID</th>
              <th>CN</th>
              <th>SANs</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {certs.map((c) => (
              <tr key={c.id} className="border-t border-slate-800">
                <td>{c.id}</td>
                <td>{c.common_name}</td>
                <td>{c.sans}</td>
                <td>{c.status}</td>
                <td className="space-x-2 py-2">
                  <button
                    className="rounded bg-blue-600 px-2 py-1 text-xs"
                    onClick={() => runAction("renew", c.id)}
                  >
                    Renew
                  </button>
                  <button
                    className="rounded bg-rose-600 px-2 py-1 text-xs"
                    onClick={() => runAction("revoke", c.id)}
                  >
                    Revoke
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
