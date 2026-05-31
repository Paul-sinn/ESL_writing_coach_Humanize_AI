-- Allow OAuth-created profiles to exist before the app collects a username.
-- Google OAuth does not provide app-specific username metadata, so the
-- auth.users trigger must be able to insert a profile with username NULL.
-- The app completes onboarding later by setting profiles.username.

alter table public.profiles
  alter column username drop not null;
