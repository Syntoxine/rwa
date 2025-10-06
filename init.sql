CREATE EXTENSION IF NOT EXISTS moddatetime;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

create table nations (
  name text not null,
  fullname text null,
  region text not null,
  wa_member boolean not null default false,
  wa_delegate boolean not null default false,
  endorsements text[] not null default '{}'::text[],
  flag text null,
  active boolean not null default true,
  updated_at timestamp with time zone null default now(),
  constraint nations_pkey primary key (name)
) TABLESPACE pg_default;

create trigger handle_updated_at BEFORE
update on nations for EACH row
execute FUNCTION moddatetime ('updated_at');