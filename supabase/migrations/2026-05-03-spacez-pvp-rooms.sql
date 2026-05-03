-- =====================================================================
-- Migration: Space-Z PvP Rooms (1:1 dodge battle)
-- Date:      2026-05-03
-- Purpose:   호스트가 방을 만들고 게스트가 join 하는 1:1 대결 모드.
--            - 호스트는 방 생성 시 행성당 아이템 개수(1~3)를 선택
--            - 친구 초대 (private room) 또는 공개 방 (lobby 목록)
--            - Realtime broadcast 채널 'spacez:room:<id>' 통해 ping/pong,
--              state(100ms 주기), event(즉시), chat 교환
--            - deterministic seed 로 둘 다 같은 메테오 패턴
--
-- 동기화 모델:
--   각 client 가 같은 seed 로 local 시뮬레이션 → 100ms 마다 상태
--   broadcast (lives/score/zone/time/alive). 입력 동기화 없음 — 1:1
--   parallel survival 라 latency 영향 최소. 채팅과 ping 도 같은 채널로.
--
-- 보안:
--   모든 read 는 SECURITY DEFINER RPC 로만 (모바일 WebView 의 RLS-gated
--   직접 SELECT 무음 실패 이슈 회피 — messaging_rpc_pattern.md 교훈).
--   write 도 RPC — auth.uid() 로 사용자 확인 + 비즈니스 룰 검증.
-- =====================================================================

-- 1. spacez_rooms ── 방 메타데이터 ─────────────────────────────────
create table if not exists public.spacez_rooms (
    id          uuid        primary key default gen_random_uuid(),
    code        text        not null unique check (code ~ '^[A-Z0-9]{6}$'),
    host_id     uuid        not null references auth.users(id) on delete cascade,
    host_name   text        not null,                -- denormalized 닉네임
    item_count  int         not null default 2 check (item_count between 1 and 3),
    seed        bigint      not null,               -- deterministic 메테오 패턴
    is_private  boolean     not null default false, -- true = 친구 초대만 (lobby 목록 제외)
    status      text        not null default 'waiting'
                            check (status in ('waiting','playing','finished','abandoned')),
    created_at  timestamptz not null default now(),
    started_at  timestamptz,
    finished_at timestamptz,
    winner_id   uuid        references auth.users(id)
);
create index if not exists spacez_rooms_lobby_idx
    on public.spacez_rooms (status, created_at desc)
    where status = 'waiting' and is_private = false;
create index if not exists spacez_rooms_host_idx
    on public.spacez_rooms (host_id);
create index if not exists spacez_rooms_code_idx
    on public.spacez_rooms (code)
    where status in ('waiting','playing');

alter table public.spacez_rooms enable row level security;
-- 직접 SELECT 차단 — RPC 로만 read.
drop policy if exists "spacez_rooms_no_direct_select" on public.spacez_rooms;
create policy "spacez_rooms_no_direct_select"
    on public.spacez_rooms for select using (false);


-- 2. spacez_room_members ── 멤버 (host + guest, max 2) ──────────
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


-- 3. spacez_room_messages ── 채팅 (lobby + 게임 중) ─────────────
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
-- RPC: 6자리 join code 생성 (충돌 회피)
-- =====================================================================
create or replace function public._spacez_gen_code()
returns text
language plpgsql
as $$
declare
    v_code text;
    v_attempts int := 0;
begin
    loop
        v_code := upper(substring(md5(random()::text || clock_timestamp()::text), 1, 6));
        -- 코드 중복 검사 — waiting/playing 상태인 방 중에서만 unique 보장
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
-- RPC: spacez_create_room — 호스트가 방 생성
-- =====================================================================
create or replace function public.spacez_create_room(
    p_item_count int,
    p_is_private boolean default false
)
returns table (
    room_id  uuid,
    code     text,
    seed     bigint
)
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user_id  uuid := auth.uid();
    v_nickname text;
    v_room_id  uuid;
    v_code     text;
    v_seed     bigint;
begin
    if v_user_id is null then
        raise exception 'auth_required';
    end if;
    if p_item_count < 1 or p_item_count > 3 then
        raise exception 'invalid_item_count';
    end if;
    -- 닉네임 fetch (display_name 우선, fallback email prefix)
    select coalesce(
            nullif(raw_user_meta_data->>'display_name',''),
            split_part(coalesce(email,''), '@', 1),
            'Player'
        )
    into v_nickname
    from auth.users where id = v_user_id;
    -- 사용자가 이미 활성 방 보유? 자동 정리 (abandoned 처리 후 새로 생성)
    update public.spacez_rooms
       set status = 'abandoned', finished_at = now()
     where host_id = v_user_id and status in ('waiting','playing');
    -- 새 코드 + seed 생성
    v_code := public._spacez_gen_code();
    v_seed := floor(random() * 1e15)::bigint;
    -- 방 + 호스트 멤버 record
    insert into public.spacez_rooms (code, host_id, host_name, item_count, seed, is_private)
    values (v_code, v_user_id, v_nickname, p_item_count, v_seed, p_is_private)
    returning id into v_room_id;
    insert into public.spacez_room_members (room_id, user_id, nickname, role)
    values (v_room_id, v_user_id, v_nickname, 'host');
    return query select v_room_id, v_code, v_seed;
