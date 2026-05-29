-- Harden public schema RLS and trigger function exposure.
--
-- Apply this against the Supabase project database with a write-capable
-- migration path. The connected MCP in this session is read-only, so it
-- cannot apply this file directly.

-- 1) Enable RLS on public tables that were exposed without row policies.
alter table public.profiles enable row level security;
alter table public.user_accounts enable row level security;
alter table public.rate_limits enable row level security;

alter table public.profiles add column if not exists terms_accepted_at timestamptz;
alter table public.profiles add column if not exists privacy_accepted_at timestamptz;
alter table public.profiles add column if not exists onboarded_at timestamptz;
alter table public.profiles add column if not exists deleted_at timestamptz;
create index if not exists ix_profiles_deleted_at on public.profiles (deleted_at);

-- 2) Recreate existing read policies with initplan-friendly auth.uid() usage.
drop policy if exists "Users can read own subscription" on public.subscriptions;
create policy "Users can read own subscription"
  on public.subscriptions
  for select
  to authenticated
  using (user_id = (select auth.uid()));

drop policy if exists "Users can read own usage" on public.usage;
create policy "Users can read own usage"
  on public.usage
  for select
  to authenticated
  using (user_id = (select auth.uid()));

drop policy if exists "Users can read own activity logs" on public.user_activity_logs;
create policy "Users can read own activity logs"
  on public.user_activity_logs
  for select
  to authenticated
  using (user_id = (select auth.uid()));

-- 3) Add missing owner-scoped policies for profile/account/rate-limit/ledger
-- visibility. Billing writes remain server-side only.
drop policy if exists "Users can read own profile" on public.profiles;
create policy "Users can read own profile"
  on public.profiles
  for select
  to authenticated
  using (id = (select auth.uid()));

drop policy if exists "Users can insert own profile" on public.profiles;
create policy "Users can insert own profile"
  on public.profiles
  for insert
  to authenticated
  with check (id = (select auth.uid()));

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile"
  on public.profiles
  for update
  to authenticated
  using (id = (select auth.uid()))
  with check (id = (select auth.uid()));

drop policy if exists "Users can read own account" on public.user_accounts;
create policy "Users can read own account"
  on public.user_accounts
  for select
  to authenticated
  using (user_id = (select auth.uid()));

drop policy if exists "Users can read own rate limit" on public.rate_limits;
create policy "Users can read own rate limit"
  on public.rate_limits
  for select
  to authenticated
  using (user_id = (select auth.uid()));

drop policy if exists "Users can read own credit ledger" on public.credit_ledger;
create policy "Users can read own credit ledger"
  on public.credit_ledger
  for select
  to authenticated
  using (user_id = (select auth.uid()));

-- 4) Keep signup trigger behavior, but pin search_path for SECURITY DEFINER
-- safety.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
    insert into public.profiles (
        id,
        username,
        nickname,
        terms_accepted_at,
        privacy_accepted_at,
        onboarded_at
    )
    values (
        new.id,
        new.raw_user_meta_data->>'username',
        new.raw_user_meta_data->>'nickname',
        case when (new.raw_user_meta_data->>'accepted_terms')::boolean then now() else null end,
        case when (new.raw_user_meta_data->>'accepted_privacy')::boolean then now() else null end,
        case when new.raw_user_meta_data->>'username' is not null then now() else null end
    )
    on conflict (id) do nothing;

    insert into public.user_accounts (user_id, subscription_status, credits_remaining, plan_name, monthly_credit_limit)
    values (new.id, 'free', 0, 'Free', 0)
    on conflict (user_id) do nothing;

    return new;
end;
$$;

-- 5) Prevent direct RPC execution of the SECURITY DEFINER trigger function.
revoke execute on function public.handle_new_user() from public;
revoke execute on function public.handle_new_user() from anon;
revoke execute on function public.handle_new_user() from authenticated;
