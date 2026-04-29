import { FormEvent, useState } from "react";
import api from "../lib/api";

type Job = {
  id: number;
  status: string;
  error?: string;
};

export default function IssueCertificate() {
  const [commonName, setCommonName] = useState("");
  const [sans, setSans] = useState("");
  const [job, setJob] = useState<Job | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const response = await api.post("/certificates/issue", {
      common_name: commonName,
      sans: sans.split(",").map((v) => v.trim()).filter(Boolean),
    });
    const jobId = response.data.job_id;
    pollJob(jobId);
  };

  const pollJob = async (jobId: number) => {
    const interval = setInterval(async () => {
      const res = await api.get(`/jobs/${jobId}`);
      setJob(res.data);
      if (res.data.status === "succeeded" || res.data.status === "failed") {
        clearInterval(interval);
      }
    }, 2000);
  };

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-lg font-semibold">Issue Certificate</h2>
      <form onSubmit={submit} className="space-y-3 rounded-lg border border-slate-800 bg-slate-900 p-4">
        <input
          className="w-full rounded bg-slate-800 px-3 py-2"
          placeholder="Common Name (CN)"
          value={commonName}
          onChange={(e) => setCommonName(e.target.value)}
          required
        />
        <input
          className="w-full rounded bg-slate-800 px-3 py-2"
          placeholder="SANs comma separated"
          value={sans}
          onChange={(e) => setSans(e.target.value)}
        />
        <button type="submit" className="rounded bg-emerald-600 px-3 py-2 text-sm">
          Queue Issue Job
        </button>
      </form>
      {job && (
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
          <p>Job #{job.id}</p>
          <p>Status: {job.status}</p>
          {job.error && <p className="text-red-400">Error: {job.error}</p>}
        </div>
      )}
    </div>
  );
}
