-- =====================================================================
-- Migration: get_dm_thread_messages RPC
-- Date:      2026-04-22
-- Purpose:   Mobile Chrome Android + Samsung Internet showed empty
--            chat panes when opening a DM thread, despite the sidebar
--            summary (served by the existing dm_inbox SECURITY DEFINER
--            RPC) being populated correctly. Direct-table SELECT
--            through PostgREST was returning zero rows on mobile even
--            though the data was there — we suspect an RLS evaluation
--            edge case in the mobile WebView's auth context.
--
--            Routing the main thread-load path through a SECURITY
--            DEFINER RPC sidesteps both the RLS context differences
--            AND the client-side md5 thread_id computation that used
--            to be the primary bug surface. Same pattern the inbox
--            already uses successfully.
--
-- The RPC returns messages between the caller (auth.uid()) and
-- p_friend, ordered oldest-first (so the client can render directly
-- without reversing). Supports cursor pagination via p_before.
-- =====================================================================

create or replace function public.get_dm_thread_messages(
    p_friend  uuid,
    p_before  timestamptz default null,
    p_limit   int default 50
) returns table (
    id               bigint,
    thread_id        uuid,
    from_id          uuid,
    to_id            uuid,
    body             text,
    created_at       timestamptz,
    read_at          timestamptz,
    deleted_at       timestamptz,
    attachment_url   text,
    attachment_type  text,
    attachment_size  bigint,
    attachment_name  text,
    reply_to_id      bigint
)
language sql security definer
set search_path = public
as $$
    /* Filter by the (auth.uid, p_friend) pair both ways. Server-side,
       so no client-side thread_id ambiguity. Deleted rows stay in the
       result with deleted_at set — client renders them as a tombstone. */
    with me as (select auth.uid() as uid)
    select d.id, d.thread_id, d.from_id, d.to_id, d.body,
           d.created_at, d.read_at, d.deleted_at,
           d.attachment_url, d.attachment_type, d.attachment_size, d.attachment_name,
           d.reply_to_id
    from public.direct_messages d, me
    where ( (d.from_id = me.uid and d.to_id = p_friend)
         or (d.from_id = p_friend and d.to_id = me.uid) )
      and (p_before is null or d.created_at < p_before)
    order by d.created_at asc
    limit greatest(1, least(p_limit, 200));
$$;

grant execute on function public.get_dm_thread_messages(uuid, timestamptz, int) to authenticated;
