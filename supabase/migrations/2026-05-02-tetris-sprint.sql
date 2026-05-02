-- =====================================================================
-- Migration: Tetris Sprint mode (40-line time trial)
-- Date:      2026-05-02
-- Purpose:   Sprint mode 별도 ranking — 40 라인 클리어 시간 기록.
--            Marathon 과 다른 메트릭 (duration ASC = 낮을수록 좋음)이라
--            테이블 분리. 같은 SECURITY DEFINER RPC 패턴.
--
-- Sprint 규칙:
--   * 40 라인 클리어 시 record_tetris_sprint_attempt(p_duration_ms)
--   * 미완료 (top-out) 는 기록 안 함 — 클라이언트가 안 보냄
--   * Personal best = MIN(duration_ms), tie-break 은 더 빠른 기록 우선
--
-- Anti-cheat:
--   * duration_ms 8s ~ 10min 범위
--     (사람 sprint 40L 한계는 ~15s, 8s 도 매우 generous floor)
--   * 30 attempts/hour/user (남용 방지)
-- =====================================================================

create table if not exists public.tetris_sprint_attempts (
    id             bigserial   primary key,
    user_id        uuid        not null references auth.users(id) on delete cascade,
    duration_ms    int         not null check (duration_ms between 8000 and 600000),
    lines_cleared  int         not null default 40 check (lines_cleared >= 40),
    created_at     timestamptz not null default now()
);

create index if not exists tetris_sprint_attempts_user_idx
    on public.tetris_sprint_attempts (user_id, created_at desc);
create index if not exists tetris_sprint_attempts_dur_idx
    on public.tetris_sprint_attempts (duration_ms asc);

alter table public.tetris_sprint_attempts enable row level security;
drop policy if exists "tetris_sprint_attempts_select_all" on public.tetris_sprint_attempts;
create policy "tetris_sprint_attempts_select_all"
    on public.tetris_sprint_attempts for select using (true);


create table if not exists public.tetris_sprint_records (
    user_id           uuid        primary key references auth.users(id) on delete cascade,
    best_duration_ms  int         not null,
    total_completes   int         not null default 0,
    total_playtime_ms bigint      not null default 0,
    achieved_at       timestamptz not null default now(),
    updated_at        timestamptz not null default now()
);

create index if not exists tetris_sprint_records_best_idx
    on public.tetris_sprint_records (best_duration_ms asc);

alter table public.tetris_sprint_records enable row level security;
drop policy if exists "tetris_sprint_records_select_all" on public.tetris_sprint_records;
create policy "tetris_sprint_records_select_all"
    on public.tetris_sprint_records for select using (true);


-- Trigger: 매 attempt 마다 records 갱신 (best = MIN).
create or replace function public._tetris_sprint_refresh_record()
returns trigger
language plpgsql security definer
set search_path = public
as $$
begin
    insert into public.tetris_sprint_records
        (user_id, best_duration_ms, total_completes, total_playtime_ms,
         achieved_at, updated_at)
    values (new.user_id, new.duration_ms, 1, new.duration_ms, now(), now())
    on conflict (user_id) do update
      set best_duration_ms  = least(public.tetris_sprint_records.best_duration_ms,
                                    new.duration_ms),
          achieved_at       = case when new.duration_ms
                                       < public.tetris_sprint_records.best_duration_ms
                                   then now()
                                   else public.tetris_sprint_records.achieved_at end,
          total_completes   = public.tetris_sprint_records.total_completes + 1,
          total_playtime_ms = public.tetris_sprint_records.total_playtime_ms
                              + new.duration_ms,
          updated_at        = now();
    return new;
end;
$$;
drop trigger if exists tetris_sprint_refresh_record on public.tetris_sprint_attempts;
create trigger tetris_sprint_refresh_record
    after insert on public.tetris_sprint_attempts
    for each row execute function public._tetris_sprint_refresh_record();


