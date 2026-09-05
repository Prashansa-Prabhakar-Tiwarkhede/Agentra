import { useState, useRef, useEffect } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { Send, ShieldCheck, PackageCheck, Loader2, CreditCard, X, CheckCircle2 } from "lucide-react";
import { api } from "@/services/api";
import { useRazorpayCheckout } from "@/hooks/useRazorpayCheckout";
import type { ChatResponse, CheckoutIntent, ChatProduct } from "@/types";

interface Turn {
  role: "buyer" | "agent";
  content: string;
  products?: ChatProduct[];
  recommendedId?: string | null;
}

export default function BuyerChat() {
  const { merchantId = "" } = useParams();
  const [searchParams] = useSearchParams();
  const prefillPrompt = searchParams.get("prompt");
  const [turns, setTurns] = useState<Turn[]>([
    {
      role: "agent",
      content: "Hi! I'm your AI shopping assistant. Tell me what you're looking for — an occasion, a budget, anything.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [cart, setCart] = useState<ChatProduct[]>([]);
  const [intent, setIntent] = useState<CheckoutIntent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [paymentStatus, setPaymentStatus] = useState<"idle" | "processing" | "success" | "failed">("idle");
  const { startCheckout } = useRazorpayCheckout();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, intent]);

  useEffect(() => {
    if (prefillPrompt) setInput(prefillPrompt);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function sendMessage() {
    if (!input.trim() || loading) return;
    const message = input.trim();
    setInput("");
    setError(null);
    setTurns((t) => [...t, { role: "buyer", content: message }]);
    setLoading(true);
    try {
      const res: ChatResponse = await api.chat({ merchant_id: merchantId, session_id: sessionId, message });
      setSessionId(res.session_id);
      setTurns((t) => [
        ...t,
        { role: "agent", content: res.reply, products: res.products, recommendedId: res.structured_action?.product_id ?? null },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function addToCart(p: ChatProduct) {
    if (cart.find((c) => c.product_id === p.product_id)) return;
    setCart((c) => [...c, p]);
  }

  function removeFromCart(productId: string) {
    setCart((c) => c.filter((p) => p.product_id !== productId));
  }

  async function proceedToCheckout() {
    if (!cart.length) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.createCheckoutIntent({
        merchant_id: merchantId,
        session_id: sessionId,
        line_items: cart.map((p) => ({ product_id: p.product_id, name: p.name, price: p.price, qty: 1 })),
      });
      setIntent(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Checkout failed.");
    } finally {
      setLoading(false);
    }
  }

  async function approve(approveIt: boolean) {
    if (!intent) return;
    setLoading(true);
    try {
      const res = await api.approveCheckout(intent.id, approveIt);
      setIntent(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approval failed.");
    } finally {
      setLoading(false);
    }
  }

  async function payNow() {
    if (!intent) return;
    setPaymentStatus("processing");
    setError(null);
    startCheckout(intent.id, {
      businessName: "AURA Demo Store",
      onSuccess: () => setPaymentStatus("success"),
      onFailure: (reason) => {
        setPaymentStatus("failed");
        setError(reason);
      },
    });
  }

  return (
    <div className="min-h-screen bg-base flex flex-col">
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="font-display text-lg">AURA <span className="text-amber">Assistant</span></div>
        <div className="text-xs font-mono text-muted flex items-center gap-1.5">
          <ShieldCheck size={14} className="text-amber" /> guardrails active
        </div>
      </header>

      <div className="flex-1 max-w-2xl w-full mx-auto px-6 py-8 flex flex-col gap-5">
        {turns.map((turn, i) => (
          <div key={i} className={`flex ${turn.role === "buyer" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-md rounded-2xl px-4 py-3 ${
              turn.role === "buyer" ? "bg-amber text-base" : "card"
            }`}>
              <p className="text-sm leading-relaxed">{turn.content}</p>
              {turn.products && turn.products.length > 0 && (
                <div className="mt-3 space-y-2">
                  {turn.products.map((p) => (
                    <div
                      key={p.product_id}
                      className={`flex items-center justify-between gap-3 rounded-xl border px-3 py-2 ${
                        p.product_id === turn.recommendedId ? "border-amber/50 bg-amber/5" : "border-border"
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        {p.image_url && (
                          <img
                            src={p.image_url}
                            alt={p.name}
                            className="w-10 h-10 rounded-lg object-cover border border-border shrink-0"
                            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                          />
                        )}
                        <div className="min-w-0">
                          <div className="text-sm font-medium truncate">{p.name}</div>
                          <div className="text-xs font-mono text-muted">
                            ₹{p.price.toFixed(0)} · {p.in_stock ? "in stock" : "out of stock"}
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => addToCart(p)}
                        disabled={!p.in_stock}
                        className="text-xs font-mono text-amber border border-amber-dim/40 rounded-full px-3 py-1.5 hover:bg-amber/10 disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
                      >
                        Add
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && !intent && (
          <div className="flex justify-start">
            <div className="card px-4 py-3 flex items-center gap-2 text-muted text-sm">
              <Loader2 size={14} className="animate-spin" /> thinking…
            </div>
          </div>
        )}
        {error && <div className="text-danger text-sm font-mono">{error}</div>}
        <div ref={bottomRef} />
      </div>

      {/* Cart / checkout strip */}
      {cart.length > 0 && !intent && (
        <div className="border-t border-border bg-panel px-6 py-4">
          <div className="max-w-2xl mx-auto">
            <div className="space-y-1.5 mb-3">
              {cart.map((p) => (
                <div key={p.product_id} className="flex items-center justify-between text-sm">
                  <span className="text-ink/80">{p.name}</span>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-muted">₹{p.price.toFixed(0)}</span>
                    <button
                      onClick={() => removeFromCart(p.product_id)}
                      className="text-muted hover:text-danger transition-colors text-xs"
                      aria-label={`Remove ${p.name}`}
                    >
                      <X size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between ledger-rule pt-3">
              <div className="text-sm font-mono">
                Total ₹{cart.reduce((s, p) => s + p.price, 0).toFixed(0)}
              </div>
              <button onClick={proceedToCheckout} disabled={loading} className="btn-primary text-sm flex items-center gap-2">
                <PackageCheck size={16} /> Review checkout
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Approval / policy decision panel */}
      {intent && (
        <div className="border-t border-border bg-panel px-6 py-5">
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono text-muted uppercase tracking-widest">Checkout total</span>
              <span className="font-mono text-lg text-ink">₹{intent.total.toFixed(0)}</span>
            </div>
            <div className="ledger-rule pt-3 flex items-start justify-between gap-4">
              <p className="text-sm text-muted leading-relaxed">{intent.policy_reason}</p>
              <span className={
                intent.policy_decision === "ALLOWED" ? "pill-allowed" :
                intent.policy_decision === "BLOCKED" ? "pill-blocked" : "pill-approval"
              }>{intent.policy_decision}</span>
            </div>

            {intent.requires_approval && intent.buyer_approved === null && (
              <div className="mt-4 flex gap-3">
                <button onClick={() => approve(true)} disabled={loading} className="btn-primary flex-1">Approve Purchase</button>
                <button onClick={() => approve(false)} disabled={loading} className="btn-ghost flex-1">Cancel</button>
              </div>
            )}

            {intent.policy_decision === "ALLOWED" && intent.buyer_approved && paymentStatus === "idle" && (
              <button onClick={payNow} className="btn-primary mt-4 w-full flex items-center justify-center gap-2">
                <CreditCard size={16} /> Pay with Razorpay (Test Mode)
              </button>
            )}
            {paymentStatus === "processing" && (
              <div className="mt-4 text-sm text-muted font-mono flex items-center gap-2">
                <Loader2 size={14} className="animate-spin" /> waiting for payment…
              </div>
            )}
            {paymentStatus === "success" && (
              <div className="mt-4 rounded-xl border border-success/30 bg-success/5 p-4">
                <div className="flex items-center gap-2 text-success text-sm font-medium mb-3">
                  <CheckCircle2 size={16} /> Order confirmed
                </div>
                <div className="space-y-1.5 mb-3">
                  {cart.map((p) => (
                    <div key={p.product_id} className="flex items-center justify-between text-xs">
                      <span className="text-ink/70">{p.name}</span>
                      <span className="font-mono text-muted">₹{p.price.toFixed(0)}</span>
                    </div>
                  ))}
                </div>
                <div className="ledger-rule pt-2 flex items-center justify-between text-sm">
                  <span className="text-ink/80">Total paid</span>
                  <span className="font-mono text-success">₹{intent.total.toFixed(0)}</span>
                </div>
                <div className="text-xs font-mono text-muted mt-2">Order ID: {intent.id.slice(0, 8)}</div>
              </div>
            )}
            {paymentStatus === "failed" && error && (
              <div className="mt-4 text-sm text-danger font-mono">{error}</div>
            )}

            {intent.policy_decision === "BLOCKED" && (
              <div className="mt-4 text-sm text-danger font-mono">
                This purchase can't proceed — try a smaller cart or a different item.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Composer */}
      <div className="border-t border-border px-6 py-4">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="I need a birthday gift for my friend under ₹1500…"
            className="flex-1 bg-panel border border-border rounded-full px-5 py-3 text-sm outline-none focus:border-amber-dim transition-colors"
          />
          <button onClick={sendMessage} disabled={loading} className="bg-amber text-base rounded-full p-3 hover:bg-amber-glow transition-colors disabled:opacity-50">
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
