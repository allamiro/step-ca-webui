import { useEffect, useState } from "react";
import api from "../lib/api";

type User = {
  username: string;
  email?: string;
  roles: string[];
  source: string;
};

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    api.get("/users").then((res) => setUsers(res.data.items || []));
  }, []);

  return (
    <div className="p-6">
      <h2 className="mb-4 text-lg font-semibold">Users</h2>
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-slate-400">
              <th>Username</th>
              <th>Email</th>
              <th>Roles</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.username} className="border-t border-slate-800">
                <td>{user.username}</td>
                <td>{user.email || "-"}</td>
                <td>{user.roles.join(", ")}</td>
                <td>{user.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
