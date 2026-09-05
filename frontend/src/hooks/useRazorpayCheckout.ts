import { useCallback } from "react";
import { api } from "@/services/api";

declare global {
  interface Window {
    Razorpay: new (options: Record<string, unknown>) => { open: () => void };
  }
}

let sdkPromise: Promise<void> | null = null;

function loadRazorpaySdk(): Promise<void> {
  if (window.Razorpay) return Promise.resolve();
  if (sdkPromise) return sdkPromise;
  sdkPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Razorpay checkout script."));
    document.body.appendChild(script);
  });
  return sdkPromise;
}

export function useRazorpayCheckout() {
  const startCheckout = useCallback(
    async (
      checkoutIntentId: string,
      opts: { businessName: string; onSuccess: () => void; onFailure: (reason: string) => void }
    ) => {
      try {
        const created = await api.createPayment(checkoutIntentId);
        if (!created.razorpay_key_id) {
          opts.onFailure("Razorpay is not configured for this merchant yet.");
          return;
        }
        await loadRazorpaySdk();

        const rzp = new window.Razorpay({
          key: created.razorpay_key_id,
          amount: Math.round(created.amount * 100),
          currency: created.currency,
          name: opts.businessName,
          description: "AURA Commerce — test mode purchase",
          order_id: created.razorpay_order_id,
          theme: { color: "#E8B454" },
          handler: async (response: {
            razorpay_order_id: string;
            razorpay_payment_id: string;
            razorpay_signature: string;
          }) => {
            try {
              await api.verifyPayment(response);
              opts.onSuccess();
            } catch (e) {
              opts.onFailure(e instanceof Error ? e.message : "Payment verification failed.");
            }
          },
          modal: {
            ondismiss: () => opts.onFailure("Payment window closed before completion."),
          },
        });
        rzp.open();
      } catch (e) {
        opts.onFailure(e instanceof Error ? e.message : "Could not start checkout.");
      }
    },
    []
  );

  return { startCheckout };
}
