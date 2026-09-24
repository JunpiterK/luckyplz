-- =====================================================================
-- Migration: Live Quiz v2 — 서버가 진행하는 라이브 퀴즈 (2026-09-24)
--
-- 운영자: "안정성과 신뢰성이 가장 중요. 튕겨도 언제든 쉽게 다시 참석."
--
-- v1(lpRoom 브로드캐스트)은 호스트 브라우저가 게임 상태를 전부 들고 있었다.
-- 호스트 폰이 잠들거나 끊기면 방이 멈추고, 참가자가 새로고침하면 PIN 인증부터
-- 다시 해야 했으며, 답안은 유실될 수 있는 브로드캐스트로 호스트에게 갔다.
--
-- v2 는 DB 가 유일한 진실원천이다.
--   · 진행은 서버 시각 기준 "시간표"(phase + ends_at). 누구든 qlive_state 를 부르면
--     기한이 지난 단계를 서버가 넘긴다 → 호스트가 사라져도 게임은 끝까지 간다
--   · 답안은 (방, 문제, 참가자) 기본키 — 몇 번을 다시 보내도 한 번만 기록(멱등)
--   · 점수·연속 정답은 서버가 서버 시각으로 계산 — 폰 시계·지연과 무관
--   · 참가자 신원 = 기기에 저장된 pid(uuid). 같은 pid 로 다시 들어오면 점수 그대로 복귀
--   · 테이블은 RLS 로 전부 막고 SECURITY DEFINER RPC 로만 접근
--     (카카오톡 인앱에서 RLS 걸린 직접 SELECT 가 무음 실패하던 교훈)
--   · 실시간 채널은 "상태가 바뀌었다"는 알림만 — 놓쳐도 폴링이 받는다
-- =====================================================================

create table if not exists public.qlive_rooms (
    code           text        primary key check (code ~ '^[0-9]{6}$'),
    host_key       uuid        not null,
    lang           text        not null default 'ko',
    questions      jsonb       not null,
    total          int         not null check (total between 1 and 60),
    settings       jsonb       not null default '{}'::jsonb,
    phase          text        not null default 'lobby'
                   check (phase in ('lobby','intro','question','reveal','board','final')),
    q_index        int         not null default -1,
    phase_at       timestamptz not null default now(),
    ends_at        timestamptz,
    paused_left_ms int,
    locked         boolean     not null default false,
    rev            bigint      not null default 0,
    host_seen      timestamptz not null default now(),
    started_at     timestamptz,
    created_at     timestamptz not null default now()
);
create index if not exists qlive_rooms_created_idx on public.qlive_rooms (created_at);

create table if not exists public.qlive_players (
    code        text        not null references public.qlive_rooms(code) on delete cascade,
    pid         uuid        not null,
    nick        text        not null,
    avatar      text,
    score       int         not null default 0,
    streak      int         not null default 0,
    best_streak int         not null default 0,
    n_correct   int         not null default 0,
    kicked      boolean     not null default false,
    joined_at   timestamptz not null default now(),
    seen_at     timestamptz not null default now(),
    primary key (code, pid)
);
create unique index if not exists qlive_players_nick_uq on public.qlive_players (code, lower(nick));

create table if not exists public.qlive_answers (
    code    text        not null,
    q       int         not null,
    pid     uuid        not null,
    choice  int         not null,
    ms      int         not null,
    ok      boolean     not null,
    pts     int         not null,
    at      timestamptz not null default now(),
    primary key (code, q, pid),
    foreign key (code, pid) references public.qlive_players (code, pid) on delete cascade
);

alter table public.qlive_rooms   enable row level security;
alter table public.qlive_players enable row level security;
alter table public.qlive_answers enable row level security;
revoke all on public.qlive_rooms, public.qlive_players, public.qlive_answers from anon, authenticated;


-- ─── 내부: 설정값 ───
create or replace function public._qlive_ms(s jsonb, k text, dflt int)
returns int language sql immutable as $$
    select coalesce(nullif(s->>k,'')::int, dflt)
$$;

