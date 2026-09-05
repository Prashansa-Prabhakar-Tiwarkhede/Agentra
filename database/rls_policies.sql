-- Row Level Security policies for AURA Commerce.
--
-- Context: the FastAPI backend uses the Supabase SERVICE ROLE key (via DATABASE_URL) for
-- all queries, which bypasses RLS entirely — the app-layer merchant scoping in every
-- endpoint (e.g. `Product.merchant_id == merchant.id`) is what actually protects data today.
--
-- RLS matters as a SECOND layer of defense in case:
--   (a) the Supabase anon/public key is ever used directly from the frontend for reads
--   (b) a future endpoint forgets to scope a query by merchant_id
--   (c) someone queries the DB directly via the Supabase dashboard with a non-service role
--
-- Run this in the Supabase SQL Editor (Dashboard -> SQL Editor -> New query -> paste -> Run).
-- Safe to re-run — uses IF NOT EXISTS / DROP POLICY IF EXISTS guards.

-- 1. Enable RLS on every table.
alter table merchants enable row level security;
alter table agent_configs enable row level security;
alter table policies enable row level security;
alter table products enable row level security;
alter table agent_sessions enable row level security;
alter table agent_messages enable row level security;
alter table checkout_intents enable row level security;
alter table orders enable row level security;
alter table payment_attempts enable row level security;
alter table audit_events enable row level security;

-- 2. The backend's service role key bypasses RLS by default in Supabase, so these policies
--    only need to cover what happens when a request is made with a LESS privileged key
--    (the anon/public key, e.g. if the frontend ever queries Supabase directly instead of
--    going through the FastAPI backend).

-- Merchants can read/write only their own merchant row.
drop policy if exists "merchants_owner_access" on merchants;
create policy "merchants_owner_access" on merchants
  for all
  using (auth.uid()::text = auth_user_id)
  with check (auth.uid()::text = auth_user_id);

-- Agent config / policy: scoped to the owning merchant.
drop policy if exists "agent_configs_owner_access" on agent_configs;
create policy "agent_configs_owner_access" on agent_configs
  for all
  using (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text))
  with check (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text));

drop policy if exists "policies_owner_access" on policies;
create policy "policies_owner_access" on policies
  for all
  using (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text))
  with check (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text));

-- Products: merchants manage their own catalog. Public (anon) read access is allowed so a
-- buyer-facing storefront could read products directly if needed later — write stays owner-only.
drop policy if exists "products_public_read" on products;
create policy "products_public_read" on products
  for select
  using (true);

drop policy if exists "products_owner_write" on products;
create policy "products_owner_write" on products
  for insert
  with check (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text));

drop policy if exists "products_owner_update" on products;
create policy "products_owner_update" on products
  for update
  using (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text))
  with check (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text));

drop policy if exists "products_owner_delete" on products;
create policy "products_owner_delete" on products
  for delete
  using (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text));

-- Orders, audit events, checkout intents, payment attempts: owner-only, no public access.
-- Buyers are anonymous/session-scoped in this build (no buyer accounts), so these stay
-- readable only by the merchant that owns them, via the backend's service role.
drop policy if exists "orders_owner_access" on orders;
create policy "orders_owner_access" on orders
  for all
  using (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text))
  with check (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text));

drop policy if exists "audit_events_owner_access" on audit_events;
create policy "audit_events_owner_access" on audit_events
  for all
  using (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text))
  with check (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text));

drop policy if exists "checkout_intents_owner_access" on checkout_intents;
create policy "checkout_intents_owner_access" on checkout_intents
  for all
  using (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text))
  with check (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text));

drop policy if exists "payment_attempts_owner_access" on payment_attempts;
create policy "payment_attempts_owner_access" on payment_attempts
  for all
  using (
    order_id in (
      select o.id from orders o
      join merchants m on m.id = o.merchant_id
      where m.auth_user_id = auth.uid()::text
    )
  );

-- Agent sessions / messages: owner-only.
drop policy if exists "agent_sessions_owner_access" on agent_sessions;
create policy "agent_sessions_owner_access" on agent_sessions
  for all
  using (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text))
  with check (merchant_id in (select id from merchants where auth_user_id = auth.uid()::text));

drop policy if exists "agent_messages_owner_access" on agent_messages;
create policy "agent_messages_owner_access" on agent_messages
  for all
  using (
    session_id in (
      select s.id from agent_sessions s
      join merchants m on m.id = s.merchant_id
      where m.auth_user_id = auth.uid()::text
    )
  );
