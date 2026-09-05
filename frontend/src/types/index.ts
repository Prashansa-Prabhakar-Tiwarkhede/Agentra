export interface Product {
  id: string;
  merchant_id: string;
  name: string;
  description: string | null;
  category: string | null;
  price: number;
  currency: string;
  sku: string | null;
  inventory: number;
  images: string[];
  tags: string[];
  attributes: Record<string, string>;
  upsell_product_ids: string[];
  cross_sell_product_ids: string[];
}

/**
 * The narrower shape returned inside AI chat responses (Product.to_ai_context() on the
 * backend). Deliberately does not include an exact inventory count — buyers only ever see
 * an in_stock boolean, never the raw number. Chat UI must check `in_stock`, not `inventory`.
 */
export interface ChatProduct {
  product_id: string;
  name: string;
  description: string | null;
  category: string | null;
  price: number;
  currency: string;
  in_stock: boolean;
  tags: string[];
  attributes: Record<string, string>;
  image_url: string | null;
}

export interface Merchant {
  id: string;
  business_name: string;
  logo_url: string | null;
  description: string | null;
  category: string | null;
  currency: string;
  store_description: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  onboarding_complete: boolean;
}

export interface PolicyConfig {
  max_transaction_amount: number;
  approval_threshold: number;
  max_automatic_retries: number;
  max_discount_percent: number;
  max_upsell_amount: number;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  structured_action: {
    action: string;
    product_id: string;
    reason: string;
    confidence: number;
  } | null;
  products: ChatProduct[];
  cart_preview: unknown | null;
}

export type PolicyDecision = "ALLOWED" | "REQUIRES_APPROVAL" | "BLOCKED";

export interface CheckoutIntent {
  id: string;
  subtotal: number;
  total: number;
  currency: string;
  policy_decision: PolicyDecision | null;
  policy_reason: string | null;
  requires_approval: boolean;
  buyer_approved: boolean | null;
  status: string;
}

export interface Order {
  id: string;
  merchant_id: string;
  line_items: { name: string; unit_price: number; qty: number; line_total: number }[];
  amount: number;
  currency: string;
  payment_status: string;
  order_status: string;
  is_ai_generated: boolean;
  razorpay_order_id: string | null;
  razorpay_payment_id: string | null;
}

export interface AuditEvent {
  id: string;
  created_at: string;
  event_type: string;
  actor: string;
  reason: string | null;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  policy_decision: PolicyDecision | null;
  amount: number | null;
  result: string | null;
}

export interface AnalyticsSummary {
  ai_gmv: number;
  ai_orders: number;
  conversion_rate_percent: number;
  average_order_value: number;
  agent_sessions: number;
  upsells_suggested: number;
  cross_sells_suggested: number;
  successful_payments: number;
  failed_payments: number;
  note: string;
}

export interface RevenueDay {
  date: string;
  revenue: number;
  orders: number;
}

export interface ProductPerformance {
  name: string;
  units_sold: number;
  revenue: number;
}