-- ─── 내부: 기한 지난 단계를 넘긴다 (행 잠금 상태에서 호출) ───
-- 호스트가 25초 넘게 안 보이면 수동 진행 방도 자동으로 넘긴다(방이 멈추지 않게).
-- 일시정지는 호스트가 90초 넘게 안 보이면 풀린다.
create or replace function public._qlive_advance(p_code text)
returns void language plpgsql security definer set search_path = public as $$
declare
    r        public.qlive_rooms%rowtype;
    qms      int; intro int; rev_ms int; board int; auto boolean;
    due      timestamptz; hostgone boolean; guard int := 0;
begin
    loop
        guard := guard + 1; exit when guard > 8;
        -- 잠그지 않고 먼저 본다 — 폴링 수백 번이 한 행 잠금에 줄 서지 않게. 넘길 게 있을 때만 잠근다
        select * into r from public.qlive_rooms where code = p_code;
        if not found then return; end if;
        if r.paused_left_ms is null and r.phase not in ('lobby','final') then
            due := r.ends_at;
            if due is null and now() - r.host_seen > interval '25 seconds' and r.phase in ('reveal','board') then due := r.phase_at; end if;
            if due is null or now() < due then return; end if;
        elsif r.paused_left_ms is not null and now() - r.host_seen <= interval '90 seconds' then
            return;
        elsif r.phase in ('lobby','final') then
            return;
        end if;
        select * into r from public.qlive_rooms where code = p_code for update;
        if not found then return; end if;
        qms    := public._qlive_ms(r.settings,'qsec',20) * 1000;
        intro  := public._qlive_ms(r.settings,'intro_ms',3500);
        rev_ms := public._qlive_ms(r.settings,'reveal_ms',5500);
        board  := public._qlive_ms(r.settings,'board_ms',5500);
        auto   := coalesce((r.settings->>'auto')::boolean, true);
        hostgone := now() - r.host_seen > interval '25 seconds';

        if r.paused_left_ms is not null then
            if now() - r.host_seen > interval '90 seconds' then
                update public.qlive_rooms set ends_at = now() + make_interval(secs => r.paused_left_ms/1000.0),
                       paused_left_ms = null, rev = rev + 1 where code = p_code;
                continue;
            end if;
            return;
        end if;

        due := r.ends_at;
        if due is null and hostgone and r.phase in ('reveal','board') then
            due := r.phase_at + make_interval(secs => (case when r.phase='reveal' then rev_ms else board end)/1000.0);
        end if;
        -- 문제 단계는 0.4초 유예(지연 도착 답안을 받기 위해)
        if r.phase = 'question' and due is not null then due := due + interval '400 milliseconds'; end if;
        exit when due is null or now() < due;

        if r.phase = 'intro' then
            update public.qlive_rooms set phase='question', phase_at=now(),
                   ends_at = now() + make_interval(secs => qms/1000.0), rev = rev + 1 where code = p_code;
        elsif r.phase = 'question' then
            -- 이번 문제를 못 맞힌(오답·무응답) 참가자는 연속 정답이 끊긴다
            update public.qlive_players p set streak = 0
             where p.code = p_code and not exists (
                   select 1 from public.qlive_answers a
                    where a.code = p_code and a.q = r.q_index and a.pid = p.pid and a.ok);
            update public.qlive_rooms set phase='reveal', phase_at=now(),
                   ends_at = case when auto then now() + make_interval(secs => rev_ms/1000.0) end,
                   rev = rev + 1 where code = p_code;
        elsif r.phase = 'reveal' then
            if r.q_index >= r.total - 1 then
                update public.qlive_rooms set phase='final', phase_at=now(), ends_at=null, rev = rev + 1 where code = p_code;
            else
                update public.qlive_rooms set phase='board', phase_at=now(),
                       ends_at = case when auto then now() + make_interval(secs => board/1000.0) end,
                       rev = rev + 1 where code = p_code;
            end if;
        elsif r.phase = 'board' then
            update public.qlive_rooms set phase='intro', q_index = q_index + 1, phase_at=now(),
                   ends_at = now() + make_interval(secs => intro/1000.0), rev = rev + 1 where code = p_code;
        else
            exit;
        end if;
    end loop;
end $$;


