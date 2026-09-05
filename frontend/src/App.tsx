import { Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import BuyerChat from "./pages/BuyerChat";
import Onboarding from "./pages/Onboarding";
import DemoMode from "./pages/DemoMode";
import Dashboard from "./pages/Dashboard";
import Catalog from "./pages/Catalog";
import Orders from "./pages/Orders";
import AuditTrail from "./pages/AuditTrail";
import PolicySettings from "./pages/PolicySettings";
import AgentPlayground from "./pages/AgentPlayground";
import DashboardLayout from "./layouts/DashboardLayout";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/buyer/:merchantId" element={<BuyerChat />} />
      <Route path="/demo" element={<DemoMode />} />
      <Route path="/onboarding" element={<Onboarding />} />

      <Route element={<DashboardLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/dashboard/catalog" element={<Catalog />} />
        <Route path="/dashboard/orders" element={<Orders />} />
        <Route path="/dashboard/audit" element={<AuditTrail />} />
        <Route path="/dashboard/policy" element={<PolicySettings />} />
        <Route path="/dashboard/playground" element={<AgentPlayground />} />
      </Route>
    </Routes>
  );
}
