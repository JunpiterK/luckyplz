-- Blog reactions: add toggle / undo support.
-- Companion to 2026-05-04-blog-reactions.sql.
--
-- The widget now toggles on click — first click adds, second click
-- removes. Per-device dedupe still lives in localStorage, so this RPC
-- just decrements the aggregate count by deleting the most recent row
-- for the given (slug, kind).
--
-- Trade-off (intentional): we don't track who reacted. So "remove"
-- deletes ANY one row for that (slug, kind) — typically the latest.
-- A determined user could click "remove" without first clicking "add"
-- and offset another user's reaction. That's fine for vanity engagement
-- counters; it would not be acceptable if these were votes.

create or replace function public.remove_blog_reaction(p_slug text, p_kind text)
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
    -- Delete the most recent row for this (slug, kind). Approximate
    -- "undo" since we don't track per-user. If no rows exist the
    -- delete is a no-op — safe.
    delete from public.blog_reactions
    where id = (
        select id from public.blog_reactions
        where slug = p_slug and kind = p_kind
        order by created_at desc
        limit 1
    );
end;
$$;

revoke all on function public.remove_blog_reaction(text, text) from public;
grant execute on function public.remove_blog_reaction(text, text) to anon, authenticated;

comment on function public.remove_blog_reaction(text, text) is
    'Decrement reaction count by deleting the most recent matching row. Used by the widget toggle/undo path.';