-- ─── 방 만들기 ───
-- p_questions: [{q, o:[..2~4], c:int, cat, h}] 최대 60문항
create or replace function public.qlive_create(p_host_key uuid, p_questions jsonb, p_settings jsonb, p_lang text default 'ko')
returns jsonb language plpgsql security definer set search_path = public as $$
declare v_code text; n int; i int; q jsonb; tries int := 0; recent int;
begin
    if p_host_key is null then raise exception 'bad_host'; end if;
    if jsonb_typeof(p_questions) <> 'array' then raise exception 'bad_questions'; end if;
    n := jsonb_array_length(p_questions);
    if n < 1 or n > 60 then raise exception 'bad_count'; end if;
    for i in 0 .. n-1 loop
        q := p_questions->i;
        if length(coalesce(q->>'q','')) not between 1 and 240 then raise exception 'bad_q_text'; end if;
        if jsonb_typeof(q->'o') <> 'array' or jsonb_array_length(q->'o') not between 2 and 4 then raise exception 'bad_q_opts'; end if;
        if (q->>'c')::int < 0 or (q->>'c')::int >= jsonb_array_length(q->'o') then raise exception 'bad_q_correct'; end if;
    end loop;
    if length(p_questions::text) > 60000 then raise exception 'too_large'; end if;

    -- 오래된 방 정리 + 같은 호스트의 남용 방지
    delete from public.qlive_rooms where created_at < now() - interval '8 hours';
    select count(*) into recent from public.qlive_rooms where host_key = p_host_key and created_at > now() - interval '10 minutes';
    if recent >= 12 then raise exception 'rate_limited'; end if;

    loop
        tries := tries + 1;
        v_code := lpad((floor(random()*900000)+100000)::int::text, 6, '0');
        exit when not exists (select 1 from public.qlive_rooms where code = v_code);
        if tries > 30 then raise exception 'no_code'; end if;
    end loop;

    insert into public.qlive_rooms (code, host_key, lang, questions, total, settings)
    values (v_code, p_host_key, left(coalesce(p_lang,'ko'),5), p_questions, n, coalesce(p_settings,'{}'::jsonb));
    return jsonb_build_object('ok', true, 'code', v_code);
end $$;


-- ─── 참가 (멱등 — 같은 pid 로 다시 부르면 그대로 복귀) ───
create or replace function public.qlive_join(p_code text, p_pid uuid, p_nick text, p_avatar text default null)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r public.qlive_rooms%rowtype; me public.qlive_players%rowtype; v_nick text; k int := 1; cnt int;
begin
    select * into r from public.qlive_rooms where code = p_code;
    if not found then return jsonb_build_object('ok', false, 'err', 'no_room'); end if;
    if p_pid is null then return jsonb_build_object('ok', false, 'err', 'bad_pid'); end if;

    select * into me from public.qlive_players where code = p_code and pid = p_pid;
    if found then
        if me.kicked then return jsonb_build_object('ok', false, 'err', 'kicked'); end if;
        update public.qlive_players set seen_at = now() where code = p_code and pid = p_pid;
        return jsonb_build_object('ok', true, 'nick', me.nick, 'rejoined', true, 'score', me.score);
    end if;

    if r.locked then return jsonb_build_object('ok', false, 'err', 'locked'); end if;
    if r.phase = 'final' then return jsonb_build_object('ok', false, 'err', 'ended'); end if;
    select count(*) into cnt from public.qlive_players where code = p_code and not kicked;
    if cnt >= 200 then return jsonb_build_object('ok', false, 'err', 'full'); end if;

    v_nick := left(regexp_replace(btrim(coalesce(p_nick,'')), '\s+', ' ', 'g'), 16);
    if length(v_nick) < 1 then return jsonb_build_object('ok', false, 'err', 'bad_nick'); end if;
    -- 같은 닉네임이 있으면 뒤에 번호를 붙인다
    while exists (select 1 from public.qlive_players where code = p_code and lower(nick) = lower(v_nick)) loop
        k := k + 1; v_nick := left(regexp_replace(btrim(coalesce(p_nick,'')), '\s+', ' ', 'g'), 13) || k::text;
        exit when k > 99;
    end loop;

    insert into public.qlive_players (code, pid, nick, avatar) values (p_code, p_pid, v_nick, left(p_avatar, 8));
    update public.qlive_rooms set rev = rev + 1 where code = p_code;
    return jsonb_build_object('ok', true, 'nick', v_nick, 'rejoined', false, 'score', 0);
end $$;