end;
$$;
revoke all on function public.spacez_create_room(int, boolean) from public;
grant execute on function public.spacez_create_room(int, boolean) to authenticated;


-- =====================================================================
-- RPC: spacez_join_room — 게스트가 코드로 방 join
-- =====================================================================
create or replace function public.spacez_join_room(p_code text)
returns table (
    room_id     uuid,
    seed        bigint,
    item_count  int,
    host_id     uuid,
    host_name   text
)
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user_id  uuid := auth.uid();
    v_nickname text;
    v_room     record;
    v_member_count int;
begin
    if v_user_id is null then
        raise exception 'auth_required';
    end if;
    -- 닉네임 fetch
    select coalesce(
            nullif(raw_user_meta_data->>'display_name',''),
            split_part(coalesce(email,''), '@', 1),
            'Player'
        )
    into v_nickname
    from auth.users where id = v_user_id;
    -- 코드로 방 찾기 (waiting 상태만)
    select * into v_room
    from public.spacez_rooms
    where code = upper(p_code) and status = 'waiting';
    if not found then
        raise exception 'room_not_found';
    end if;
    if v_room.host_id = v_user_id then
        raise exception 'cannot_join_own_room';
    end if;
    -- 정원 (2명) 검사
    select count(*) into v_member_count
    from public.spacez_room_members where room_id = v_room.id;
    if v_member_count >= 2 then
        raise exception 'room_full';
    end if;
    -- guest 멤버 추가 (idempotent — 중복 시 join_at 만 update)
    insert into public.spacez_room_members (room_id, user_id, nickname, role)
    values (v_room.id, v_user_id, v_nickname, 'guest')
    on conflict (room_id, user_id) do update
        set nickname = excluded.nickname,
            joined_at = now();
    return query select v_room.id, v_room.seed, v_room.item_count, v_room.host_id, v_room.host_name;
end;
$$;
revoke all on function public.spacez_join_room(text) from public;
grant execute on function public.spacez_join_room(text) to authenticated;


