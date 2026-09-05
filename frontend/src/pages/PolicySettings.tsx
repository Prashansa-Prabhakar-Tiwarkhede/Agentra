import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import type { PolicyConfig } from "@/types";

const FIELDS: { key: keyof PolicyConfig; label: string; suffix: string }[] = [
  { key: "max_transaction_amount", label: "Maximum transaction amount", suffix: "₹" },
  { key: "approval_threshold", label: "Approval threshold", suffix: "₹" },
  { key: "max_automatic_retries", label: "Maximum automatic retries", suffix: "" },
  { key: "max_discount_percent", label: "Maximum discount", suffix: "%" },
  { key: "max_upsell_amount", label: "Maximum upsell amount", suffix: "₹" },
];

export default function PolicySettings() {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ["policy"], queryFn: api.getPolicy });
  const [form, setForm] = useState<PolicyConfig | null>(null);

  useEffect(() => {
    if (data) setForm(data);
  }, [data]);

  const mutation = useMutation({
    mutationFn: (payload: Partial<PolicyConfig>) => api.updatePolicy(payload),
    onSuccess: (res) => {
      qc.setQueryData(["policy"], res);
      setForm(res);
    },
  });

  return (
    <div>
      <h1 className="font-display text-2xl mb-1">Guardrail Policies</h1>
      <p className="text-sm text-muted mb-8">
        These limits are enforced by a deterministic policy engine, independent of the AI agent.
      </p>

      {error && <p className="text-danger text-sm font-mono">Sign in as a merchant to edit policies.</p>}
      {isLoading && <p className="text-muted text-sm">Loading…</p>}

      {form && (
        <div className="card p-6 max-w-lg space-y-5">
          {FIELDS.map(({ key, label, suffix }) => (
            <label key={key} className="block">
              <span className="text-xs font-mono text-muted uppercase tracking-wide mb-1.5 block">
                {label} {suffix && `(${suffix})`}
              </span>
              <input
                type="number"
                className="input"
                value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: Number(e.target.value) })}
              />
            </label>
          ))}
          <button onClick={() => mutation.mutate(form)} disabled={mutation.isPending} className="btn-primary">
            {mutation.isPending ? "Saving…" : "Save policies"}
          </button>
        </div>
      )}
    </div>
  );
}
