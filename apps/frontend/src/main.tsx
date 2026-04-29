import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import "./index.css";
import { initAuth } from "./lib/auth";
import Certificates from "./pages/Certificates";
import Dashboard from "./pages/Dashboard";
import IssueCertificate from "./pages/IssueCertificate";
import CaHealth from "./pages/CaHealth";
import AuditLogs from "./pages/AuditLogs";
import Users from "./pages/Users";
import Settings from "./pages/Settings";
import IdentitySync from "./pages/IdentitySync";
import CaSetup from "./pages/CaSetup";
import Provisioners from "./pages/Provisioners";
import Acme from "./pages/Acme";

const queryClient = new QueryClient();

async function bootstrap() {
  await initAuth();
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <div className="min-h-screen bg-slate-950 text-slate-100">
            <nav className="border-b border-slate-800 bg-slate-900 px-6 py-3 space-x-6">
              <Link to="/">Dashboard</Link>
              <Link to="/certificates">Certificates</Link>
              <Link to="/issue">Issue</Link>
              <Link to="/ca-setup">CA Setup</Link>
              <Link to="/provisioners">Provisioners</Link>
              <Link to="/acme">ACME</Link>
              <Link to="/identity-sync">Identity Sync</Link>
              <Link to="/ca-health">CA Health</Link>
              <Link to="/audit-logs">Audit Logs</Link>
              <Link to="/admin-users">Users</Link>
              <Link to="/settings">Settings</Link>
            </nav>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/certificates" element={<Certificates />} />
              <Route path="/issue" element={<IssueCertificate />} />
              <Route path="/ca-setup" element={<CaSetup />} />
              <Route path="/provisioners" element={<Provisioners />} />
              <Route path="/acme" element={<Acme />} />
              <Route path="/identity-sync" element={<IdentitySync />} />
              <Route path="/ca-health" element={<CaHealth />} />
              <Route path="/audit-logs" element={<AuditLogs />} />
              <Route path="/admin-users" element={<Users />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </div>
        </BrowserRouter>
      </QueryClientProvider>
    </React.StrictMode>
  );
}

bootstrap();
