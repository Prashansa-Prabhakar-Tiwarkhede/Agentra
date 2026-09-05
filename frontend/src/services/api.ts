import { supabase } from "./supabase";
import type {
  Product, Merchant, PolicyConfig, ChatResponse, CheckoutIntent, Order, AuditEvent, AnalyticsSummary,
  RevenueDay, ProductPerformance,
} from "@/types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function extractErrorMessage(body: unknown, fallback: string): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      // FastAPI/Pydantic validation errors: a list of {loc, msg, type} objects.
      return detail
        .map((d) => (typeof d === "object" && d !== null && "msg" in d ? String((d as { msg: unknown }).msg) : JSON.stringify(d)))
        .join("; ");
    }
    if (detail != null) return JSON.stringify(detail);
  }
  return fallback;
}

async function request<T>(path: string, options: RequestInit = {}, auth = false): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
    ...(auth ? await authHeaders() : {}),
  };
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(extractErrorMessage(body, `Request failed: ${res.status}`));
  }
  return res.json();
}

export const api = {
  // Public, buyer-facing — no auth
  chat: (payload: { merchant_id: string; session_id?: string | null; message: string; buyer_budget?: number | null }) =>
    request<ChatResponse>("/agent/chat", { method: "POST", body: JSON.stringify(payload) }),

  createCheckoutIntent: (payload: {
    merchant_id: string; session_id?: string | null;
    line_items: { product_id: string; name: string; price: number; qty: number }[];
    buyer_budget?: number | null; discount_percent?: number;
  }) => request<CheckoutIntent>("/checkout/intent", { method: "POST", body: JSON.stringify(payload) }),

  approveCheckout: (checkout_intent_id: string, approve: boolean) =>
    request<CheckoutIntent>("/checkout/approve", { method: "POST", body: JSON.stringify({ checkout_intent_id, approve }) }),

  createPayment: (checkout_intent_id: string) =>
    request<{ order_id: string; payment_attempt_id: string; razorpay_order_id: string; razorpay_key_id: string; amount: number; currency: string }>(
      "/payments/create", { method: "POST", body: JSON.stringify({ checkout_intent_id }) }
    ),

  verifyPayment: (payload: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }) =>
    request<Order>("/payments/verify", { method: "POST", body: JSON.stringify(payload) }),

  listPublicProducts: (merchantId: string) =>
    // catalog browse without merchant auth isn't exposed yet server-side beyond /agent/chat search;
    // for the buyer UI we drive discovery through chat, matching the "AI shopping assistant" brief.
    Promise.resolve([] as Product[]),

  // Merchant-authed
  getMe: () => request<Merchant>("/merchants/me", {}, true),
  createMerchant: (payload: Partial<Merchant>) =>
    request<Merchant>("/merchants", { method: "POST", body: JSON.stringify(payload) }, true),
  completeOnboarding: () => request<Merchant>("/merchants/me/complete-onboarding", { method: "PUT" }, true),
  getPolicy: () => request<PolicyConfig>("/merchants/me/policy", {}, true),
  updatePolicy: (payload: Partial<PolicyConfig>) =>
    request<PolicyConfig>("/merchants/me/policy", { method: "PUT", body: JSON.stringify(payload) }, true),

  listProducts: () => request<Product[]>("/products", {}, true),
  createProduct: (payload: Partial<Product>) =>
    request<Product>("/products", { method: "POST", body: JSON.stringify(payload) }, true),
  updateProduct: (id: string, payload: Partial<Product>) =>
    request<Product>(`/products/${id}`, { method: "PUT", body: JSON.stringify(payload) }, true),
  deleteProduct: (id: string) => request<{ deleted: boolean }>(`/products/${id}`, { method: "DELETE" }, true),

  listOrders: () => request<Order[]>("/orders", {}, true),
  listAudit: (params?: { session_id?: string; event_type?: string }) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return request<AuditEvent[]>(`/audit${qs ? `?${qs}` : ""}`, {}, true);
  },
  analyticsSummary: () => request<AnalyticsSummary>("/analytics/summary", {}, true),
  revenueTimeseries: () => request<RevenueDay[]>("/analytics/revenue-timeseries", {}, true),
  productPerformance: () => request<ProductPerformance[]>("/analytics/product-performance", {}, true),
};
