-- =====================================================================
-- Migration: Reaction-speed game (first record-keeping skill game)
-- Date:      2026-04-22
-- Purpose:   Stand up the first login-required skill game. User clicks
--            when a red box turns green, we record reaction ms, keep a
--            personal best + global + friend leaderboards.
--
-- Design notes:
--   * Every read path is a SECURITY DEFINER RPC (see
--     memory/messaging_rpc_pattern.md — mobile WebView's RLS
--     evaluation silently drops rows on direct-table SELECT, while
--     RPCs work). New-game code should ALWAYS follow this pattern
--     from day one.
--   * Client-reported reaction_ms is trusted with a 100 ms floor (no
--     human reacts faster than that). Rate-limited to 10 attempts per
--     minute per user so bots can't flood the leaderboard.
--   * reaction_records is a flattened snapshot of each user's best /
--     average / count, maintained by a trigger — leaderboard reads
--     don't need to MAX/AVG over thousands of rows.
-- =====================================================================


-- Raw attempt log — one row per try. Keeps history for "최근 기록" UI.
create table if not exists public.reaction_attempts (
    id            bigserial   primary key,
    user_id       uuid        not null references auth.users(id) on delete cascade,
    reaction_ms   int         not null check (reaction_ms between 100 and 5000),
    wait_delay_ms int         not null check (wait_delay_ms between 500 and 8000),
    created_at    timestamptz not null default now()
);

create index if not exists reaction_attempts_user_idx
    on public.reaction_attempts (user_id, created_at desc);
create index if not exists reaction_attempts_ms_idx
    on public.reaction_attempts (reaction_ms asc);
create index if not exists reaction_attempts_today_idx
    on public.reaction_attempts (created_at)
    where created_at > now() - interval '2 days';  /* for today's board */

alter table public.reaction_attempts enable row level security;

-- Anyone can SELECT (leaderboards are world-readable). Insertion
-- happens only via RPC, which enforces rate limits + integrity checks.
drop policy if exists "reaction_attempts_select_all" on public.reaction_attempts;
create policy "reaction_attempts_select_all"
    on public.reaction_attempts for select using (true);


-- Per-user snapshot — best, count, avg. A trigger keeps this in sync.
create table if not exists public.reaction_records (
    user_id        uuid        primary key references auth.users(id) on delete cascade,
    best_ms        int         not null,
    total_attempts int         not null default 0,
    avg_ms         int,
    updated_at     timestamptz not null default now()
);

create index if not exists reaction_records_best_idx on public.reaction_records (best_ms asc);

alter table public.reaction_records enable row level security;
drop policy if exists "reaction_records_select_all" on public.reaction_records;
create policy "reaction_records_select_all"
    on public.reaction_records for select using (true);


-- Trigger: after an attempt is inserted, update the user's summary
-- row. Handles both first insert (INSERT summary) and subsequent
-- (UPDATE if better / bump count + avg).
create or replace function public._reaction_refresh_record()
returns trigger
language plpgsql security definer
set search_path = public
as $$
begin
    insert into public.reaction_records (user_id, best_ms, total_attempts, avg_ms, updated_at)
    values (new.user_id, new.reaction_ms, 1, new.reaction_ms, now())
    on conflict (user_id) do update
      set best_ms        = least(public.reaction_records.best_ms, new.reaction_ms),
          total_attempts = public.reaction_records.total_attempts + 1,
          avg_ms         = (
              select avg(reaction_ms)::int
              from public.reaction_attempts
              where user_id = new.user_id
          ),
          updated_at = now();
    return new;
end;
$$;
drop trigger if exists reaction_refresh_record on public.reaction_attempts;
create trigger reaction_refresh_record
    after insert on public.reaction_attempts
    for each row execute function public._reaction_refresh_record();