-- ─── 답안 (멱등 — 첫 답만 기록) ───
create or replace function public.qlive_answer(p_code text, p_pid uuid, p_q int, p_choice int)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r public.qlive_rooms%rowtype; me public.qlive_players%rowtype; prev public.qlive_answers%rowtype;
        qq jsonb; qms int; v_ms int; v_ok boolean; v_pts int; v_streak int; nact int; nans int;
begin
    select * into r from public.qlive_rooms where code = p_code;
    if not found then return jsonb_build_object('ok', false, 'err', 'no_room'); end if;
    select * into me from public.qlive_players where code = p_code and pid = p_pid;
    if not found or me.kicked then return jsonb_build_object('ok', false, 'err', 'not_player'); end if;

    select * into prev from public.qlive_answers where code = p_code and q = p_q and pid = p_pid;
    if found then return jsonb_build_object('ok', true, 'dup', true, 'choice', prev.choice); end if;

    if r.phase <> 'question' or r.q_index <> p_q or r.paused_left_ms is not null
       or (r.ends_at is not null and now() > r.ends_at + interval '400 milliseconds') then
        return jsonb_build_object('ok', false, 'err', 'closed');
    end if;
    qq  := r.questions -> p_q;
    if p_choice < 0 or p_choice >= jsonb_array_length(qq->'o') then return jsonb_build_object('ok', false, 'err', 'bad_choice'); end if;
    qms := public._qlive_ms(r.settings,'qsec',20) * 1000;
    v_ms := greatest(0, least(qms, (extract(epoch from (now() - r.phase_at)) * 1000)::int));
    v_ok := (p_choice = (qq->>'c')::int);
    if v_ok then
        v_streak := me.streak + 1;
        -- 맞히면 500~1000점(빠를수록) + 연속 정답 보너스 100점씩, 최대 500
        v_pts := round(1000 * (1 - 0.5 * v_ms::numeric / qms))::int + least(v_streak - 1, 5) * 100;
    else
        v_streak := 0; v_pts := 0;
    end if;

    insert into public.qlive_answers (code, q, pid, choice, ms, ok, pts)
    values (p_code, p_q, p_pid, p_choice, v_ms, v_ok, v_pts)
    on conflict do nothing;
    if not found then
        select * into prev from public.qlive_answers where code = p_code and q = p_q and pid = p_pid;
        return jsonb_build_object('ok', true, 'dup', true, 'choice', prev.choice);
    end if;

    update public.qlive_players set score = score + v_pts, streak = v_streak,
           best_streak = greatest(best_streak, v_streak), n_correct = n_correct + (case when v_ok then 1 else 0 end),
           seen_at = now()
     where code = p_code and pid = p_pid;

    -- 접속 중인 전원이 답하면 1초 뒤 바로 공개
    select count(*) into nact from public.qlive_players where code = p_code and not kicked and seen_at > now() - interval '20 seconds';
    select count(*) into nans from public.qlive_answers where code = p_code and q = p_q;
    if nans >= nact and r.ends_at is not null and r.ends_at > now() + interval '1 second' then
        update public.qlive_rooms set ends_at = now() + interval '600 milliseconds', rev = rev + 1
         where code = p_code and phase = 'question' and q_index = p_q;
    end if;
    return jsonb_build_object('ok', true, 'dup', false, 'choice', p_choice);
end $$;


