# Database Schema Usage Report

This report summarizes the DB tables and columns currently present or recently added for billing, usage tracking, and app-level encryption. It is based on the repository code and the Supabase schema audit shared during setup. It does not include any sensitive row values.

## Executive Summary

The current schema has two groups of tables:

- Core app tables already used by the product flow: `profiles`, `user_accounts`, `credit_ledger`, `rate_limits`.
- New support tables/columns added for encryption, subscription history, usage reporting, and future security logging: `subscriptions`, `usage`, `user_activity_logs`, plus encrypted PII columns on `profiles`.

The schema is structurally close to complete, but the latest Supabase MCP audit found missing RLS hardening on several public tables. Some newly added pieces are not yet heavily used by the UI and should be treated as support/future-proofing unless we decide to make them the source of truth.

## Current Tables

## `profiles`

Purpose: stores user profile metadata linked to Supabase Auth user IDs.

Current columns:

| Column | Use | Current Status |
| --- | --- | --- |
| `id` | Primary user ID. Mirrors Supabase Auth user ID. Used for joins and ownership checks. | Active |
| `username` | Public/user-chosen handle. Used by auth/profile availability checks and UI metadata. | Active |
| `nickname` | Display name fallback. Used by profile responses and existing UI. | Active |
| `created_at` | Profile creation timestamp. | Active |
| `email` | AES-256-GCM encrypted email for app-level encrypted storage. | New; currently empty in existing rows |
| `email_hash` | HMAC-SHA256 lookup hash for email search/login/duplicate checks without plaintext email. | New; indexed |
| `full_name` | AES-256-GCM encrypted display name/full name. | New; currently empty in existing rows |
| `full_name_hash` | HMAC-SHA256 lookup hash for full-name lookup if needed. | New; indexed |

Indexes:

- `profiles_pkey` on `id`.
- Unique indexes on `username` and `nickname`.
- `ix_profiles_email_hash` unique index.
- `ix_profiles_full_name_hash` index.

Important note:

Existing rows currently have `email`/`full_name` empty, so there is no existing plaintext in those new columns to migrate. Supabase Auth still owns the actual login email unless we intentionally populate encrypted email into `profiles.email`.

## `user_accounts`

Purpose: current billing source of truth for plan and credit balance.

Columns:

| Column | Use | Current Status |
| --- | --- | --- |
| `id` | Internal row ID. | Active |
| `user_id` | Profile/Auth user ID. Unique account owner. | Active |
| `subscription_status` | Plan key: `free`, `starter`, `student_plus`, `pro`. | Active |
| `credits_remaining` | Current usable credit balance. | Active |
| `plan_name` | Human-readable plan name. | Active |
| `monthly_credit_limit` | Included monthly credits for the plan. | Active |
| `polar_subscription_id` | Polar subscription identifier for reconciliation. | Active |
| `updated_at` | Last account update timestamp. | Active |

Where used:

- `backend/app/services/billing.py`
- `backend/app/services/polar_webhook.py`
- `backend/app/main.py`
- `backend/app/graphs.py`
- Frontend billing/status display via `/api/billing/status`

Important note:

This is still the main billing state table. `subscriptions` currently mirrors subscription data, but `user_accounts` is what the app reads most directly.

## `credit_ledger`

Purpose: tracks credit reservations and captures/releases around paid operations.

Columns:

| Column | Use | Current Status |
| --- | --- | --- |
| `id` | Ledger row ID. | Active |
| `user_id` | Owner profile/auth ID. | Active |
| `feature` | Feature consuming credits, e.g. `coach`, `humanize`. | Active |
| `amount` | Credits reserved/charged. | Active |
| `status` | Reservation state: `reserved`, `charged`, `released`. | Active |
| `created_at` | Creation timestamp. | Active |
| `updated_at` | Update timestamp. | Active |

Where used:

- Credit reservation/capture/release methods in `backend/app/services/billing.py`.
- Coach/humanize endpoints in `backend/app/main.py`.