-- =====================================================================
-- RPC: spacez_leave_room — 멤버 나감 (host 면 방 abandoned)
-- =====================================================================
create or replace function public.spacez_leave_room(p_room_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user_id uuid := auth.uid();
    v_role    text;
begin
    if v_user_id is null then
        raise exception 'auth_required';
    end if;
    select role into v_role
    from public.spacez_room_members
    where room_id = p_room_id and user_id = v_user_id;
    if not found then
        return;   -- 이미 안 들어있음, no-op
    end if;
    -- 멤버 row 삭제
    delete from public.spacez_room_members
    where room_id = p_room_id and user_id = v_user_id;
    -- host 가 나가면 방 자체 abandoned
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
-- RPC: spacez_list_rooms — public 대기실 목록 (랭킹 카드 스타일)
-- =====================================================================
create or replace function public.spacez_list_rooms()
returns table (
    room_id      uuid,
    code         text,
    host_name    text,
    item_count   int,
    member_count int,
    created_at   timestamptz
)
language sql
security definer
set search_path = public
stable
as $$
    select r.id, r.code, r.host_name, r.item_count,
           (select count(*) from public.spacez_room_members where room_id = r.id)::int,
           r.created_at
      from public.spacez_rooms r
     where r.status = 'waiting' and r.is_private = false
       -- 5분 이상 묵혀진 방은 제외 (host 가 잠수)
       and r.created_at > now() - interval '5 minutes'
     order by r.created_at desc
     limit 30;
$$;
revoke all on function public.spacez_list_rooms() from public;
grant execute on function public.spacez_list_rooms() to authenticated;


-- =====================================================================
-- RPC: spacez_get_room — 특정 방 + 멤버 정보
-- =====================================================================
create or replace function public.spacez_get_room(p_room_id uuid)
returns table (
    room_id     uuid,
    code        text,
    host_id     uuid,
    item_count  int,
    seed        bigint,
    is_private  boolean,
    status      text,
    members     jsonb
)
language plpgsql
security definer
set search_path = public
stable
as $$
declare
    v_user_id uuid := auth.uid();
begin
    if v_user_id is null then
        raise exception 'auth_required';
    end if;
    -- 방 멤버 만 가져옴 (보안)
    if not exists (
        select 1 from public.spacez_room_members
        where room_id = p_room_id and user_id = v_user_id
    ) then
        raise exception 'not_a_member';
    end if;
    return query
    select r.id, r.code, r.host_id, r.item_count, r.seed, r.is_private, r.status,
           coalesce((
               select jsonb_agg(jsonb_build_object(
                   'user_id',  m.user_id,
                   'nickname', m.nickname,
                   'role',     m.role,
                   'is_ready', m.is_ready,
                   'joined_at', m.joined_at
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
-- RPC: spacez_set_ready — 멤버 준비 토글
-- =====================================================================
create or replace function public.spacez_set_ready(p_room_id uuid, p_ready boolean)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user_id uuid := auth.uid();
begin
    if v_user_id is null then
        raise exception 'auth_required';
    end if;
    update public.spacez_room_members
       set is_ready = p_ready
     where room_id = p_room_id and user_id = v_user_id;
    if not found then
        raise exception 'not_a_member';
    end if;
end;
$$;
revoke all on function public.spacez_set_ready(uuid, boolean) from public;
grant execute on function public.spacez_set_ready(uuid, boolean) to authenticated;


-- =====================================================================
-- RPC: spacez_start_game — 호스트가 게임 시작 (양쪽 ready 검증)
-- =====================================================================
create or replace function public.spacez_start_game(p_room_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user_id uuid := auth.uid();
    v_room    record;
    v_ready_count int;
begin
    if v_user_id is null then
        raise exception 'auth_required';
    end if;
    select * into v_room from public.spacez_rooms
    where id = p_room_id and host_id = v_user_id and status = 'waiting';
    if not found then
        raise exception 'not_host_or_invalid_state';
    end if;
    -- 양쪽 다 ready 인지 검증
    select count(*) into v_ready_count
    from public.spacez_room_members
    where room_id = p_room_id and is_ready = true;
    if v_ready_count < 2 then
        raise exception 'not_all_ready';
    end if;
    update public.spacez_rooms
       set status = 'playing', started_at = now()
     where id = p_room_id;
end;
$$;
revoke all on function public.spacez_start_game(uuid) from public;
grant execute on function public.spacez_start_game(uuid) to authenticated;


-- =====================================================================
-- RPC: spacez_finish_game — 게임 결과 보고 (각 player 가 호출)
--   양쪽 모두 결과 보고하면 winner 결정 + status='finished'.
-- =====================================================================
create or replace function public.spacez_finish_game(
    p_room_id      uuid,
    p_score        int,
    p_duration_ms  int
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user_id uuid := auth.uid();
    v_finished_count int;
    v_winner uuid;
begin
    if v_user_id is null then
        raise exception 'auth_required';
    end if;
    -- 자기 결과 기록
    update public.spacez_room_members
       set final_score = p_score, final_time_ms = p_duration_ms
     where room_id = p_room_id and user_id = v_user_id
       and final_score is null;
    -- 양쪽 모두 보고 완료?
    select count(*) into v_finished_count
    from public.spacez_room_members
    where room_id = p_room_id and final_score is not null;
    if v_finished_count >= 2 then
        -- winner 결정 — score 큰 쪽, tie 면 time 짧은 쪽
        select user_id into v_winner
        from public.spacez_room_members
        where room_id = p_room_id
        order by final_score desc nulls last, final_time_ms asc nulls last
        limit 1;
        update public.spacez_rooms
           set status = 'finished', finished_at = now(), winner_id = v_winner
         where id = p_room_id;
    end if;
end;
$$;
revoke all on function public.spacez_finish_game(uuid, int, int) from public;
grant execute on function public.spacez_finish_game(uuid, int, int) to authenticated;


-- =====================================================================
-- RPC: spacez_send_message — 채팅
-- =====================================================================
create or replace function public.spacez_send_message(p_room_id uuid, p_msg text)
returns bigint
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user_id  uuid := auth.uid();
    v_member   record;
    v_msg_id   bigint;
begin
    if v_user_id is null then
        raise exception 'auth_required';
    end if;
    select * into v_member from public.spacez_room_members
    where room_id = p_room_id and user_id = v_user_id;
    if not found then
        raise exception 'not_a_member';
    end if;
    if length(trim(p_msg)) = 0 then
        raise exception 'empty_message';
    end if;
    insert into public.spacez_room_messages (room_id, user_id, nickname, msg)
    values (p_room_id, v_user_id, v_member.nickname, left(trim(p_msg), 200))
    returning id into v_msg_id;
    return v_msg_id;
end;
$$;
revoke all on function public.spacez_send_message(uuid, text) from public;
grant execute on function public.spacez_send_message(uuid, text) to authenticated;


-- =====================================================================
-- RPC: spacez_get_messages — 채팅 history (최근 50개)
-- =====================================================================
create or replace function public.spacez_get_messages(p_room_id uuid)
returns table (
    id          bigint,
    user_id     uuid,
    nickname    text,
    msg         text,
    created_at  timestamptz
)
language plpgsql
security definer
set search_path = public
stable
as $$
declare
    v_user_id uuid := auth.uid();
begin
    if v_user_id is null then
        raise exception 'auth_required';
    end if;
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
-- 정리: 5분 이상 묵힌 waiting room 자동 abandoned 처리하는 cron 비슷한
-- 효과는 _list_rooms 에서 already filtered. 별도 cleanup 함수는 나중에
-- 필요하면 추가 (Supabase pg_cron extension 활용).
-- =====================================================================
