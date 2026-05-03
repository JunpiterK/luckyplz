-- =====================================================================
-- Migration: Space-Z PvP Rooms (1:1 dodge battle)
-- Date:      2026-05-03
-- Purpose:   1:1 대결 — 호스트 방 생성 → 게스트 lobby 목록에서 직접 join.
--            기본 public (목록 노출) / private (비밀번호 요구).
--
-- 모델:
--   · spacez_rooms — 방 메타 (code, host, item_count(1-3), seed, password_hash, ...)
--   · spacez_room_members — 멤버 (host + guest, max 2)
--   · spacez_room_messages — 채팅
-- 동기화: Supabase Realtime broadcast 'spacez:room:<id>' 채널 (state/event/chat/ping).
-- 보안: 모든 read 는 SECURITY DEFINER RPC. RLS 직접 SELECT 차단.
-- 비번: pgcrypto 의 crypt() + bf salt — Supabase 기본 활성.
--
-- IDEMPOTENT: 재실행 시 안전 (IF NOT EXISTS / OR REPLACE / DROP IF EXISTS).
-- =====================================================================

create extension if not exists pgcrypto;

-- 1. spacez_rooms ──────────────────────────────────────────────────
create table if not exists public.spacez_rooms (
    id          uuid        primary key default gen_random_uuid(),
    code        text        not null unique check (code ~ '^[A-Z0-9]{6}$'),
    host_id     uuid        not null references auth.users(id) on delete cascade,
    host_name   text        not null,
    item_count  int         not null default 2 check (item_count between 1 and 3),
    seed        bigint      not null,
    is_private  boolean     not null default false,
    password_hash text       default null,            -- private 방 비번 해시 (bf)
    status      text        not null default 'waiting'
                            check (status in ('waiting','playing','finished','abandoned')),
    created_at  timestamptz not null default now(),
    started_at  timestamptz,
    finished_at timestamptz,
    winner_id   uuid        references auth.users(id)
);
-- 컬럼 idempotent 추가 (이미 있으면 무시)
alter table public.spacez_rooms add column if not exists password_hash text;

create index if not exists spacez_rooms_lobby_idx
    on public.spacez_rooms (status, created_at desc)
    where status = 'waiting';
create index if not exists spacez_rooms_host_idx
    on public.spacez_rooms (host_id);
create index if not exists spacez_rooms_code_idx
    on public.spacez_rooms (code)
    where status in ('waiting','playing');

alter table public.spacez_rooms enable row level security;
drop policy if exists "spacez_rooms_no_direct_select" on public.spacez_rooms;
create policy "spacez_rooms_no_direct_select"
    on public.spacez_rooms for select using (false);


-- 2. spacez_room_members ───────────────────────────────────────────
create table if not exists public.spacez_room_members (
    room_id        uuid        not null references public.spacez_rooms(id) on delete cascade,
    user_id        uuid        not null references auth.users(id) on delete cascade,
    nickname       text        not null,
    role           text        not null check (role in ('host','guest')),
    is_ready       boolean     not null default false,
    joined_at      timestamptz not null default now(),
    final_score    int,
    final_time_ms  int,
    primary key (room_id, user_id)
);
create index if not exists spacez_members_room_idx on public.spacez_room_members (room_id);
create index if not exists spacez_members_user_idx on public.spacez_room_members (user_id);
alter table public.spacez_room_members enable row level security;
drop policy if exists "spacez_members_no_direct_select" on public.spacez_room_members;
create policy "spacez_members_no_direct_select"
    on public.spacez_room_members for select using (false);


-- 3. spacez_room_messages ──────────────────────────────────────────
create table if not exists public.spacez_room_messages (
    id          bigserial   primary key,
    room_id     uuid        not null references public.spacez_rooms(id) on delete cascade,
    user_id     uuid        not null references auth.users(id) on delete cascade,
    nickname    text        not null,
    msg         text        not null check (length(msg) between 1 and 200),
    created_at  timestamptz not null default now()
);
create index if not exists spacez_msg_room_idx on public.spacez_room_messages (room_id, created_at);
alter table public.spacez_room_messages enable row level security;
drop policy if exists "spacez_messages_no_direct_select" on public.spacez_room_messages;
create policy "spacez_messages_no_direct_select"
    on public.spacez_room_messages for select using (false);


