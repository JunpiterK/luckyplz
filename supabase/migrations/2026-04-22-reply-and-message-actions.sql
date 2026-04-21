-- =====================================================================
-- Migration: Message actions — reply_to + delete-for-everyone
-- Date:      2026-04-22
-- Purpose:   Bring the messenger up to WhatsApp / KakaoTalk parity on
--            per-message actions.
--
-- Additions:
--   * direct_messages.reply_to_id  (FK to own id, SET NULL on cascade)
--   * chat_messages.reply_to_id   (FK to own id, SET NULL on cascade)
--   * RPCs for soft-delete so the client doesn't have to update rows
--     directly (the RLS policies we already have permit the author
--     to update deleted_at, but routing through an RPC lets us add
--     sanity guards + keeps the audit trail consistent if we ever
--     want to log deletions).
--
-- Delete semantics:
--   * delete_dm(id)      — only the SENDER can delete. Sets deleted_at
--                          + clears body/attachment_*. UI renders the
--                          row as a '삭제된 메시지' tombstone for both
--                          sides. 5-minute grace: after that, blocks
--                          (matches KakaoTalk's 5 min rule).
--   * delete_group_msg(id) — sender OR room creator can delete. Same
--                          clearing + tombstone shape.
--
-- reply_to rendering happens entirely client-side: when a row has
-- reply_to_id set, the client fetches the referenced row (cheap, one
-- row by id) and renders a small quote bar above the bubble.
-- =====================================================================


-- Reply columns — nullable, FK SET NULL so deleting the quoted
-- message doesn't cascade-delete every reply that referenced it.
alter table public.direct_messages
    add column if not exists reply_to_id bigint
        references public.direct_messages(id) on delete set null;

alter table public.chat_messages
    add column if not exists reply_to_id bigint
        references public.chat_messages(id) on delete set null;

create index if not exists direct_messages_reply_idx
    on public.direct_messages (reply_to_id) where reply_to_id is not null;
create index if not exists chat_messages_reply_idx
    on public.chat_messages (reply_to_id) where reply_to_id is not null;


-- Delete DM: only the sender, within the 5-minute grace window.
-- Clears body + attachment fields so the row no longer leaks data;
-- deleted_at is the signal the client uses to render the tombstone.
create or replace function public.delete_dm(p_msg_id bigint)
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        msg public.direct_messages%rowtype;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    select * into msg from public.direct_messages where id = p_msg_id;
    if not found then raise exception 'not_found'; end if;
    if msg.from_id <> me then raise exception 'not_author'; end if;
    if msg.deleted_at is not null then return jsonb_build_object('ok', true, 'already', true); end if;
    /* 5-minute author grace. Same window KakaoTalk uses so the
       behaviour feels familiar. */
    if msg.created_at < now() - interval '5 minutes' then
        raise exception 'too_old';
    end if;

    update public.direct_messages
       set deleted_at = now(),
           body = null,
           attachment_url = null, attachment_type = null,
           attachment_size = null, attachment_name = null
     where id = p_msg_id;
    return jsonb_build_object('ok', true);
end;
$$;
grant execute on function public.delete_dm(bigint) to authenticated;


-- Delete group message: sender OR room creator can delete. Room
-- creator can moderate content posted by members — matches Discord
-- / Slack "admin removes message" convention.
create or replace function public.delete_group_msg(p_msg_id bigint)
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        msg public.chat_messages%rowtype;
        is_room_creator boolean;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    select * into msg from public.chat_messages where id = p_msg_id;
    if not found then raise exception 'not_found'; end if;
    if msg.deleted_at is not null then return jsonb_build_object('ok', true, 'already', true); end if;

    select (created_by = me) into is_room_creator
      from public.chat_rooms where id = msg.room_id;

    if msg.from_id <> me and not coalesce(is_room_creator, false) then
        raise exception 'not_authorized';
    end if;
    /* 5 min grace ONLY applies to the author; room creators can
       moderate older messages. */
    if msg.from_id = me and not coalesce(is_room_creator, false)
       and msg.created_at < now() - interval '5 minutes' then
        raise exception 'too_old';
    end if;

    update public.chat_messages
       set deleted_at = now(),
           body = null,
           attachment_url = null, attachment_type = null,
           attachment_size = null, attachment_name = null
     where id = p_msg_id;
    return jsonb_build_object('ok', true);
end;
$$;
grant execute on function public.delete_group_msg(bigint) to authenticated;
