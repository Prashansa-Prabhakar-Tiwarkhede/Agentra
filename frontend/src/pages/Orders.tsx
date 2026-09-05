import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

const STATUS_PILL: Record<string, string> = {
  paid: "pill-allowed",
  failed: "pill-blocked",
  pending: "pill-approval",
};

export default function Orders() {
  const { data: orders, isLoading, error } = useQuery({ queryKey: ["orders"], queryFn: api.listOrders });

  return (
    <div>
      <h1 className="font-display text-2xl mb-1">Orders</h1>
      <p className="text-sm text-muted mb-8">{orders?.length ?? 0} orders across all AI sessions.</p>

      {error && <p className="text-danger text-sm font-mono">Sign in as a merchant to view orders.</p>}
      {isLoading && <p className="text-muted text-sm">Loading…</p>}

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="ledger-rule text-left text-xs font-mono text-muted uppercase tracking-wide">
              <th className="px-5 py-3">Order</th>
              <th className="px-5 py-3">Items</th>
              <th className="px-5 py-3">Amount</th>
              <th className="px-5 py-3">Payment</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3">Source</th>
            </tr>
          </thead>
          <tbody>
            {orders?.map((o) => (
              <tr key={o.id} className="ledger-rule">
                <td className="px-5 py-3 font-mono text-xs text-muted">{o.id.slice(0, 8)}</td>
                <td className="px-5 py-3">{o.line_items.map((li) => li.name).join(", ")}</td>
                <td className="px-5 py-3 font-mono">₹{o.amount.toFixed(0)}</td>
                <td className="px-5 py-3">
                  <span className={STATUS_PILL[o.payment_status] ?? "pill-approval"}>{o.payment_status}</span>
                </td>
                <td className="px-5 py-3 text-muted">{o.order_status}</td>
                <td className="px-5 py-3 text-xs font-mono text-amber-dim">{o.is_ai_generated ? "AI agent" : "manual"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {orders?.length === 0 && <p className="text-muted text-sm px-5 py-8 text-center">No orders yet.</p>}
      </div>
    </div>
  );
}
