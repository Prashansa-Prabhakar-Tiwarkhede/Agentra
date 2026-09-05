import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import type { AuditEvent } from "@/types";

function decisionPillClass(decision: AuditEvent["policy_decision"]) {
  if (decision === "ALLOWED") return "pill-allowed";
  if (decision === "BLOCKED") return "pill-blocked";
  if (decision === "REQUIRES_APPROVAL") return "pill-approval";
  return null;
}

export default function AuditTrail() {
  const { data: events, isLoading, error } = useQuery({ queryKey: ["audit"], queryFn: () => api.listAudit() });

  return (
    <div>
      <h1 className="font-display text-2xl mb-1">Audit Trail</h1>
      <p className="text-sm text-muted mb-8">Every AI and financial action, timestamped and explainable.</p>

      {error && <p className="text-danger text-sm font-mono">Sign in as a merchant to view the audit trail.</p>}
      {isLoading && <p className="text-muted text-sm">Loading…</p>}

      <div className="card p-6">
        {events?.map((e, i) => (
          <div key={e.id} className={`py-4 flex items-start justify-between gap-6 ${i > 0 ? "ledger-rule" : ""}`}>
            <div className="flex gap-4 min-w-0">
              <span className="font-mono text-xs text-muted pt-0.5 shrink-0 w-20">
                {new Date(e.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
              </span>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-amber-dim">{e.event_type}</span>
                  <span className="text-xs text-muted">· {e.actor}</span>
                </div>
                {e.reason && <p className="text-sm text-ink/80 mt-1">{e.reason}</p>}
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              {e.amount != null && <span className="font-mono text-xs text-muted">₹{e.amount.toFixed(0)}</span>}
              {decisionPillClass(e.policy_decision) && (
                <span className={decisionPillClass(e.policy_decision)!}>{e.policy_decision}</span>
              )}
            </div>
          </div>
        ))}
        {events?.length === 0 && <p className="text-muted text-sm text-center py-8">No events logged yet.</p>}
      </div>
    </div>
  );
}
