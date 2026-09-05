import { Link } from "react-router-dom";
import { ArrowRight, ShieldCheck, Sparkles, ScrollText, BarChart3, Lock } from "lucide-react";

const LEDGER_PREVIEW = [
  { t: "09:42:12", type: "PRODUCT_SEARCH", detail: "Buyer requested birthday gift under ₹1500.", decision: null },
  { t: "09:42:16", type: "PRODUCT_RECOMMENDED", detail: "Premium Gift Box matches occasion + budget.", decision: null },
  { t: "09:42:48", type: "POLICY_CHECK", detail: "Total ₹1448 within all guardrails.", decision: "ALLOWED" as const },
  { t: "09:43:20", type: "ORDER_CREATED", detail: "Order confirmed, payment captured.", decision: null },
];

function DecisionPill({ decision }: { decision: "ALLOWED" | "BLOCKED" | "REQUIRES_APPROVAL" | null }) {
  if (!decision) return null;
  const cls = decision === "ALLOWED" ? "pill-allowed" : decision === "BLOCKED" ? "pill-blocked" : "pill-approval";
  return <span className={cls}>{decision}</span>;
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-base">
      {/* Nav */}
      <nav className="max-w-6xl mx-auto flex items-center justify-between px-6 py-6">
        <div className="font-display text-xl tracking-tight">AURA <span className="text-amber">Commerce</span></div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="text-sm text-muted hover:text-ink transition-colors">Merchant Login</Link>
          <Link to="/onboarding" className="btn-primary text-sm">Start Building</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-24 grid lg:grid-cols-2 gap-16 items-center">
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-mono text-amber-dim border border-amber-dim/30 rounded-full px-3 py-1 mb-8">
            <Sparkles size={12} /> Razorpay Agentic Commerce Track
          </div>
          <h1 className="font-display text-5xl lg:text-6xl leading-[1.05] tracking-tight">
            Commerce built for the <span className="italic text-amber">age of AI buyers.</span>
          </h1>
          <p className="mt-6 text-lg text-muted max-w-md leading-relaxed">
            Turn your catalog into an intelligent, transactable storefront for autonomous AI agents —
            every recommendation explainable, every rupee gated and audited.
          </p>
          <div className="mt-10 flex items-center gap-4">
            <Link to="/onboarding" className="btn-primary inline-flex items-center gap-2">
              Start Building <ArrowRight size={16} />
            </Link>
            <Link to="/demo" className="btn-ghost">See AI Buyer Demo</Link>
          </div>
        </div>

        {/* Signature element: the ledger */}
        <div className="card p-6 shadow-glow">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-mono text-muted tracking-widest uppercase">Live Audit Ledger</span>
            <span className="flex items-center gap-1.5 text-xs font-mono text-success">
              <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" /> session active
            </span>
          </div>
          <div className="space-y-0">
            {LEDGER_PREVIEW.map((row, i) => (
              <div key={i} className={`py-3 flex items-start justify-between gap-4 ${i > 0 ? "ledger-rule" : ""}`}>
                <div className="flex gap-4">
                  <span className="font-mono text-xs text-muted pt-0.5 shrink-0">{row.t}</span>
                  <div>
                    <div className="font-mono text-xs text-amber-dim">{row.type}</div>
                    <div className="text-sm text-ink/80 mt-0.5">{row.detail}</div>
                  </div>
                </div>
                <DecisionPill decision={row.decision} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-6xl mx-auto px-6 py-20 ledger-rule">
        <h2 className="font-display text-3xl mb-12">How it works</h2>
        <div className="grid md:grid-cols-4 gap-8">
          {[
            { icon: Sparkles, title: "AI Buyer", body: "Natural-language shopping, product discovery, and intelligent upselling." },
            { icon: ShieldCheck, title: "Merchant Agent", body: "Recommends and explains — never executes a payment directly." },
            { icon: Lock, title: "Guardrails", body: "A deterministic policy engine gates every transaction before money moves." },
            { icon: ScrollText, title: "Auditability", body: "Every AI and financial action is logged, explainable, and reviewable." },
          ].map(({ icon: Icon, title, body }) => (
            <div key={title}>
              <Icon size={20} className="text-amber mb-4" />
              <h3 className="font-display text-lg mb-2">{title}</h3>
              <p className="text-sm text-muted leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Razorpay + Analytics */}
      <section className="max-w-6xl mx-auto px-6 py-20 ledger-rule grid md:grid-cols-2 gap-12">
        <div className="card p-8">
          <ShieldCheck size={20} className="text-amber mb-4" />
          <h3 className="font-display text-xl mb-2">Razorpay-powered test commerce</h3>
          <p className="text-sm text-muted leading-relaxed">
            Every AI-initiated purchase settles through Razorpay TEST MODE — idempotency-keyed,
            retry-bounded, and never trusting the frontend for financial state.
          </p>
        </div>
        <div className="card p-8">
          <BarChart3 size={20} className="text-amber mb-4" />
          <h3 className="font-display text-xl mb-2">Analytics that explain themselves</h3>
          <p className="text-sm text-muted leading-relaxed">
            AI-driven GMV, conversion funnels, and upsell revenue — with clearly labeled
            synthetic data whenever you're in demo mode.
          </p>
        </div>
      </section>

      <footer className="max-w-6xl mx-auto px-6 py-12 text-xs text-muted font-mono">
        AURA Commerce — hackathon build, Razorpay TEST MODE only. No real payments are ever processed.
      </footer>
    </div>
  );
}