-- =====================================================================
-- _spacez_gen_code: 6자리 join code (충돌 회피, URL 공유용)
-- =====================================================================
create or replace function public._spacez_gen_code()
returns text
language plpgsql
as $$
#variable_conflict use_column
declare
    v_code text;
    v_attempts int := 0;
begin
    loop
        v_code := upper(substring(md5(random()::text || clock_timestamp()::text), 1, 6));
        if not exists (
            select 1 from public.spacez_rooms
            where code = v_code and status in ('waiting','playing')
        ) then
            return v_code;
        end if;
        v_attempts := v_attempts + 1;
        if v_attempts > 50 then
            raise exception 'code_generation_failed';
        end if;
    end loop;
end;
$$;


-- =====================================================================
-- spacez_create_room — public 또는 private (비번 hashed) 방 생성
-- =====================================================================
drop function if exists public.spacez_create_room(int, boolean);
drop function if exists public.spacez_create_room(int, boolean, text);
create or replace function public.spacez_create_room(
    p_item_count int,
    p_is_private boolean default false,
    p_password   text    default null
)
returns table (
    room_id uuid,
    code    text,
    seed    bigint
)
language plpgsql
security definer
set search_path = public
as $$
#variable_conflict use_column
declare
    v_user_id  uuid := auth.uid();
    v_nickname text;
    v_room_id  uuid;
    v_code     text;
    v_seed     bigint;
    v_pw_hash  text;
begin
    if v_user_id is null then
        raise exception 'auth_required';
    end if;
    if p_item_count < 1 or p_item_count > 3 then
        raise exception 'invalid_item_count';
    end if;
    -- private 방은 비밀번호 필수 (4-30자)
    if p_is_private then
        if p_password is null or length(trim(p_password)) < 4 or length(p_password) > 30 then
            raise exception 'invalid_password';
        end if;
        v_pw_hash := crypt(p_password, gen_salt('bf', 8));
    else
        v_pw_hash := null;
    end if;
    -- 닉네임 fetch (profiles 우선, fallback email prefix)
    select coalesce(
            nullif(p.nickname,''),
            nullif(u.raw_user_meta_data->>'display_name',''),
            split_part(coalesce(u.email,''), '@', 1),
            'Player'
        )
    into v_nickname
    from auth.users u
    left join public.profiles p on p.id = u.id
    where u.id = v_user_id;
    -- 기존 활성 방 정리
    update public.spacez_rooms
       set status = 'abandoned', finished_at = now()
     where host_id = v_user_id and status in ('waiting','playing');
    -- 새 방
    v_code := public._spacez_gen_code();
    v_seed := floor(random() * 1e15)::bigint;
    insert into public.spacez_rooms
        (code, host_id, host_name, item_count, seed, is_private, password_hash)
    values
        (v_code, v_user_id, v_nickname, p_item_count, v_seed, p_is_private, v_pw_hash)
    returning id into v_room_id;
    insert into public.spacez_room_members (room_id, user_id, nickname, role)
    values (v_room_id, v_user_id, v_nickname, 'host');
    return query select v_room_id, v_code, v_seed;
end;
$$;
revoke all on function public.spacez_create_room(int, boolean, text) from public;
grant execute on function public.spacez_create_room(int, boolean, text) to authenticated;


-- =====================================================================
-- spacez_join_room_by_id — 방 목록에서 직접 join (private 면 비번 검사)
-- =====================================================================
drop function if exists public.spacez_join_room_by_id(uuid, text);
create or replace function public.spacez_join_room_by_id(
    p_room_id  uuid,
    p_password text default null
)
returns table (
    room_id     uuid,
    code        text,
    seed        bigint,
    item_count  int,
    host_id     uuid,
    host_name   text
)
language plpgsql
security definer
set search_path = public
as $$
#variable_conflict use_column
declare
    v_user_id  uuid := auth.uid();
    v_nickname text;
    v_room     record;
    v_member_count int;
