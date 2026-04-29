import { FormEvent, useState } from "react";
import api from "../lib/api";

type ScimUser = { id: string; userName: string; active: boolean };
type ScimGroup = { id: string; displayName: string };

export default function IdentitySync() {
  const [token, setToken] = useState("dev-scim-token");
  const [users, setUsers] = useState<ScimUser[]>([]);
  const [groups, setGroups] = useState<ScimGroup[]>([]);
  const [newUserName, setNewUserName] = useState("");
  const [newGroupName, setNewGroupName] = useState("");
  const [message, setMessage] = useState("");

  const scim = api.create({
    baseURL: (import.meta.env.VITE_API_URL || "http://localhost:8000/api").replace("/api", "/scim/v2"),
    headers: { Authorization: `Bearer ${token}` },
  });

  const refresh = async () => {
    const [u, g] = await Promise.all([scim.get("/Users"), scim.get("/Groups")]);
    setUsers(u.data.Resources || []);
    setGroups(g.data.Resources || []);
  };

  const createUser = async (e: FormEvent) => {
    e.preventDefault();
    await scim.post("/Users", { userName: newUserName, active: true });
    setNewUserName("");
    setMessage("SCIM user created");
    await refresh();
  };

  const createGroup = async (e: FormEvent) => {
    e.preventDefault();
    await scim.post("/Groups", { displayName: newGroupName });
    setNewGroupName("");
    setMessage("SCIM group created");
    await refresh();
  };

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-lg font-semibold">Identity Sync (SCIM)</h2>
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-3">
        <label className="block text-sm text-slate-300">SCIM Bearer Token</label>
        <input
          className="w-full rounded bg-slate-800 px-3 py-2"
          value={token}
          onChange={(e) => setToken(e.target.value)}
        />
        <button className="rounded bg-indigo-600 px-3 py-2 text-sm" onClick={refresh}>
          Refresh SCIM Data
        </button>
      </div>
      {message && <p className="text-emerald-400 text-sm">{message}</p>}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <form onSubmit={createUser} className="rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-2">
          <h3 className="font-medium">Create User</h3>
          <input
            className="w-full rounded bg-slate-800 px-3 py-2"
            placeholder="userName"
            value={newUserName}
            onChange={(e) => setNewUserName(e.target.value)}
            required
          />
          <button type="submit" className="rounded bg-emerald-600 px-3 py-2 text-sm">
            Create SCIM User
          </button>
          <ul className="mt-3 text-sm text-slate-300 space-y-1">
            {users.map((u) => (
              <li key={u.id}>
                {u.userName} ({u.active ? "active" : "inactive"})
              </li>
            ))}
          </ul>
        </form>
        <form onSubmit={createGroup} className="rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-2">
          <h3 className="font-medium">Create Group</h3>
          <input
            className="w-full rounded bg-slate-800 px-3 py-2"
            placeholder="displayName"
            value={newGroupName}
            onChange={(e) => setNewGroupName(e.target.value)}
            required
          />
          <button type="submit" className="rounded bg-blue-600 px-3 py-2 text-sm">
            Create SCIM Group
          </button>
          <ul className="mt-3 text-sm text-slate-300 space-y-1">
            {groups.map((g) => (
              <li key={g.id}>{g.displayName}</li>
            ))}
          </ul>
        </form>
      </div>
    </div>
  );
}
