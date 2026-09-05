-- Creates a second demo merchant directly, bypassing the signup/onboarding UI.
-- Run this in Supabase SQL Editor -> New query -> paste -> Run.
--
-- IMPORTANT: this merchant will work for the BUYER chat (/buyer/<id>) immediately,
-- since that endpoint requires no login. It will NOT let you log into /dashboard as
-- this merchant, because dashboard login is verified by your backend against a real
-- Supabase Auth session — that's a separate issue from whether this row exists.

-- 1. Insert the merchant and capture its new id.
with new_merchant as (
  insert into merchants (
    id, auth_user_id, business_name, description, category, currency,
    store_description, contact_email, onboarding_complete, created_at, updated_at
  )
  values (
    gen_random_uuid(),
    'sql-demo-merchant',              -- placeholder, not a real Supabase Auth user
    'Quick Test Store',
    'Created directly via SQL for testing.',
    'General',
    'INR',
    'A quick test storefront.',
    'test@example.com',
    true,
    now(),
    now()
  )
  returning id
)
-- 2. Insert matching agent_config and policy rows (both required — the backend expects
--    every merchant to have exactly one of each).
insert into agent_configs (id, merchant_id, agent_name, personality, upselling_enabled, cross_selling_enabled, allowed_actions, created_at, updated_at)
select gen_random_uuid(), id, 'Aura', 'friendly, concise, helpful', true, true,
       'search_products,get_product,compare_products,check_inventory,calculate_cart,create_checkout_intent,request_buyer_approval',
       now(), now()
from new_merchant;

insert into policies (id, merchant_id, max_transaction_amount, approval_threshold, max_automatic_retries, max_discount_percent, max_upsell_amount, created_at, updated_at)
select gen_random_uuid(), id, 2000, 1000, 1, 10, 200, now(), now()
from merchants where auth_user_id = 'sql-demo-merchant';

-- 3. See the new merchant's id (use this in your /buyer/<id> URL).
select id, business_name from merchants where auth_user_id = 'sql-demo-merchant';
