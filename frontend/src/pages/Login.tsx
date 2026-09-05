import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/services/supabase";
import { api } from "@/services/api";

export default function Login() {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) routeAfterLogin();
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function routeAfterLogin() {
    try {
      const merchant = await api.getMe();
      navigate(merchant.onboarding_complete ? "/dashboard" : "/onboarding");
    } catch {
      // No merchant profile yet for this account — send to onboarding to create one.
      navigate("/onboarding");
    }
  }

  async function submit() {
    setLoading(true);
    setError(null);
    setInfo(null);
    try {
      if (mode === "signup") {
        const { error: signUpError } = await supabase.auth.signUp({ email, password });
        if (signUpError) throw signUpError;
        setInfo("Account created. If email confirmation is enabled on your Supabase project, check your inbox — otherwise you're signed in already.");
        const { data } = await supabase.auth.getSession();
        if (data.session) await routeAfterLogin();
      } else {
        const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
        if (signInError) throw signInError;
        await routeAfterLogin();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <div className="font-display text-xl mb-1 text-center">
          AURA <span className="text-amber">Commerce</span>
        </div>
        <p className="text-sm text-muted text-center mb-8">
          {mode === "signin" ? "Sign in to your merchant dashboard." : "Create a merchant account."}
        </p>

        <div className="card p-6 space-y-4">
          <label className="block">
            <span className="text-xs font-mono text-muted uppercase tracking-wide mb-1.5 block">Email</span>
            <input
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@store.com"
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </label>
          <label className="block">
            <span className="text-xs font-mono text-muted uppercase tracking-wide mb-1.5 block">Password</span>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </label>

          {error && <p className="text-danger text-xs font-mono">{error}</p>}
          {info && <p className="text-success text-xs font-mono">{info}</p>}

          <button onClick={submit} disabled={loading || !email || !password} className="btn-primary w-full">
            {loading ? "Please wait…" : mode === "signin" ? "Sign in" : "Create account"}
          </button>
        </div>

        <p className="text-center text-sm text-muted mt-6">
          {mode === "signin" ? "New merchant?" : "Already have an account?"}{" "}
          <button
            onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
            className="text-amber hover:underline"
          >
            {mode === "signin" ? "Create an account" : "Sign in"}
          </button>
        </p>
      </div>
    </div>
  );
}
