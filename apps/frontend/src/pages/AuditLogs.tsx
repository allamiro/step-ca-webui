import { useEffect, useState } from "react";
import api from "../lib/api";

type AuditLog = {
  id: number;
  actor: string;
  action: string;
  resource: string;
  status: string;
  created_at: string;
};

export default function AuditLogs() {
  const [rows, setRows] = useState<AuditLog[]>([]);

  useEffect(() => {
    api.get("/audit-logs").then((res) => setRows(res.data));
  }, []);

  return (
    <div className="p-6">
      <h2 className="mb-4 text-lg font-semibold">Audit Logs</h2>
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-slate-400">
              <th>When</th>
              <th>Actor</th>
              <th>Action</th>
              <th>Resource</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-t border-slate-800">
                <td>{new Date(row.created_at).toLocaleString()}</td>
                <td>{row.actor}</td>
                <td>{row.action}</td>
                <td>{row.resource}</td>
                <td>{row.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
