-- Restore profiles.nickname after accidental removal.
-- Runtime code and the signup trigger still reference this column.

alter table public.profiles
  add column if not exists nickname varchar(50);

create unique index if not exists ix_profiles_nickname
  on public.profiles (nickname);