begin
    if v_user_id is null then
        raise exception 'auth_required';
    end if;
    select * into v_room
    from public.spacez_rooms
    where id = p_room_id and status = 'waiting';
    if not found then
        raise exception 'room_not_found';
    end if;
    if v_room.host_id = v_user_id then
        raise exception 'cannot_join_own_room';
    end if;
    -- private 비번 검증
    if v_room.is_private then
        if p_password is null or v_room.password_hash is null
            or crypt(p_password, v_room.password_hash) <> v_room.password_hash then
            raise exception 'invalid_password';
        end if;
    end if;
    -- 정원
    select count(*) into v_member_count
    from public.spacez_room_members where room_id = v_room.id;
    -- 이미 멤버인지 확인 (rejoin OK)
    if not exists (
        select 1 from public.spacez_room_members
        where room_id = v_room.id and user_id = v_user_id
    ) then
        if v_member_count >= 2 then
            raise exception 'room_full';
        end if;
    end if;
    -- 닉네임
    select coalesce(
            nullif(p.nickname,''),
            nullif(u.raw_user_meta_data->>'display_name',''),
            split_part(coalesce(u.email,''), '@', 1),
            'Player'
        )
    into v_nickname
    from auth.users u
    left join public.profiles p on p.id = u.id
    where u.id = v_user_id;
    insert into public.spacez_room_members (room_id, user_id, nickname, role)
    values (v_room.id, v_user_id, v_nickname, 'guest')
    on conflict (room_id, user_id) do update
        set nickname = excluded.nickname, joined_at = now();
    return query select v_room.id, v_room.code, v_room.seed,
                        v_room.item_count, v_room.host_id, v_room.host_name;
end;
$$;
revoke all on function public.spacez_join_room_by_id(uuid, text) from public;
grant execute on function public.spacez_join_room_by_id(uuid, text) to authenticated;


-- =====================================================================
-- spacez_join_room — 코드로 join (URL 공유 / private 직접 입장 옵션)
-- =====================================================================
drop function if exists public.spacez_join_room(text);
drop function if exists public.spacez_join_room(text, text);
create or replace function public.spacez_join_room(
    p_code     text,
    p_password text default null
)
returns table (
    room_id     uuid,
    code        text,
    seed        bigint,
    item_count  int,
    host_id     uuid,
    host_name   text
)
language plpgsql
security definer
set search_path = public
as $$
#variable_conflict use_column
declare
    v_room_id uuid;
begin
    select id into v_room_id from public.spacez_rooms
    where code = upper(p_code) and status = 'waiting';
    if not found then
        raise exception 'room_not_found';
    end if;
    return query select * from public.spacez_join_room_by_id(v_room_id, p_password);
end;
$$;
revoke all on function public.spacez_join_room(text, text) from public;
grant execute on function public.spacez_join_room(text, text) to authenticated;


