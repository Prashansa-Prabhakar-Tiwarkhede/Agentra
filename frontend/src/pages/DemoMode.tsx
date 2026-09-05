import { useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, XCircle, ShieldAlert, Clock3, ArrowRight } from "lucide-react";

const SCENARIOS = [
  {
    key: "success",
    title: "Run successful purchase",
    icon: CheckCircle2,
    color: "text-success",
    description: "Birthday gift under ₹1500 → recommendation → upsell → policy ALLOWED → Razorpay test payment → order.",
    prompt: "I need a birthday gift for my friend under ₹1500.",
  },
  {
    key: "approval",
    title: "Run approval-required transaction",
    icon: Clock3,
    color: "text-amber",
    description: "A cart above the approval threshold → REQUIRES_APPROVAL → buyer approves → payment proceeds.",
    prompt: "I want the luxury chocolate hamper and the wireless earbuds together.",
  },
  {
    key: "blocked",
    title: "Run blocked transaction",
    icon: ShieldAlert,
    color: "text-danger",
    description: "A cart exceeding the merchant's hard transaction cap → BLOCKED, no payment attempted.",
    prompt: "I want two mechanical keyboards.",
  },
  {
    key: "failure",
    title: "Run payment failure",
    icon: XCircle,
    color: "text-danger",
    description: "A simulated Razorpay decline → retry policy checked → duplicate payment prevented → explained.",
    prompt: "I want the analog wrist watch.",
  },
];

export default function DemoMode() {
  const [merchantId, setMerchantId] = useState("");

  return (
    <div className="min-h-screen bg-base px-6 py-16">
      <div className="max-w-3xl mx-auto">
        <div className="font-display text-2xl mb-2">Launch Demo</div>
        <p className="text-sm text-muted mb-8">
          Preloaded demo merchant with 30+ products, policies, and sample orders. Pick a scenario —
          each opens the buyer chat with a scripted prompt that exercises a different guardrail path.
        </p>

        <input
          className="input mb-8 max-w-md"
          placeholder="Demo merchant ID (from `python3 database/seed.py`)"
          value={merchantId}
          onChange={(e) => setMerchantId(e.target.value)}
        />

        <div className="grid md:grid-cols-2 gap-4">
          {SCENARIOS.map(({ key, title, icon: Icon, color, description, prompt }) => (
            <div key={key} className="card p-5">
              <Icon size={18} className={`${color} mb-3`} />
              <h3 className="font-display text-base mb-1.5">{title}</h3>
              <p className="text-xs text-muted leading-relaxed mb-4">{description}</p>
              <Link
                to={merchantId ? `/buyer/${merchantId}?prompt=${encodeURIComponent(prompt)}` : "#"}
                className={`text-xs font-mono flex items-center gap-1.5 ${
                  merchantId ? "text-amber hover:gap-2.5 transition-all" : "text-muted/40 pointer-events-none"
                }`}
              >
                Open scenario <ArrowRight size={12} />
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