-- ─── 호스트 조작 ───
-- start · next(지금 단계 건너뛰기) · pause · resume · end · kick(pid) · lock(bool) · replay(questions)
create or replace function public.qlive_host(p_code text, p_host_key uuid, p_action text, p_arg jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r public.qlive_rooms%rowtype; intro int; n int;
begin
    select * into r from public.qlive_rooms where code = p_code for update;
    if not found then return jsonb_build_object('ok', false, 'err', 'no_room'); end if;
    if r.host_key <> p_host_key then return jsonb_build_object('ok', false, 'err', 'not_host'); end if;
    intro := public._qlive_ms(r.settings,'intro_ms',3500);
    update public.qlive_rooms set host_seen = now() where code = p_code;

    if p_action = 'start' then
        if r.phase <> 'lobby' then return jsonb_build_object('ok', false, 'err', 'already'); end if;
        update public.qlive_rooms set phase='intro', q_index=0, phase_at=now(), started_at=now(),
               ends_at = now() + make_interval(secs => intro/1000.0), rev = rev + 1 where code = p_code;
    elsif p_action = 'next' then
        if r.phase in ('lobby','final') then return jsonb_build_object('ok', false, 'err', 'bad_phase'); end if;
        update public.qlive_rooms set ends_at = now() - interval '1 second', paused_left_ms = null, rev = rev + 1 where code = p_code;
        perform public._qlive_advance(p_code);
    elsif p_action = 'pause' then
        if r.ends_at is not null and r.paused_left_ms is null and r.phase in ('intro','question','reveal','board') then
            update public.qlive_rooms set paused_left_ms = greatest(500, (extract(epoch from (r.ends_at - now()))*1000)::int),
                   ends_at = null, rev = rev + 1 where code = p_code;
        end if;
    elsif p_action = 'resume' then
        if r.paused_left_ms is not null then
            update public.qlive_rooms set ends_at = now() + make_interval(secs => r.paused_left_ms/1000.0), paused_left_ms = null,
                   rev = rev + 1 where code = p_code;
        end if;
    elsif p_action = 'end' then
        update public.qlive_rooms set phase='final', phase_at=now(), ends_at=null, paused_left_ms=null, rev = rev + 1 where code = p_code;
    elsif p_action = 'kick' then
        update public.qlive_players set kicked = true where code = p_code and pid = (p_arg->>'pid')::uuid;
        update public.qlive_rooms set rev = rev + 1 where code = p_code;
    elsif p_action = 'lock' then
        update public.qlive_rooms set locked = coalesce((p_arg->>'locked')::boolean, not r.locked), rev = rev + 1 where code = p_code;
    elsif p_action = 'replay' then
        n := jsonb_array_length(coalesce(p_arg->'questions','[]'::jsonb));
        if n < 1 or n > 60 then return jsonb_build_object('ok', false, 'err', 'bad_count'); end if;
        delete from public.qlive_answers where code = p_code;
        update public.qlive_players set score=0, streak=0, best_streak=0, n_correct=0 where code = p_code;
        update public.qlive_rooms set questions = p_arg->'questions', total = n, phase='lobby', q_index=-1, phase_at=now(),
               ends_at=null, paused_left_ms=null, started_at=null,
               settings = coalesce(p_arg->'settings', settings), rev = rev + 1 where code = p_code;
    else
        return jsonb_build_object('ok', false, 'err', 'bad_action');
    end if;
    return jsonb_build_object('ok', true);
end $$;


-- ─── 상태 (폴링 겸 진행 엔진) ───
-- 누가 부르든 기한 지난 단계를 넘기고, 부른 사람 관점의 상태를 돌려준다.
create or replace function public.qlive_state(p_code text, p_pid uuid default null, p_host_key uuid default null)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r public.qlive_rooms%rowtype; is_host boolean := false; me public.qlive_players%rowtype;
        qq jsonb; res jsonb; show_q boolean; show_c boolean; counts jsonb; nans int; nact int; nplay int;
        my_ans public.qlive_answers%rowtype; my_rank int; top jsonb; lobby jsonb; opts int;
begin
    perform public._qlive_advance(p_code);
    select * into r from public.qlive_rooms where code = p_code;
    if not found then return jsonb_build_object('ok', false, 'err', 'no_room'); end if;

    if p_host_key is not null and r.host_key = p_host_key then
        is_host := true;
        if now() - r.host_seen > interval '4 seconds' then update public.qlive_rooms set host_seen = now() where code = p_code; end if;
    end if;
    if p_pid is not null then
        select * into me from public.qlive_players where code = p_code and pid = p_pid;
        if found and me.seen_at < now() - interval '8 seconds' then
            update public.qlive_players set seen_at = now() where code = p_code and pid = p_pid;
        end if;
    end if;

    select count(*) into nplay from public.qlive_players where code = p_code and not kicked;
    select count(*) into nact from public.qlive_players where code = p_code and not kicked and seen_at > now() - interval '20 seconds';

    res := jsonb_build_object(
        'ok', true, 'now', (extract(epoch from now())*1000)::bigint, 'rev', r.rev,
        'phase', r.phase, 'q', r.q_index, 'total', r.total, 'lang', r.lang, 'locked', r.locked,
        'paused', r.paused_left_ms is not null, 'paused_left', r.paused_left_ms,
        'phase_at', (extract(epoch from r.phase_at)*1000)::bigint,
        'ends_at', case when r.ends_at is null then null else (extract(epoch from r.ends_at)*1000)::bigint end,
        'settings', r.settings, 'players', nplay, 'active', nact, 'is_host', is_host,
        'host_online', now() - r.host_seen < interval '20 seconds');

    if r.q_index >= 0 and r.q_index < r.total then
        qq := r.questions -> r.q_index;
        opts := jsonb_array_length(qq->'o');
        show_c := r.phase in ('reveal','board','final');
        res := res || jsonb_build_object('question', jsonb_build_object(
            'text', qq->>'q', 'cat', qq->>'cat', 'n', opts,
            'o', case when r.phase = 'intro' and not is_host then null else qq->'o' end,
            'c', case when show_c or is_host then (qq->>'c')::int end,
            'h', case when show_c then qq->>'h' end,
            'img', qq->>'img'));
        select count(*) into nans from public.qlive_answers where code = p_code and q = r.q_index;
        res := res || jsonb_build_object('answered', nans);
        if show_c or is_host then
            select coalesce(jsonb_agg(coalesce(c.cnt,0) order by g.i), '[]'::jsonb) into counts
              from generate_series(0, opts - 1) g(i)
              left join (select choice, count(*) cnt from public.qlive_answers where code = p_code and q = r.q_index group by choice) c on c.choice = g.i;
            res := res || jsonb_build_object('counts', counts);
        end if;
    end if;

    if me.pid is not null then
        select * into my_ans from public.qlive_answers where code = p_code and q = r.q_index and pid = p_pid;
        select rk into my_rank from (select pid, rank() over (order by score desc) rk from public.qlive_players where code = p_code and not kicked) t where t.pid = p_pid;
        res := res || jsonb_build_object('me', jsonb_build_object(
            'nick', me.nick, 'avatar', me.avatar, 'kicked', me.kicked,
            'score', case when r.phase in ('question','intro') then me.score - coalesce(my_ans.pts,0) else me.score end,
            'streak', case when r.phase in ('question','intro') and my_ans.ok then me.streak - 1 else me.streak end,
            'best_streak', me.best_streak, 'n_correct', me.n_correct, 'rank', my_rank,
            'choice', my_ans.choice,
            'ok', case when r.phase in ('reveal','board','final') then my_ans.ok end,
            'pts', case when r.phase in ('reveal','board','final') then my_ans.pts end));
    end if;

    if r.phase in ('reveal','board','final') or is_host then
        select coalesce(jsonb_agg(x order by x->>'r', x->>'nick'), '[]'::jsonb) into top from (
            select jsonb_build_object('r', lpad(rk::text, 4, '0'), 'rank', rk, 'nick', nick, 'avatar', avatar, 'score', score,
                                      'streak', streak, 'n_correct', n_correct, 'pid', case when is_host then pid::text end) x
              from (select *, rank() over (order by score desc) rk from public.qlive_players where code = p_code and not kicked) t
             order by rk, nick limit case when is_host then 200 else 10 end) s;
        res := res || jsonb_build_object('top', top);
    end if;
    if r.phase = 'lobby' then
        select coalesce(jsonb_agg(jsonb_build_object('nick', nick, 'avatar', avatar, 'pid', case when is_host then pid::text end) order by joined_at), '[]'::jsonb)
          into lobby from (select * from public.qlive_players where code = p_code and not kicked order by joined_at limit 200) t;
        res := res || jsonb_build_object('lobby', lobby);
    end if;
    return res;
end $$;

grant execute on function public.qlive_create(uuid, jsonb, jsonb, text)          to anon, authenticated;
grant execute on function public.qlive_join(text, uuid, text, text)              to anon, authenticated;
grant execute on function public.qlive_answer(text, uuid, int, int)              to anon, authenticated;
grant execute on function public.qlive_host(text, uuid, text, jsonb)             to anon, authenticated;
grant execute on function public.qlive_state(text, uuid, uuid)                   to anon, authenticated;
revoke execute on function public._qlive_advance(text) from anon, authenticated, public;
