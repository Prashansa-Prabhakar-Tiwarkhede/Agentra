import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Check } from "lucide-react";
import { api } from "@/services/api";
import { supabase } from "@/services/supabase";

const STEPS = ["Business", "Commerce", "AI Agent", "Safety Policies"];

interface FormState {
  business_name: string;
  description: string;
  category: string;
  currency: string;
  store_description: string;
  contact_email: string;
  agent_name: string;
  personality: string;
  upselling_enabled: boolean;
  max_transaction_amount: number;
  approval_threshold: number;
  max_automatic_retries: number;
  max_discount_percent: number;
  max_upsell_amount: number;
}

const initialState: FormState = {
  business_name: "",
  description: "",
  category: "Gifts",
  currency: "INR",
  store_description: "",
  contact_email: "",
  agent_name: "Aura",
  personality: "friendly, concise, helpful",
  upselling_enabled: true,
  max_transaction_amount: 2000,
  approval_threshold: 1000,
  max_automatic_retries: 1,
  max_discount_percent: 10,
  max_upsell_amount: 200,
};

export default function Onboarding() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>(initialState);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) navigate("/login");
    });
  }, [navigate]);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function finish() {
    setSubmitting(true);
    setError(null);
    try {
      await api.createMerchant({
        business_name: form.business_name,
        description: form.description,
        category: form.category,
        currency: form.currency,
        store_description: form.store_description,
        contact_email: form.contact_email,
      });
      await api.updatePolicy({
        max_transaction_amount: form.max_transaction_amount,
        approval_threshold: form.approval_threshold,
        max_automatic_retries: form.max_automatic_retries,
        max_discount_percent: form.max_discount_percent,
        max_upsell_amount: form.max_upsell_amount,
      });
      await api.completeOnboarding();
      navigate("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong finishing setup. You need to be signed in.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-base flex flex-col items-center px-6 py-16">
      <div className="w-full max-w-lg">
        <div className="flex items-center gap-2 mb-10">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center gap-2 flex-1">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono shrink-0 ${
                i < step ? "bg-amber text-base" : i === step ? "border border-amber text-amber" : "border border-border text-muted"
              }`}>
                {i < step ? <Check size={14} /> : i + 1}
              </div>
              {i < STEPS.length - 1 && <div className={`h-px flex-1 ${i < step ? "bg-amber-dim" : "bg-border"}`} />}
            </div>
          ))}
        </div>

        <h1 className="font-display text-2xl mb-1">{STEPS[step]}</h1>
        <p className="text-sm text-muted mb-8">Step {step + 1} of {STEPS.length}</p>

        <div className="card p-6 space-y-4">
          {step === 0 && (
            <>
              <Field label="Business name">
                <input className="input" value={form.business_name} onChange={(e) => update("business_name", e.target.value)} placeholder="AURA Demo Store" />
              </Field>
              <Field label="Category">
                <input className="input" value={form.category} onChange={(e) => update("category", e.target.value)} placeholder="Gifts" />
              </Field>
              <Field label="Description">
                <textarea className="input min-h-[80px]" value={form.description} onChange={(e) => update("description", e.target.value)} placeholder="What does your store sell?" />
              </Field>
            </>
          )}

          {step === 1 && (
            <>
              <Field label="Currency">
                <input className="input" value={form.currency} onChange={(e) => update("currency", e.target.value)} />
              </Field>
              <Field label="Store description">
                <textarea className="input min-h-[80px]" value={form.store_description} onChange={(e) => update("store_description", e.target.value)} />
              </Field>
              <Field label="Contact email">
                <input className="input" value={form.contact_email} onChange={(e) => update("contact_email", e.target.value)} placeholder="you@store.com" />
              </Field>
            </>
          )}

          {step === 2 && (
            <>
              <Field label="Agent name">
                <input className="input" value={form.agent_name} onChange={(e) => update("agent_name", e.target.value)} />
              </Field>
              <Field label="Agent personality">
                <input className="input" value={form.personality} onChange={(e) => update("personality", e.target.value)} />
              </Field>
              <label className="flex items-center gap-2 text-sm text-ink/80 pt-2">
                <input type="checkbox" checked={form.upselling_enabled} onChange={(e) => update("upselling_enabled", e.target.checked)} className="accent-amber" />
                Enable upselling
              </label>
            </>
          )}

          {step === 3 && (
            <>
              <Field label="Maximum transaction amount (₹)">
                <input type="number" className="input" value={form.max_transaction_amount} onChange={(e) => update("max_transaction_amount", Number(e.target.value))} />
              </Field>
              <Field label="Approval threshold (₹)">
                <input type="number" className="input" value={form.approval_threshold} onChange={(e) => update("approval_threshold", Number(e.target.value))} />
              </Field>
              <Field label="Maximum automatic retries">
                <input type="number" className="input" value={form.max_automatic_retries} onChange={(e) => update("max_automatic_retries", Number(e.target.value))} />
              </Field>
              <Field label="Maximum discount (%)">
                <input type="number" className="input" value={form.max_discount_percent} onChange={(e) => update("max_discount_percent", Number(e.target.value))} />
              </Field>
              <Field label="Maximum upsell amount (₹)">
                <input type="number" className="input" value={form.max_upsell_amount} onChange={(e) => update("max_upsell_amount", Number(e.target.value))} />
              </Field>
            </>
          )}
        </div>

        {error && <p className="text-danger text-sm font-mono mt-4">{error}</p>}

        <div className="flex justify-between mt-8">
          <button onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0} className="btn-ghost disabled:opacity-30">Back</button>
          {step < STEPS.length - 1 ? (
            <button onClick={() => setStep((s) => s + 1)} className="btn-primary">Continue</button>
          ) : (
            <button onClick={finish} disabled={submitting} className="btn-primary">{submitting ? "Setting up…" : "Launch AI Agent"}</button>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-mono text-muted uppercase tracking-wide mb-1.5 block">{label}</span>
      {children}
    </label>
  );
}
