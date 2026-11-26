-- Keep the existing qlive RPC signatures and eight-hour room lifecycle.
-- Serialize admission per room so simultaneous arrivals cannot take the same name or exceed capacity.
-- Return phase-specific data and avoid a full roster in each player's lobby poll.
begin;

create or replace function public.qlive_join(p_code text, p_pid uuid, p_nick text, p_avatar text default null)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r public.qlive_rooms%rowtype; me public.qlive_players%rowtype; v_nick text; k int := 1; cnt int;
begin
    select * into r from public.qlive_rooms where code = p_code for update;
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
    -- Seat checks and nickname allocation run under this room's row lock.
    while exists (select 1 from public.qlive_players where code = p_code and lower(nick) = lower(v_nick)) loop
        k := k + 1;
        v_nick := left(regexp_replace(btrim(p_nick), '\s+', ' ', 'g'), 16 - length(k::text)) || k::text;
    end loop;

    insert into public.qlive_players (code, pid, nick, avatar) values (p_code, p_pid, v_nick, left(p_avatar, 8));
    update public.qlive_rooms set rev = rev + 1 where code = p_code;
    return jsonb_build_object('ok', true, 'nick', v_nick, 'rejoined', false, 'score', 0);
end $$;

create or replace function public.qlive_host(p_code text, p_host_key uuid, p_action text, p_arg jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r public.qlive_rooms%rowtype; intro int; n int;
begin
    select * into r from public.qlive_rooms where code = p_code for update;
    if not found then return jsonb_build_object('ok', false, 'err', 'no_room'); end if;
    if r.host_key is distinct from p_host_key then return jsonb_build_object('ok', false, 'err', 'not_host'); end if;
    -- Older clients omit the expected phase. New clients bind each command to the screen on which it was pressed.
    if p_arg ? 'expected_phase' and (
        (p_arg->>'expected_phase') is distinct from r.phase
        or (p_arg->>'expected_q')::int is distinct from r.q_index
        or (p_arg->>'expected_phase_at')::bigint is distinct from (extract(epoch from r.phase_at)*1000)::bigint
    ) then return jsonb_build_object('ok', false, 'err', 'stale'); end if;
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

create or replace function public.qlive_answer(p_code text, p_pid uuid, p_q int, p_choice int)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r public.qlive_rooms%rowtype; me public.qlive_players%rowtype; prev public.qlive_answers%rowtype;
        qq jsonb; qms int; v_ms int; v_ok boolean; v_pts int; v_streak int;
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
    if p_choice is null or p_choice < 0 or p_choice >= jsonb_array_length(qq->'o') then return jsonb_build_object('ok', false, 'err', 'bad_choice'); end if;
    qms := public._qlive_ms(r.settings,'qsec',20) * 1000;
    v_ms := greatest(0, least(qms, qms - (extract(epoch from (r.ends_at - now())) * 1000)::int));
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
    if r.ends_at > now() + interval '1 second' and not exists (
        select 1 from public.qlive_players p
        where p.code = p_code and not p.kicked and p.seen_at > now() - interval '20 seconds'
          and not exists (select 1 from public.qlive_answers a where a.code = p_code and a.q = p_q and a.pid = p.pid)
    ) then
        update public.qlive_rooms set ends_at = now() + interval '600 milliseconds', rev = rev + 1
         where code = p_code and phase = 'question' and q_index = p_q and phase_at = r.phase_at
           and paused_left_ms is null and ends_at = r.ends_at;
    end if;
    return jsonb_build_object('ok', true, 'dup', false, 'choice', p_choice);
end $$;

create or replace function public.qlive_state(p_code text, p_pid uuid default null, p_host_key uuid default null)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r public.qlive_rooms%rowtype; is_host boolean := false; me public.qlive_players%rowtype;
        qq jsonb; res jsonb; show_c boolean; counts jsonb; nans int; nact int; nplay int;
        my_ans public.qlive_answers%rowtype; my_rank int; top jsonb; lobby jsonb; opts int;
        shortened_at timestamptz; shortened_rev bigint;
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

    select count(*), count(*) filter (where seen_at > now() - interval '20 seconds') into nplay, nact
    from public.qlive_players where code = p_code and not kicked;

    if r.q_index >= 0 and r.q_index < r.total then
        select count(*) into nans from public.qlive_answers where code = p_code and q = r.q_index;
    end if;
    -- The last simultaneous submissions can each see the other as uncommitted.
    -- Reconcile after commit on the host poll. Each currently active seat needs its own answer.
    if is_host and r.phase = 'question' and r.paused_left_ms is null
       and r.ends_at > now() + interval '1 second' and nact > 0 and nans >= nact then
        update public.qlive_rooms set ends_at = now() + interval '600 milliseconds', rev = rev + 1
         where code = p_code and phase = 'question' and q_index = r.q_index and phase_at = r.phase_at
           and paused_left_ms is null and ends_at = r.ends_at
           and (select bool_and(a.pid is not null)
                  from public.qlive_players p
                  left join public.qlive_answers a on a.code = p.code and a.q = r.q_index and a.pid = p.pid
                 where p.code = p_code and not p.kicked and p.seen_at > now() - interval '20 seconds')
         returning ends_at, rev into shortened_at, shortened_rev;
        if found then r.ends_at := shortened_at; r.rev := shortened_rev; end if;
    end if;

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
        if not me.kicked and r.phase in ('reveal','board','final') then
            select 1 + count(*) into my_rank from public.qlive_players
             where code = p_code and not kicked and score > me.score;
        end if;
        res := res || jsonb_build_object('me', jsonb_build_object(
            'nick', me.nick, 'avatar', me.avatar, 'kicked', me.kicked,
            'score', case when r.phase in ('question','intro') then me.score - coalesce(my_ans.pts,0) else me.score end,
            'streak', case when r.phase in ('question','intro') and my_ans.ok then me.streak - 1 else me.streak end,
            'best_streak', me.best_streak, 'n_correct', me.n_correct, 'rank', my_rank,
            'choice', my_ans.choice,
            'ok', case when r.phase in ('reveal','board','final') then my_ans.ok end,
            'pts', case when r.phase in ('reveal','board','final') then my_ans.pts end));
    end if;

    if r.phase in ('reveal','board','final') then
        select coalesce(jsonb_agg(x order by x->>'r', x->>'nick'), '[]'::jsonb) into top from (
            select jsonb_build_object('r', lpad(rk::text, 4, '0'), 'rank', rk, 'nick', nick, 'avatar', avatar, 'score', score,
                                      'streak', streak, 'n_correct', n_correct, 'pid', case when is_host then pid::text end) x
              from (select *, rank() over (order by score desc) rk from public.qlive_players where code = p_code and not kicked) t
             order by rk, nick limit case when is_host then 200 else 10 end) s;
        res := res || jsonb_build_object('top', top);
    end if;
    if r.phase = 'lobby' and is_host then
        select coalesce(jsonb_agg(jsonb_build_object('nick', nick, 'avatar', avatar, 'pid', case when is_host then pid::text end) order by joined_at), '[]'::jsonb)
          into lobby from (select * from public.qlive_players where code = p_code and not kicked order by joined_at limit 200) t;
        res := res || jsonb_build_object('lobby', lobby);
    end if;
    return res;
end $$;

notify pgrst, 'reload schema';
commit;
