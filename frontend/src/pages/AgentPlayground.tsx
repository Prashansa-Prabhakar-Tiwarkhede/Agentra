import { useState } from "react";
import { Send } from "lucide-react";
import { api } from "@/services/api";
import type { ChatResponse } from "@/types";

export default function AgentPlayground() {
  const [merchantId, setMerchantId] = useState("");
  const [message, setMessage] = useState("I need a gift under ₹2000.");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.chat({ merchant_id: merchantId, session_id: sessionId, message });
      setSessionId(res.session_id);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Playground request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="font-display text-2xl mb-1">Agent Playground</h1>
      <p className="text-sm text-muted mb-8">Test your AI agent exactly as a buyer would experience it.</p>

      <input
        className="input mb-4 max-w-md"
        placeholder="Merchant ID"
        value={merchantId}
        onChange={(e) => setMerchantId(e.target.value)}
      />

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <h3 className="text-xs font-mono text-muted uppercase tracking-wide mb-3">Buyer message</h3>
          <textarea className="input min-h-[100px]" value={message} onChange={(e) => setMessage(e.target.value)} />
          <button onClick={run} disabled={loading || !merchantId} className="btn-primary mt-3 flex items-center gap-2 text-sm">
            <Send size={14} /> {loading ? "Running…" : "Run agent"}
          </button>
          {error && <p className="text-danger text-sm font-mono mt-3">{error}</p>}
        </div>

        <div className="card p-5">
          <h3 className="text-xs font-mono text-muted uppercase tracking-wide mb-3">Decision trace</h3>
          {!result && <p className="text-muted text-sm">Run the agent to see its reasoning, tool calls, and policy decisions.</p>}
          {result && (
            <div className="space-y-4 text-sm">
              <div>
                <span className="font-mono text-xs text-amber-dim">REPLY</span>
                <p className="text-ink/80 mt-1">{result.reply}</p>
              </div>
              {result.structured_action && (
                <div className="ledger-rule pt-4">
                  <span className="font-mono text-xs text-amber-dim">STRUCTURED ACTION</span>
                  <pre className="text-xs font-mono text-ink/70 mt-1 whitespace-pre-wrap">
                    {JSON.stringify(result.structured_action, null, 2)}
                  </pre>
                </div>
              )}
              <div className="ledger-rule pt-4">
                <span className="font-mono text-xs text-amber-dim">CANDIDATES RETURNED</span>
                <p className="text-ink/70 mt-1">{result.products.length} products from catalog search</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