-- =====================================================================
-- spacez_leave_room
-- =====================================================================
create or replace function public.spacez_leave_room(p_room_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
#variable_conflict use_column
declare
    v_user_id uuid := auth.uid();
    v_role    text;
begin
    if v_user_id is null then raise exception 'auth_required'; end if;
    select role into v_role from public.spacez_room_members
    where room_id = p_room_id and user_id = v_user_id;
    if not found then return; end if;
    delete from public.spacez_room_members
    where room_id = p_room_id and user_id = v_user_id;
    if v_role = 'host' then
        update public.spacez_rooms
           set status = 'abandoned', finished_at = now()
         where id = p_room_id and status in ('waiting','playing');
    end if;
end;
$$;
revoke all on function public.spacez_leave_room(uuid) from public;
grant execute on function public.spacez_leave_room(uuid) to authenticated;


-- =====================================================================
-- spacez_list_rooms — public + private 모두 표시 (private 은 자물쇠 + 비번 요구).
-- 추가 필드: room_id, host_id, has_password, is_private — UI 에서 카드 직접 join.
-- =====================================================================
drop function if exists public.spacez_list_rooms();
create or replace function public.spacez_list_rooms()
returns table (
    room_id      uuid,
    code         text,
    host_id      uuid,
    host_name    text,
    item_count   int,
    is_private   boolean,
    has_password boolean,
    member_count int,
    created_at   timestamptz
)
language sql
security definer
set search_path = public
stable
as $$
    select r.id, r.code, r.host_id, r.host_name, r.item_count, r.is_private,
           (r.password_hash is not null) as has_password,
           (select count(*) from public.spacez_room_members where room_id = r.id)::int,
           r.created_at
      from public.spacez_rooms r
     where r.status = 'waiting'
       and r.created_at > now() - interval '5 minutes'
     order by r.is_private asc, r.created_at desc
     limit 30;
$$;
revoke all on function public.spacez_list_rooms() from public;
grant execute on function public.spacez_list_rooms() to authenticated;


-- =====================================================================
-- spacez_get_room — 멤버만 호출 가능
-- =====================================================================
drop function if exists public.spacez_get_room(uuid);
create or replace function public.spacez_get_room(p_room_id uuid)
returns table (
    room_id     uuid,
    code        text,
    host_id     uuid,
    item_count  int,
    seed        bigint,
    is_private  boolean,
    status      text,
    winner_id   uuid,    -- 게임 끝나면 winner. 안 끝났으면 null. 클라가 polling 으로 사용.
    members     jsonb    -- final_score / final_time_ms 도 포함 (점수 비교용).
)
language plpgsql
security definer
set search_path = public
stable
as $$
#variable_conflict use_column
declare
    v_user_id uuid := auth.uid();
begin
    if v_user_id is null then raise exception 'auth_required'; end if;
    if not exists (
        select 1 from public.spacez_room_members
        where room_id = p_room_id and user_id = v_user_id
    ) then
        raise exception 'not_a_member';
    end if;
    return query
    select r.id, r.code, r.host_id, r.item_count, r.seed, r.is_private, r.status, r.winner_id,
           coalesce((
               select jsonb_agg(jsonb_build_object(
                   'user_id',       m.user_id,
                   'nickname',      m.nickname,
                   'role',          m.role,
                   'is_ready',      m.is_ready,
                   'joined_at',     m.joined_at,
                   'final_score',   m.final_score,
                   'final_time_ms', m.final_time_ms
               ) order by m.joined_at)
               from public.spacez_room_members m
               where m.room_id = r.id
           ), '[]'::jsonb)
      from public.spacez_rooms r
     where r.id = p_room_id;
end;
$$;
revoke all on function public.spacez_get_room(uuid) from public;
grant execute on function public.spacez_get_room(uuid) to authenticated;


-- =====================================================================
-- spacez_set_ready / spacez_start_game / spacez_finish_game
-- =====================================================================
create or replace function public.spacez_set_ready(p_room_id uuid, p_ready boolean)
returns void
language plpgsql security definer set search_path = public
as $$
#variable_conflict use_column
declare v_user_id uuid := auth.uid();
begin
    if v_user_id is null then raise exception 'auth_required'; end if;
    update public.spacez_room_members
       set is_ready = p_ready
     where room_id = p_room_id and user_id = v_user_id;
    if not found then raise exception 'not_a_member'; end if;
end;
$$;
revoke all on function public.spacez_set_ready(uuid, boolean) from public;
grant execute on function public.spacez_set_ready(uuid, boolean) to authenticated;

drop function if exists public.spacez_start_game(uuid);
create or replace function public.spacez_start_game(p_room_id uuid)
returns bigint   /* return new seed — host 가 receive 후 broadcast 'game_start' payload 로 사용 */
language plpgsql security definer set search_path = public
as $$
#variable_conflict use_column
declare
    v_user_id uuid := auth.uid();
    v_ready_count int;
    v_room record;
    v_seed bigint;
begin
    if v_user_id is null then raise exception 'auth_required'; end if;
    select * into v_room from public.spacez_rooms
    where id = p_room_id and host_id = v_user_id;
    if not found then raise exception 'not_host_or_invalid_state'; end if;
    /* 'waiting' (첫 게임) 또는 'finished' (rematch) 상태에서만 시작 가능. */
    if v_room.status not in ('waiting', 'finished') then
        raise exception 'invalid_state';
    end if;
    select count(*) into v_ready_count
    from public.spacez_room_members
    where room_id = p_room_id and is_ready = true;
    if v_ready_count < 2 then raise exception 'not_all_ready'; end if;
    /* rematch — 멤버 final_score/time reset, 새 seed 생성. */
    if v_room.status = 'finished' then
        update public.spacez_room_members
           set final_score = null, final_time_ms = null
         where room_id = p_room_id;
        v_seed := floor(random() * 1e15)::bigint;
        update public.spacez_rooms
           set seed = v_seed, winner_id = null, finished_at = null
         where id = p_room_id;
    else
        v_seed := v_room.seed;
    end if;
    update public.spacez_rooms
       set status = 'playing', started_at = now()
     where id = p_room_id;
    return v_seed;
end;
$$;
revoke all on function public.spacez_start_game(uuid) from public;
grant execute on function public.spacez_start_game(uuid) to authenticated;

create or replace function public.spacez_finish_game(
    p_room_id uuid, p_score int, p_duration_ms int
)
returns void
language plpgsql security definer set search_path = public
as $$
#variable_conflict use_column
declare
    v_user_id uuid := auth.uid();
    v_finished_count int;
    v_winner uuid;
begin
    if v_user_id is null then raise exception 'auth_required'; end if;
    update public.spacez_room_members
       set final_score = p_score, final_time_ms = p_duration_ms
     where room_id = p_room_id and user_id = v_user_id and final_score is null;
    select count(*) into v_finished_count
    from public.spacez_room_members
    where room_id = p_room_id and final_score is not null;
    if v_finished_count >= 2 then
        /* tiebreaker: 동률 점수 시 더 오래 산 쪽 (final_time_ms desc) 우승.
           이전 asc 는 짧게 산 쪽이 win 되는 버그였음. */
        select user_id into v_winner
        from public.spacez_room_members
        where room_id = p_room_id
        order by final_score desc nulls last, final_time_ms desc nulls last
        limit 1;
        update public.spacez_rooms
           set status = 'finished', finished_at = now(), winner_id = v_winner
         where id = p_room_id;
        /* rematch 위해 양쪽 is_ready 자동 reset — 다음 게임 시작 시 양쪽
           [준비] 다시 눌러야 함. */
        update public.spacez_room_members
           set is_ready = false
         where room_id = p_room_id;
    end if;
end;
$$;
revoke all on function public.spacez_finish_game(uuid, int, int) from public;
grant execute on function public.spacez_finish_game(uuid, int, int) to authenticated;


-- =====================================================================
-- 채팅 RPC
-- =====================================================================
create or replace function public.spacez_send_message(p_room_id uuid, p_msg text)
returns bigint
language plpgsql security definer set search_path = public
as $$
#variable_conflict use_column
declare
    v_user_id uuid := auth.uid();
    v_member  record;
    v_msg_id  bigint;
begin
    if v_user_id is null then raise exception 'auth_required'; end if;
    select * into v_member from public.spacez_room_members
    where room_id = p_room_id and user_id = v_user_id;
    if not found then raise exception 'not_a_member'; end if;
    if length(trim(p_msg)) = 0 then raise exception 'empty_message'; end if;
    insert into public.spacez_room_messages (room_id, user_id, nickname, msg)
    values (p_room_id, v_user_id, v_member.nickname, left(trim(p_msg), 200))
    returning id into v_msg_id;
    return v_msg_id;
end;
$$;
revoke all on function public.spacez_send_message(uuid, text) from public;
grant execute on function public.spacez_send_message(uuid, text) to authenticated;

create or replace function public.spacez_get_messages(p_room_id uuid)
returns table (
    id          bigint,
    user_id     uuid,
    nickname    text,
    msg         text,
    created_at  timestamptz
)
language plpgsql security definer set search_path = public stable
as $$
#variable_conflict use_column
declare v_user_id uuid := auth.uid();
begin
    if v_user_id is null then raise exception 'auth_required'; end if;
    if not exists (
        select 1 from public.spacez_room_members
        where room_id = p_room_id and user_id = v_user_id
    ) then
        raise exception 'not_a_member';
    end if;
    return query
    select m.id, m.user_id, m.nickname, m.msg, m.created_at
      from public.spacez_room_messages m
     where m.room_id = p_room_id
     order by m.created_at desc
     limit 50;
end;
$$;
revoke all on function public.spacez_get_messages(uuid) from public;
grant execute on function public.spacez_get_messages(uuid) to authenticated;


-- =====================================================================
-- spacez_user_winloss — 사용자 1:1 승/패 (placeholder, 나중 확장).
-- 현재는 finished room 의 winner 기준 단순 집계.
-- =====================================================================
drop function if exists public.spacez_user_winloss(uuid);
create or replace function public.spacez_user_winloss(p_user_id uuid)
returns table (wins int, losses int)
language sql security definer set search_path = public stable
as $$
    with played as (
        select r.id, r.winner_id, r.host_id,
               case when m.user_id = r.winner_id then 1 else 0 end as won,
               case when m.user_id <> r.winner_id then 1 else 0 end as lost
          from public.spacez_room_members m
          join public.spacez_rooms r on r.id = m.room_id
         where m.user_id = p_user_id and r.status = 'finished' and r.winner_id is not null
    )
    select coalesce(sum(won),0)::int, coalesce(sum(lost),0)::int from played;
$$;
revoke all on function public.spacez_user_winloss(uuid) from public;
grant execute on function public.spacez_user_winloss(uuid) to authenticated;
