-- Create an operator-only billing lookup view that joins Supabase Auth email
-- with the app billing state. Keep it outside the public schema so user email
-- is not duplicated into app tables or exposed through the public Data API.

create schema if not exists app_admin;

revoke all on schema app_admin from public;
revoke all on schema app_admin from anon;
revoke all on schema app_admin from authenticated;

create or replace view app_admin.billing_accounts_with_email as
select
    auth_user.id as user_id,
    auth_user.email,
    profile.username,
    profile.nickname,
    coalesce(account.subscription_status, subscription.subscription_status, 'free') as subscription_status,
    coalesce(account.plan_name, subscription.plan_name, 'Free') as plan_name,
    coalesce(account.credits_remaining, 0) as credits_remaining,
    coalesce(account.monthly_credit_limit, subscription.monthly_credit_limit, 0) as monthly_credit_limit,
    coalesce(account.polar_subscription_id, subscription.polar_subscription_id) as polar_subscription_id,
    (
        coalesce(account.subscription_status, subscription.subscription_status, 'free') <> 'free'
        or coalesce(account.credits_remaining, 0) > 0
    ) as is_paid_or_has_credits,
    auth_user.email_confirmed_at,
    auth_user.last_sign_in_at,
    auth_user.created_at as auth_created_at,
    account.updated_at as account_updated_at,
    subscription.updated_at as subscription_updated_at,
    profile.deleted_at as account_deleted_at
from auth.users as auth_user
left join public.profiles as profile
    on profile.id = auth_user.id
left join public.user_accounts as account
    on account.user_id = auth_user.id
left join public.subscriptions as subscription
    on subscription.user_id = auth_user.id
order by
    is_paid_or_has_credits desc,
    plan_name,
    auth_user.email;

comment on view app_admin.billing_accounts_with_email is
    'Operator-only view for matching Supabase Auth emails to EssayCoach billing plans and credit state.';

revoke all on app_admin.billing_accounts_with_email from public;
revoke all on app_admin.billing_accounts_with_email from anon;
revoke all on app_admin.billing_accounts_with_email from authenticated;

grant usage on schema app_admin to service_role;
grant select on app_admin.billing_accounts_with_email to service_role;
