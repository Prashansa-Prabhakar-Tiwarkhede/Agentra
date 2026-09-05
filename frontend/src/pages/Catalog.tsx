import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, ImageOff } from "lucide-react";
import { api } from "@/services/api";
import type { Product } from "@/types";

export default function Catalog() {
  const qc = useQueryClient();
  const { data: products, isLoading, error } = useQuery({ queryKey: ["products"], queryFn: api.listProducts });
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", category: "", price: 0, inventory: 0, description: "", imageUrl: "" });

  const createMutation = useMutation({
    mutationFn: () =>
      api.createProduct({
        name: form.name,
        category: form.category,
        price: form.price,
        inventory: form.inventory,
        description: form.description,
        currency: "INR",
        tags: [],
        attributes: {},
        images: form.imageUrl ? [form.imageUrl] : [],
        upsell_product_ids: [],
        cross_sell_product_ids: [],
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["products"] });
      setShowForm(false);
      setForm({ name: "", category: "", price: 0, inventory: 0, description: "", imageUrl: "" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteProduct(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl mb-1">Catalog</h1>
          <p className="text-sm text-muted">{products?.length ?? 0} products, AI-readable.</p>
        </div>
        <button onClick={() => setShowForm((s) => !s)} className="btn-primary text-sm flex items-center gap-2">
          <Plus size={16} /> Add product
        </button>
      </div>

      {error && <p className="text-danger text-sm font-mono mb-4">Sign in as a merchant to manage the catalog.</p>}

      {showForm && (
        <div className="card p-5 mb-6 grid grid-cols-2 gap-3">
          <input className="input" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="input" placeholder="Category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          <input className="input" type="number" placeholder="Price (₹)" value={form.price || ""} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} />
          <input className="input" type="number" placeholder="Inventory" value={form.inventory || ""} onChange={(e) => setForm({ ...form, inventory: Number(e.target.value) })} />
          <input className="input col-span-2" placeholder="Image URL (optional)" value={form.imageUrl} onChange={(e) => setForm({ ...form, imageUrl: e.target.value })} />
          <textarea className="input col-span-2" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <button onClick={() => createMutation.mutate()} disabled={!form.name || !form.price} className="btn-primary col-span-2">
            {createMutation.isPending ? "Saving…" : "Save product"}
          </button>
        </div>
      )}

      {isLoading && <p className="text-muted text-sm">Loading…</p>}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {products?.map((p: Product) => (
          <div key={p.id} className="card p-4">
            <div className="flex items-start gap-3">
              {p.images && p.images[0] ? (
                <img
                  src={p.images[0]}
                  alt={p.name}
                  className="w-12 h-12 rounded-lg object-cover border border-border shrink-0"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              ) : (
                <div className="w-12 h-12 rounded-lg border border-border shrink-0 flex items-center justify-center text-muted/40">
                  <ImageOff size={16} />
                </div>
              )}
              <div className="flex-1 min-w-0 flex items-start justify-between">
                <div className="min-w-0">
                  <div className="font-medium text-sm truncate">{p.name}</div>
                  <div className="text-xs text-muted mt-0.5">{p.category}</div>
                </div>
                <button onClick={() => deleteMutation.mutate(p.id)} className="text-muted hover:text-danger transition-colors shrink-0">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
            <div className="flex items-center justify-between mt-4">
              <span className="font-mono text-amber">₹{p.price.toFixed(0)}</span>
              <span className={`text-xs font-mono ${p.inventory > 0 ? "text-success" : "text-danger"}`}>
                {p.inventory > 0 ? `${p.inventory} in stock` : "out of stock"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
