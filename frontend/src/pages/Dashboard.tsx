import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, PieChart, Pie, Cell } from "recharts";
import { TrendingUp, ShoppingBag, Percent, Wallet, Link as LinkIcon, Check } from "lucide-react";
import { useState } from "react";
import { api } from "@/services/api";

function StatCard({ icon: Icon, label, value, sub }: { icon: any; label: string; value: string; sub?: string }) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-mono text-muted uppercase tracking-wide">{label}</span>
        <Icon size={16} className="text-amber-dim" />
      </div>
      <div className="font-display text-2xl">{value}</div>
      {sub && <div className="text-xs text-muted mt-1">{sub}</div>}
    </div>
  );
}

function StorefrontLink() {
  const { data: merchant } = useQuery({ queryKey: ["me"], queryFn: api.getMe });
  const [copied, setCopied] = useState(false);
  if (!merchant) return null;
  const link = `${window.location.origin}/buyer/${merchant.id}`;

  function copy() {
    navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="card p-4 flex items-center justify-between gap-4 mb-6">
      <div className="flex items-center gap-2 min-w-0">
        <LinkIcon size={14} className="text-amber shrink-0" />
        <span className="text-xs font-mono text-muted truncate">{link}</span>
      </div>
      <button onClick={copy} className="text-xs font-mono text-amber border border-amber-dim/40 rounded-full px-3 py-1.5 hover:bg-amber/10 shrink-0 flex items-center gap-1.5">
        {copied ? <><Check size={12} /> Copied</> : "Copy storefront link"}
      </button>
    </div>
  );
}

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({ queryKey: ["analytics-summary"], queryFn: api.analyticsSummary });
  const { data: revenue } = useQuery({ queryKey: ["revenue-timeseries"], queryFn: api.revenueTimeseries });
  const { data: products } = useQuery({ queryKey: ["product-performance"], queryFn: api.productPerformance });

  const funnelData = data ? [
    { name: "Sessions", value: data.agent_sessions },
    { name: "Orders", value: data.ai_orders },
  ] : [];

  return (
    <div>
      <h1 className="font-display text-2xl mb-1">Overview</h1>
      <p className="text-sm text-muted mb-6">AI-driven commerce, at a glance.</p>

      <StorefrontLink />

      {isLoading && <p className="text-muted text-sm">Loading metrics…</p>}
      {error && <p className="text-danger text-sm font-mono">Couldn't load analytics — sign in as a merchant to see live data.</p>}

      {data && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard icon={Wallet} label="AI GMV" value={`₹${data.ai_gmv.toLocaleString("en-IN")}`} sub={`${data.ai_orders} orders`} />
            <StatCard icon={TrendingUp} label="Conversion" value={`${data.conversion_rate_percent}%`} sub={`${data.agent_sessions} sessions`} />
            <StatCard icon={ShoppingBag} label="Avg Order Value" value={`₹${data.average_order_value.toLocaleString("en-IN")}`} />
            <StatCard icon={Percent} label="Upsells / Cross-sells" value={`${data.upsells_suggested} / ${data.cross_sells_suggested}`} />
          </div>

          <div className="grid lg:grid-cols-2 gap-6 mb-6">
            <div className="card p-6">
              <h3 className="text-sm font-mono text-muted uppercase tracking-wide mb-4">Revenue Over Time</h3>
              {revenue && revenue.length > 0 ? (
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={revenue}>
                      <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#8B8D93" }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 10, fill: "#8B8D93" }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ background: "#151821", border: "1px solid #272B36", borderRadius: 8, fontSize: 12 }} />
                      <Bar dataKey="revenue" fill="#E8B454" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-muted text-sm">No paid orders yet — revenue will chart here once you have some.</p>
              )}
            </div>

            <div className="card p-6">
              <h3 className="text-sm font-mono text-muted uppercase tracking-wide mb-4">Session → Order Funnel</h3>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={funnelData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={4}>
                      <Cell fill="#E8B454" />
                      <Cell fill="#272B36" />
                    </Pie>
                    <Tooltip contentStyle={{ background: "#151821", border: "1px solid #272B36", borderRadius: 8, fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="card p-6 mb-6">
            <h3 className="text-sm font-mono text-muted uppercase tracking-wide mb-4">Product Performance</h3>
            {products && products.length > 0 ? (
              <div className="space-y-2">
                {products.slice(0, 6).map((p) => (
                  <div key={p.name} className="flex items-center justify-between text-sm ledger-rule pt-2 first:pt-0 first:border-t-0">
                    <span className="text-ink/80">{p.name}</span>
                    <span className="font-mono text-xs text-muted">{p.units_sold} sold · ₹{p.revenue.toFixed(0)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted text-sm">No paid orders yet.</p>
            )}
          </div>

          <div className="card p-6">
            <h3 className="text-sm font-mono text-muted uppercase tracking-wide mb-4">Payments</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink/80">Successful</span>
                <span className="pill-allowed">{data.successful_payments}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink/80">Failed</span>
                <span className="pill-blocked">{data.failed_payments}</span>
              </div>
            </div>
          </div>

          <p className="text-xs text-muted font-mono mt-6">{data.note}</p>
        </>
      )}
    </div>
  );
}
