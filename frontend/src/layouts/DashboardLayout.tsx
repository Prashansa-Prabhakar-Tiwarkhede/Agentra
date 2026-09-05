import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { LayoutDashboard, Package, ShoppingCart, ScrollText, ShieldCheck, Terminal, LogOut } from "lucide-react";
import { supabase } from "@/services/supabase";

const NAV = [
  { to: "/dashboard", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/dashboard/catalog", label: "Catalog", icon: Package },
  { to: "/dashboard/orders", label: "Orders", icon: ShoppingCart },
  { to: "/dashboard/audit", label: "Audit Trail", icon: ScrollText },
  { to: "/dashboard/policy", label: "Policies", icon: ShieldCheck },
  { to: "/dashboard/playground", label: "Agent Playground", icon: Terminal },
];

export default function DashboardLayout() {
  const navigate = useNavigate();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) navigate("/login");
      else setChecked(true);
    });
  }, [navigate]);

  async function signOut() {
    await supabase.auth.signOut();
    navigate("/login");
  }

  if (!checked) return null;

  return (
    <div className="min-h-screen bg-base flex">
      <aside className="w-60 border-r border-border px-4 py-6 flex flex-col shrink-0">
        <div className="font-display text-lg px-2 mb-8">AURA <span className="text-amber">Commerce</span></div>
        <nav className="space-y-1 flex-1">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive ? "bg-amber/10 text-amber" : "text-muted hover:text-ink hover:bg-panel"
                }`
              }
            >
              <Icon size={16} /> {label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={signOut}
          className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm text-muted hover:text-ink hover:bg-panel transition-colors"
        >
          <LogOut size={16} /> Sign out
        </button>
      </aside>
      <main className="flex-1 px-8 py-8 max-w-6xl">
        <Outlet />
      </main>
    </div>
  );
}