-- RPC: record a Sprint completion. lines_cleared 는 server-side 에서 40 으로 강제.
create or replace function public.record_tetris_sprint_attempt(
    p_duration_ms int
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        prior_best int;
        recent_count int;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    if p_duration_ms < 8000 or p_duration_ms > 600000 then
        raise exception 'bad_duration';
    end if;

    select count(*) into recent_count
      from public.tetris_sprint_attempts
     where user_id = me and created_at > now() - interval '1 hour';
    if recent_count >= 30 then raise exception 'rate_limited'; end if;

    select best_duration_ms into prior_best
      from public.tetris_sprint_records where user_id = me;

    insert into public.tetris_sprint_attempts (user_id, duration_ms, lines_cleared)
    values (me, p_duration_ms, 40);

    return jsonb_build_object(
        'ok', true,
        'duration_ms', p_duration_ms,
        'is_personal_best', prior_best is null or p_duration_ms < prior_best,
        'prior_best', coalesce(prior_best, 0)
    );
end;
$$;
grant execute on function public.record_tetris_sprint_attempt(int) to authenticated;


-- RPC: Sprint leaderboard (3 scopes). Order by duration ASC (낮을수록 좋음).
create or replace function public.tetris_sprint_leaderboard(
    p_scope text default 'world',
    p_limit int   default 50
) returns table (
    rnk              int,
    user_id          uuid,
    nickname         text,
    avatar_url       text,
    best_duration_ms int,
    total_completes  int,
    achieved_at      timestamptz
)
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
begin
    if p_scope not in ('world','today','friends') then raise exception 'bad_scope'; end if;
    if p_scope = 'friends' and me is null then raise exception 'not_authenticated'; end if;

    if p_scope = 'world' then
        return query
            select (row_number() over (order by r.best_duration_ms asc,
                                                r.achieved_at asc))::int,
                   r.user_id, p.nickname, p.avatar_url,
                   r.best_duration_ms, r.total_completes, r.achieved_at
            from public.tetris_sprint_records r
            join public.profiles p on p.id = r.user_id
            order by r.best_duration_ms asc, r.achieved_at asc
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id,
                       min(duration_ms) as best_today,
                       min(created_at) as first_at
                from public.tetris_sprint_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            )
            select (row_number() over (order by t.best_today asc,
                                                t.first_at asc))::int,
                   t.user_id, p.nickname, p.avatar_url,
                   t.best_today,
                   coalesce(r.total_completes, 0), t.first_at
            from today_attempts t
            join public.profiles p on p.id = t.user_id
            left join public.tetris_sprint_records r on r.user_id = t.user_id
            order by t.best_today asc, t.first_at asc
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            with friend_ids as (
                select case when user_a = me then user_b else user_a end as fid
                from public.friendships
                where (user_a = me or user_b = me) and status = 'accepted'
                union
                select me
            )
            select (row_number() over (order by r.best_duration_ms asc,
                                                r.achieved_at asc))::int,
                   r.user_id, p.nickname, p.avatar_url,
                   r.best_duration_ms, r.total_completes, r.achieved_at
            from public.tetris_sprint_records r
            join public.profiles p on p.id = r.user_id
            where r.user_id in (select fid from friend_ids)
            order by r.best_duration_ms asc, r.achieved_at asc
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.tetris_sprint_leaderboard(text, int) to authenticated, anon;


-- RPC: 본인 Sprint 통계.
create or replace function public.tetris_sprint_my_stats()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        rec public.tetris_sprint_records%rowtype;
        rank_world int;
        recents jsonb;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    select * into rec from public.tetris_sprint_records where user_id = me;
    if not found then return jsonb_build_object('has_record', false); end if;

    /* Lower is better — best_duration_ms ASC. */
    select 1 + count(*) into rank_world
      from public.tetris_sprint_records
     where best_duration_ms < rec.best_duration_ms;

    select jsonb_agg(x order by created_at desc) into recents
    from (
        select duration_ms, lines_cleared, created_at
        from public.tetris_sprint_attempts
        where user_id = me
        order by created_at desc
        limit 10
    ) x;

    return jsonb_build_object(
        'has_record', true,
        'best_duration_ms', rec.best_duration_ms,
        'total_completes', rec.total_completes,
        'total_playtime_ms', rec.total_playtime_ms,
        'achieved_at', rec.achieved_at,
        'world_rank', rank_world,
        'recent_attempts', coalesce(recents, '[]'::jsonb)
    );
end;
$$;
grant execute on function public.tetris_sprint_my_stats() to authenticated;


-- PostgREST schema cache reload — 새 RPC 즉시 callable.
notify pgrst, 'reload schema';