-- RPC: submit a new attempt. Rate-limited (10/minute), floor-checked
-- (>=100 ms), and authenticated. Returns the new personal-best flag
-- so the UI can celebrate.
create or replace function public.record_reaction_attempt(
    p_ms int, p_delay_ms int
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        prior_best int;
        recent_count int;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    if p_ms < 100 or p_ms > 5000 then raise exception 'bad_reaction_ms'; end if;
    if p_delay_ms < 500 or p_delay_ms > 8000 then raise exception 'bad_delay_ms'; end if;

    /* Rate limit: 10 attempts per minute. Cheap count on the user_idx. */
    select count(*) into recent_count
      from public.reaction_attempts
     where user_id = me and created_at > now() - interval '1 minute';
    if recent_count >= 10 then raise exception 'rate_limited'; end if;

    select best_ms into prior_best from public.reaction_records where user_id = me;

    insert into public.reaction_attempts (user_id, reaction_ms, wait_delay_ms)
    values (me, p_ms, p_delay_ms);

    return jsonb_build_object(
        'ok', true,
        'reaction_ms', p_ms,
        'is_personal_best', prior_best is null or p_ms < prior_best,
        'prior_best', prior_best
    );
end;
$$;
grant execute on function public.record_reaction_attempt(int, int) to authenticated;


-- RPC: fetch one of the three leaderboard scopes with profile join.
-- scope: 'world' | 'today' | 'friends'.
create or replace function public.reaction_leaderboard(
    p_scope text default 'world',
    p_limit int   default 50
) returns table (
    rnk          int,
    user_id      uuid,
    nickname     text,
    avatar_url   text,
    best_ms      int,
    total_attempts int,
    achieved_at  timestamptz
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
            select (row_number() over (order by r.best_ms asc, r.updated_at asc))::int,
                   r.user_id, p.nickname, p.avatar_url, r.best_ms, r.total_attempts, r.updated_at
            from public.reaction_records r
            join public.profiles p on p.id = r.user_id
            order by r.best_ms asc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        /* Today = Asia/Seoul day boundary. Aggregate each user's best
           of attempts that landed today, then sort by that. */
        return query
            with today_attempts as (
                select user_id, min(reaction_ms) as best_today, min(created_at) as first_at
                from public.reaction_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            )
            select (row_number() over (order by t.best_today asc, t.first_at asc))::int,
                   t.user_id, p.nickname, p.avatar_url, t.best_today,
                   coalesce(r.total_attempts, 0), t.first_at
            from today_attempts t
            join public.profiles p on p.id = t.user_id
            left join public.reaction_records r on r.user_id = t.user_id
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
            select (row_number() over (order by r.best_ms asc, r.updated_at asc))::int,
                   r.user_id, p.nickname, p.avatar_url, r.best_ms, r.total_attempts, r.updated_at
            from public.reaction_records r
            join public.profiles p on p.id = r.user_id
            where r.user_id in (select fid from friend_ids)
            order by r.best_ms asc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.reaction_leaderboard(text, int) to authenticated, anon;


-- RPC: fetch the current user's own state (best + recent + rank).
-- Bundled so the game page only needs one round-trip on open.
create or replace function public.reaction_my_stats()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        rec public.reaction_records%rowtype;
        rank_world int;
        recents jsonb;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    select * into rec from public.reaction_records where user_id = me;
    if not found then
        return jsonb_build_object('has_record', false);
    end if;
    select 1 + count(*) into rank_world
      from public.reaction_records
     where best_ms < rec.best_ms;

    select jsonb_agg(x order by created_at desc) into recents
    from (
        select reaction_ms, created_at
        from public.reaction_attempts
        where user_id = me
        order by created_at desc
        limit 20
    ) x;

    return jsonb_build_object(
        'has_record', true,
        'best_ms', rec.best_ms,
        'avg_ms', rec.avg_ms,
        'total_attempts', rec.total_attempts,
        'world_rank', rank_world,
        'recent_attempts', coalesce(recents, '[]'::jsonb)
    );
end;
$$;
grant execute on function public.reaction_my_stats() to authenticated;