## `rate_limits`

Purpose: free-tier daily usage limit tracking.

Columns from Supabase audit:

| Column | Use | Current Status |
| --- | --- | --- |
| `user_id` | User being rate-limited. | Active or legacy depending on deployed rate-limit path |
| `limit_date` | Date for daily limit bucket. | Active or legacy |
| `attempts` | Attempts used for that date. | Active or legacy |

Important note:

The repository also has an in-memory `DailyBasicAnalysisLimiter` service for tests/demo behavior. If production should rely on persistent rate limits, this table should be wired explicitly and tested.

## `subscriptions`

Purpose: subscription-state mirror table for Polar subscription lifecycle.

Columns:

| Column | Use | Current Status |
| --- | --- | --- |
| `id` | Internal row ID. | New |
| `user_id` | Owner profile/auth ID. Unique. | New |
| `subscription_status` | Plan key mirrored from webhook. | New |
| `plan_name` | Human-readable plan name. | New |
| `monthly_credit_limit` | Included credits for subscription plan. | New |
| `polar_subscription_id` | Polar subscription ID. Indexed. | New |
| `created_at` | Creation timestamp. | New |
| `updated_at` | Update timestamp. | New |

Where used:

- Created/synced by `BillingService.async_get_or_create_db_account`.
- Updated by `BillingService.async_sync_subscription`.
- Called from Polar webhook handler when subscriptions become active/canceled/revoked.

RLS:

- Enabled.
- Select policy: user can read rows where `user_id = auth.uid()`.

Important note:

This currently overlaps with `user_accounts`. It is useful as a subscription mirror/history surface, but `user_accounts` remains the operational billing source of truth. We should either keep it as a mirror intentionally or later consolidate billing around one table.

## `usage`

Purpose: monthly feature usage tracking for dashboard/progress and auditability.

Columns:

| Column | Use | Current Status |
| --- | --- | --- |
| `id` | Internal row ID. | New |
| `user_id` | Owner profile/auth ID. | New |
| `period_key` | Month bucket, e.g. `2026-05`. | New |
| `feature` | Feature used, e.g. `coach`, `humanize`. | New |
| `request_count` | Number of completed requests. | New |
| `word_count` | Total input words processed. | New |
| `credits_used` | Total credits consumed. | New |
| `created_at` | Creation timestamp. | New |
| `updated_at` | Update timestamp. | New |

Indexes/constraints:

- `ix_usage_user_id`.
- `ix_usage_period_key`.
- Unique constraint/index on `(user_id, period_key, feature)`.

Where used:

- `BillingService.async_record_usage`.
- Called from `/api/coach` and `/api/humanize` after successful real-user operations.

RLS:

- Enabled.
- Select policy: user can read rows where `user_id = auth.uid()`.

Important note:

The current frontend progress bar is calculated from `monthly_credit_limit - credits_remaining`, not directly from `usage`. The `usage` table records detailed usage but is not yet the main frontend source. This is acceptable but should be documented as current behavior.

## `user_activity_logs`

Purpose: future security/activity audit logging with encrypted IP addresses.

Columns:

| Column | Use | Current Status |
| --- | --- | --- |
| `id` | Internal row ID. | New |
| `user_id` | Optional owner profile/auth ID. | New |
| `event_type` | Activity event name. | New |
| `ip_address` | AES-256-GCM encrypted IP address. | New |
| `created_at` | Creation timestamp. | New |

Where used:

- Model exists as `UserActivityLogDB`.
- Migration script encrypts `ip_address` if existing plaintext values are present.
- No active insert flow is currently wired in the FastAPI endpoints.

RLS:

- Enabled.
- Select policy: user can read rows where `user_id = auth.uid()`.

Important note:

This table is currently mostly future-ready. It is safe because it is empty and RLS-protected, but it is not yet a required runtime table unless we add activity logging.

## Encryption Model

Implemented utilities:

- TypeScript utility: `lib/encryption.ts`
- Backend runtime utility: `backend/app/lib/encryption.py`
- Key generation script: `scripts/generate-encryption-keys.ts`
- Migration script: `scripts/migrate-encrypt.ts`

Encryption details:

- Algorithm: AES-256-GCM.
- IV: random 16 bytes for every encryption.
- Stored format: `iv:authTag:encryptedData`, hex encoded.
- Encryption key: `ENCRYPTION_KEY`, 32 bytes / 64 hex characters.
- Lookup hash: HMAC-SHA256 using `HASH_KEY`.

Important operational rule:

After any production data has been encrypted or hashed, `ENCRYPTION_KEY` and `HASH_KEY` must not be changed unless we implement a controlled key-rotation migration. Losing `ENCRYPTION_KEY` makes encrypted values unrecoverable.

## Migration Status

Current Supabase audit showed:

- `profiles_total`: 3.
- `profiles.email` values present: 0.
- `profiles.full_name` values present: 0.
- `user_activity_logs` rows: 0.
- `user_activity_logs.ip_address` values present: 0.

Conclusion:

There is currently no existing data in the new encrypted columns to migrate. `scripts/migrate-encrypt.ts` is still useful for future/plaintext cleanup, but it is not necessary for the currently audited `email`, `full_name`, or `ip_address` columns.

## RLS Status

Verified RLS-enabled tables:

- `subscriptions`: RLS enabled.
- `usage`: RLS enabled.
- `user_activity_logs`: RLS enabled.
- `credit_ledger`: RLS enabled, but the latest audit found no policy before the hardening migration.

Latest audit findings:

- `profiles`: RLS disabled.
- `user_accounts`: RLS disabled.
- `rate_limits`: RLS disabled.
- `credit_ledger`: RLS enabled with no policies.
- `handle_new_user()`: `SECURITY DEFINER` function had mutable `search_path` and direct RPC execute privileges for `anon`/`authenticated`.

Policies:

- `Users can read own subscription`: `user_id = auth.uid()`.
- `Users can read own usage`: `user_id = auth.uid()`.
- `Users can read own activity logs`: `user_id = auth.uid()`.

These policy names are internal DB labels. They are not shown to end users.

The remediation SQL is stored in `supabase/migrations/20260524000000_harden_public_rls_and_trigger_function.sql`. The MCP connection used for the latest audit was read-only, so it could not apply the migration directly.

## Current Risks / Cleanup Questions

1. `subscriptions` overlaps with `user_accounts`.
   - Keep if we want a normalized subscription mirror.
   - Remove or stop using if we want `user_accounts` as the only billing state table.

2. `usage` records detailed usage but frontend usage progress currently uses credit balance math.
   - This is fine for now.
   - Later, an explicit usage endpoint could read from `usage`.

3. `user_activity_logs` is not actively written yet.
   - Keep if we plan security/audit logging.
   - Otherwise it is optional and can remain empty.

4. `nickname` remains plaintext.
   - Current encryption request targeted `profiles.email` and `profiles.full_name`.
   - Existing app still uses `username`/`nickname`.
   - If `nickname` is considered sensitive PII, we should either migrate it into encrypted `full_name` or add a separate encrypted nickname strategy.

## Recommended Next Steps

1. Deploy current encryption-aware code with `ENCRYPTION_KEY` and `HASH_KEY` set in Vercel/backend environment variables.
2. Create a fresh test account and verify:
   - `profiles.email` is `hex:hex:hex` if the app writes it.
   - `profiles.email_hash` is a 64-character hex string.
   - `profiles.full_name` is `hex:hex:hex` if written.
   - `profiles.full_name_hash` is a 64-character hex string if written.
3. Test checkout webhook again:
   - `user_accounts` updates.
   - `subscriptions` mirrors the subscription state.
4. Run coach/humanize once as a paid test user:
   - `credit_ledger` records reservation/capture.
   - `usage` increments for the month.
5. Decide whether to keep `subscriptions` and `user_activity_logs` as intentional long-term tables or simplify before launch.
