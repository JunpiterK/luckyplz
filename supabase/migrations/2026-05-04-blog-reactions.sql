-- Blog reactions: anonymous 1-click feedback per blog post.
-- Pattern follows the "messaging RPC" rule (memory: messaging_rpc_pattern)
-- where mobile WebView silently fails on RLS-gated direct selects, so all
-- reads/writes go through SECURITY DEFINER RPCs.
--
-- One row per click. We don't dedupe in SQL; the client uses localStorage
-- to gate per-device per-post repeat reactions. That keeps backend simple
-- and tolerant of corrupt/missing client state — at worst a determined
-- user can pad counts by clearing storage, which is fine for vanity
-- engagement signals (not voting).

create table if not exists public.blog_reactions (
    id          bigint generated always as identity primary key,
    slug        text not null,
    kind        text not null check (kind in ('like','fire','idea','question')),
    created_at  timestamptz not null default now()
);

create index if not exists blog_reactions_slug_idx on public.blog_reactions(slug);
create index if not exists blog_reactions_slug_kind_idx on public.blog_reactions(slug, kind);

-- RLS on, but no direct policies. All access via the two RPCs below.
alter table public.blog_reactions enable row level security;

-- ---------------------------------------------------------------------
-- add_blog_reaction(slug, kind) — record a single click.
-- ---------------------------------------------------------------------
create or replace function public.add_blog_reaction(p_slug text, p_kind text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
    if p_slug is null or length(p_slug) = 0 or length(p_slug) > 100 then
        raise exception 'invalid slug';
    end if;
    if p_kind not in ('like','fire','idea','question') then
        raise exception 'invalid kind';
    end if;
    insert into public.blog_reactions(slug, kind) values (p_slug, p_kind);
end;
$$;

revoke all on function public.add_blog_reaction(text, text) from public;
grant execute on function public.add_blog_reaction(text, text) to anon, authenticated;

-- ---------------------------------------------------------------------
-- get_blog_reactions(slug) — read aggregated counts for a single post.
-- Returns one row per kind, even kinds with zero clicks (so the client
-- can render all four buttons without separate calls).
-- ---------------------------------------------------------------------
create or replace function public.get_blog_reactions(p_slug text)
returns table(kind text, cnt int)
language sql
security definer
stable
set search_path = public
as $$
    with kinds(k) as (
        values ('like'),('fire'),('idea'),('question')
    )
    select k as kind,
           coalesce((select count(*)::int from public.blog_reactions r
                     where r.slug = p_slug and r.kind = k), 0) as cnt
    from kinds;
$$;

revoke all on function public.get_blog_reactions(text) from public;
grant execute on function public.get_blog_reactions(text) to anon, authenticated;

comment on table public.blog_reactions is
    'Anonymous reaction clicks on blog posts. Read/write via RPCs only.';
comment on function public.add_blog_reaction(text, text) is
    'Record a single reaction click. Validates kind ∈ {like,fire,idea,question}.';
comment on function public.get_blog_reactions(text) is
    'Aggregated reaction counts for a post slug. Always returns 4 rows (one per kind).';
