-- =====================================================================
-- Migration: 운영 상황판(/ops/) — 1st-party 방문 통계
-- Date:      2026-11-12
-- Purpose:   GA4 는 운영자가 보기 어렵다. 어느 나라에서 · 언제 와서 ·
--            무엇을 보고 · 얼마나 머물다 갔는지를 우리 DB 에 직접 쌓고
--            관리자 전용 /ops/ 화면에서 입체적으로 본다.
--
-- 흐름:  lpTrack.js(모든 페이지) → POST /api/p (Cloudflare Pages Function,
--        국가·도시·통신사·기기를 붙임) → lp_stat_ingest(p) → lp_hits
--
-- 개인정보: IP · 쿠키 · 계정 id 를 저장하지 않는다. 방문자 구분은 브라우저
--        저장소의 무작위 uuid 뿐이다. 위치는 Cloudflare 가 IP 로 추정한
--        국가·지역·도시 이름만 남긴다.
--
-- 읽기:  테이블은 RLS 로 전부 막고(정책 없음) 관리자 RPC 만 연다.
--        lp_ops_board / lp_ops_sessions / lp_ops_live 는 첫 줄에서
--        is_admin() (2026-04-21-admin-rbac.sql) 을 확인한다.
--
-- 보존:  원본은 400일(전년 동기 비교용) + 200만 행 상한. 일별 요약
--        lp_stat_days 는 영구 보존. 청소는 수집 호출의 0.4% 확률로 돈다
--        (pg_cron 설정 없이 동작).
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. 페이지뷰 — 한 행 = 한 페이지 열람. id 는 브라우저가 만든 uuid 라
--    시작 비컨과 머문 시간 갱신 비컨이 같은 행을 upsert 한다(멱등).
-- ---------------------------------------------------------------------
create table if not exists public.lp_hits (
    id      uuid        primary key,
    vid     uuid        not null,                 -- 방문자(브라우저 저장소)
    sid     uuid        not null,                 -- 세션(30분 무활동이면 새 세션)
    ts      timestamptz not null default now(),   -- 처음 받은 시각(서버)
    seen    timestamptz not null default now(),   -- 마지막 갱신 시각
    path    text        not null check (char_length(path) <= 200),
    sp      smallint,                             -- 세션 안에서 몇 번째 페이지(1 = 진입)
    src     text check (char_length(src) <= 60),  -- 유입: google / naver / kakaotalk / direct …
    ref     text check (char_length(ref) <= 120), -- 외부 referrer 호스트
    kw      text check (char_length(kw) <= 80),   -- 검색어(넘어올 때만)
    cmp     text check (char_length(cmp) <= 80),  -- utm_campaign
    country text check (char_length(country) <= 2),
    region  text check (char_length(region) <= 80),
    city    text check (char_length(city) <= 80),
    tz      text check (char_length(tz) <= 50),
    asorg   text check (char_length(asorg) <= 80),-- 통신사(KT / SK Broadband …)
    dc      boolean     not null default false,   -- 데이터센터 IP(봇 의심)
    dev     text check (char_length(dev) <= 10),  -- mobile / tablet / desktop
    os      text check (char_length(os) <= 16),
    br      text check (char_length(br) <= 16),
    inapp   text check (char_length(inapp) <= 16),-- kakaotalk / instagram / naver …
    lang    text check (char_length(lang) <= 8),  -- 사이트 UI 언어(luckyplz_lang)
    blang   text check (char_length(blang) <= 16),-- 브라우저 언어
    vw      smallint,
    vh      smallint,
    is_new  boolean     not null default false,   -- 첫 방문 세션
    vn      int,                                  -- 이 방문자의 몇 번째 방문(세션)
    dur     int         not null default 0 check (dur >= 0), -- 머문 시간 ms(보이는 동안만)
    me      boolean     not null default false    -- 운영자 본인 기기
);
create index if not exists lp_hits_ts_idx   on public.lp_hits (ts desc);
create index if not exists lp_hits_sid_idx  on public.lp_hits (sid, ts);
create index if not exists lp_hits_seen_idx on public.lp_hits (seen desc);
create index if not exists lp_hits_vid_idx  on public.lp_hits (vid, ts);

alter table public.lp_hits enable row level security;
revoke all on public.lp_hits from anon, authenticated;


-- ---------------------------------------------------------------------
-- 2. 이벤트 — LpTrack(game_start / game_end / share_click …) 미러.
--    국가·기기 같은 속성은 pv → lp_hits 로 조인해 얻는다.
-- ---------------------------------------------------------------------
create table if not exists public.lp_events (
    id    bigserial   primary key,
    ts    timestamptz not null default now(),
    pv    uuid,
    sid   uuid        not null,
    name  text        not null check (name ~ '^[a-z_]{1,32}$'),
    game  text        check (char_length(game) <= 32),
    props jsonb
);
create index if not exists lp_events_ts_idx  on public.lp_events (ts desc);
create index if not exists lp_events_pv_idx  on public.lp_events (pv);
create index if not exists lp_events_sid_idx on public.lp_events (sid, ts);

alter table public.lp_events enable row level security;
revoke all on public.lp_events from anon, authenticated;


-- ---------------------------------------------------------------------
-- 3. 일별 요약(KST) — 원본이 지워진 뒤에도 장기 추이를 남긴다.
--    운영자 본인 · 데이터센터 행은 빼고 센다.
-- ---------------------------------------------------------------------
create table if not exists public.lp_stat_days (
    day          date   primary key,
    visitors     int    not null,
    new_visitors int    not null,
    sessions     int    not null,
    pageviews    int    not null,
    engaged_ms   bigint not null,
    countries    jsonb  not null default '{}'::jsonb   -- {"KR": 방문자, "US": …}
);
alter table public.lp_stat_days enable row level security;
revoke all on public.lp_stat_days from anon, authenticated;


-- ---------------------------------------------------------------------
-- 4. 수집 — Pages Function 이 anon 키로 부른다. 같은 페이지뷰를 여러 번
--    보내도(시작 · 15초 · 1분 · 4분마다 · 숨김) 한 행으로 합쳐진다.
--    값 정리는 Function 이 하고, 여기서는 길이 · 범위만 다시 막는다.
-- ---------------------------------------------------------------------
create or replace function public.lp_stat_housekeep()
returns void
language plpgsql security definer
set search_path = public
as $$
declare
    v_today timestamptz := (date_trunc('day', now() at time zone 'Asia/Seoul')) at time zone 'Asia/Seoul';
    v_from  timestamptz;
    v_rows  real;
begin
    -- 4-1. 아직 요약 안 된 지난 날짜(어제까지)를 요약
    select coalesce((max(day) + 1)::timestamp at time zone 'Asia/Seoul', '-infinity'::timestamptz)
      into v_from from public.lp_stat_days;
    with b as (
        select (ts at time zone 'Asia/Seoul')::date d, vid, sid, country, dur, is_new
          from public.lp_hits
         where ts >= v_from and ts < v_today and not me and not dc
    ),
    t as (
        select d, count(distinct vid) v, count(distinct vid) filter (where is_new) nv,
               count(distinct sid) s, count(*) pv, coalesce(sum(dur), 0) ms
          from b group by d
    ),
    c as (
        select d, jsonb_object_agg(coalesce(country, '??'), n) cj
          from (select d, country, count(distinct vid) n from b group by d, country) x
         group by d
    )
    insert into public.lp_stat_days (day, visitors, new_visitors, sessions, pageviews, engaged_ms, countries)
    select t.d, t.v, t.nv, t.s, t.pv, t.ms, coalesce(c.cj, '{}'::jsonb)
      from t left join c using (d)
    on conflict (day) do nothing;

    -- 4-2. 오래된 원본 삭제(400일) + 행 수 상한(약 200만)
    delete from public.lp_hits
     where id in (select id from public.lp_hits where ts < now() - interval '400 days' limit 20000);
    delete from public.lp_events
     where id in (select id from public.lp_events where ts < now() - interval '400 days' limit 20000);
    select reltuples into v_rows from pg_class where oid = 'public.lp_hits'::regclass;
    if coalesce(v_rows, 0) > 2000000 then
        delete from public.lp_hits
         where id in (select id from public.lp_hits order by ts limit 20000);
    end if;
end;
$$;
revoke all on function public.lp_stat_housekeep() from public, anon, authenticated;


create or replace function public.lp_stat_ingest(p jsonb)
returns void
language plpgsql security definer
set search_path = public
as $$
declare
    v_id  uuid;
    v_sid uuid;
    v_vid uuid;
    v_dur int;
    v_tz  text;
begin
    if p is null or jsonb_typeof(p) <> 'object' then return; end if;
    begin
        v_id  := (p->>'id')::uuid;
        v_sid := (p->>'sid')::uuid;
        v_vid := (p->>'vid')::uuid;
        v_dur := least(greatest(coalesce((p->>'dur')::numeric, 0), 0), 21600000)::int;
    exception when others then
        return;
    end;
    if v_id is null or v_sid is null or v_vid is null then return; end if;

    v_tz := left(nullif(p->>'tz', ''), 50);
    if v_tz is not null then
        begin
            perform now() at time zone v_tz;      -- 잘못된 이름이면 이후 집계가 깨진다
        exception when others then
            v_tz := null;
        end;
    end if;

    insert into public.lp_hits as h (
        id, vid, sid, path, sp, src, ref, kw, cmp, country, region, city, tz, asorg, dc,
        dev, os, br, inapp, lang, blang, vw, vh, is_new, vn, dur, me)
    values (
        v_id, v_vid, v_sid,
        left(coalesce(nullif(p->>'path', ''), '/'), 200),
        case when p->>'sp' ~ '^\d{1,4}$' then least((p->>'sp')::int, 9999)::smallint end,
        left(nullif(p->>'src', ''), 60),
        left(nullif(p->>'ref', ''), 120),
        left(nullif(p->>'kw', ''), 80),
        left(nullif(p->>'cmp', ''), 80),
        case when p->>'country' ~ '^[A-Z0-9]{2}$' then p->>'country' end,
        left(nullif(p->>'region', ''), 80),
        left(nullif(p->>'city', ''), 80),
        v_tz,
        left(nullif(p->>'asorg', ''), 80),
        coalesce(p->>'dc', '') = 'true',
        left(nullif(p->>'dev', ''), 10),
        left(nullif(p->>'os', ''), 16),
        left(nullif(p->>'br', ''), 16),
        left(nullif(p->>'inapp', ''), 16),
        left(nullif(p->>'lang', ''), 8),
        left(nullif(p->>'blang', ''), 16),
        case when p->>'vw' ~ '^\d{1,5}$' then least((p->>'vw')::int, 32000)::smallint end,
        case when p->>'vh' ~ '^\d{1,5}$' then least((p->>'vh')::int, 32000)::smallint end,
        coalesce(p->>'new', '') = 'true',
        case when p->>'vn' ~ '^\d{1,6}$' then (p->>'vn')::int end,
        v_dur,
        coalesce(p->>'me', '') = 'true')
    on conflict (id) do update
        set seen = now(),
            dur  = greatest(h.dur, excluded.dur)
        where h.sid = excluded.sid and h.ts > now() - interval '12 hours';

    if jsonb_typeof(p->'ev') = 'array' then
        insert into public.lp_events (pv, sid, name, game, props)
        select v_id, v_sid, x->>'n', left(nullif(x->>'g', ''), 32),
               case when jsonb_typeof(x->'p') = 'object' and length((x->'p')::text) <= 300 then x->'p' end
          from jsonb_array_elements(p->'ev') with ordinality as t(x, i)
         where i <= 20 and coalesce(x->>'n', '') ~ '^[a-z_]{1,32}$';
    end if;

    if random() < 0.004 then
        perform public.lp_stat_housekeep();
    end if;
end;
$$;
revoke all on function public.lp_stat_ingest(jsonb) from public;
grant execute on function public.lp_stat_ingest(jsonb) to anon, authenticated;


-- ---------------------------------------------------------------------
-- 5. 상황판 읽기 — 내부 도우미(필터 적용된 페이지뷰 · KPI)
--    p_f: {country, path, dev, src, vid, inc_me, inc_dc}
-- ---------------------------------------------------------------------
create or replace function public._lp_ops_hits(p_from timestamptz, p_to timestamptz, p_f jsonb)
returns setof public.lp_hits
language sql stable security definer
set search_path = public
as $$
    select h.*
      from public.lp_hits h
     where h.ts >= p_from and h.ts < p_to
       and (coalesce(p_f->>'inc_me', '') = 'true' or not h.me)
       and (coalesce(p_f->>'inc_dc', '') = 'true' or not h.dc)
       and (p_f->>'country' is null or h.country is not distinct from nullif(p_f->>'country', '??'))
       and (p_f->>'path'    is null or h.path = p_f->>'path')
       and (p_f->>'dev'     is null or h.dev  = p_f->>'dev')
       and (p_f->>'vid'     is null or h.vid::text = p_f->>'vid')
       and (p_f->>'src'     is null or h.sid in (
                select s.sid from public.lp_hits s
                 where s.src = p_f->>'src'
                   and s.ts >= p_from - interval '1 day' and s.ts < p_to));
$$;
revoke all on function public._lp_ops_hits(timestamptz, timestamptz, jsonb) from public, anon, authenticated;


create or replace function public._lp_ops_kpi(p_from timestamptz, p_to timestamptz, p_f jsonb)
returns jsonb
language sql stable security definer
set search_path = public
as $$
    with h as (select * from public._lp_ops_hits(p_from, p_to, p_f)),
    e as (
        select e.sid, e.name from public.lp_events e
         where e.ts >= p_from and e.ts < p_to + interval '12 hours'
           and e.pv in (select id from h)
    ),
    s as (
        select h.sid, count(*) pages, sum(h.dur) dur,
               bool_or(h.sid in (select sid from e where name in ('game_start', 'game_end'))) played
          from h group by h.sid
    )
    select jsonb_build_object(
        'visitors',         (select count(distinct vid) from h),
        'new_visitors',     (select count(distinct vid) from h where is_new),
        'sessions',         (select count(*) from s),
        'pageviews',        (select count(*) from h),
        'engaged_ms',       (select coalesce(sum(dur), 0) from s),
        'avg_ms',           (select coalesce(round(avg(dur)), 0) from s),
        'engaged_sessions', (select count(*) from s where dur >= 10000 or pages >= 2 or played),
        'plays',            (select count(*) from e where name = 'game_end'),
        'play_sessions',    (select count(*) from s where played)
    );
$$;
revoke all on function public._lp_ops_kpi(timestamptz, timestamptz, jsonb) from public, anon, authenticated;


-- ---------------------------------------------------------------------
-- 6. lp_ops_board — 기간 하나에 대한 전체 그림(KPI · 추이 · 나라 · 도시 ·
--    페이지 · 유입 · 기기 · 언어 · 시간대 · 체류 분포 · 게임 열림 이력)
--    시간 구간은 KST. 2일 이하면 시간별, 그보다 길면 일별.
-- ---------------------------------------------------------------------
create or replace function public.lp_ops_board(p_from timestamptz, p_to timestamptz, p_f jsonb default '{}'::jsonb)
returns jsonb
language plpgsql stable security definer
set search_path = public
as $$
declare
    v_f    jsonb    := coalesce(p_f, '{}'::jsonb);
    v_span interval := p_to - p_from;
    v_unit text     := case when p_to - p_from <= interval '2 days' then 'hour' else 'day' end;
    -- 비교 기간 = 날짜 단위로 통째로 민 같은 구간('오늘 0시~지금' ↔ '어제 0시~어제 이 시각')
    v_shift interval := ceil(extract(epoch from p_to - p_from) / 86400) * interval '1 day';
begin
    if not public.is_admin() then
        raise exception 'forbidden' using errcode = '42501';
    end if;
    if p_from is null or p_to is null or p_to <= p_from or v_span > interval '400 days' then
        raise exception 'bad range';
    end if;

    return (
    with h as (select * from public._lp_ops_hits(p_from, p_to, v_f)),
    e as (
        select e.* from public.lp_events e
         where e.ts >= p_from and e.ts < p_to + interval '12 hours'
           and e.pv in (select id from h)
    ),
    s as (
        select h.sid,
               (array_agg(h.vid))[1]                                   vid,
               min(h.ts) t0, count(*) pages, sum(h.dur) dur,
               bool_or(h.is_new)                                       nw,
               max(h.vn)                                               vn,
               (array_agg(h.country order by h.ts))[1]                 country,
               (array_agg(h.city    order by h.ts))[1]                 city,
               (array_agg(h.region  order by h.ts))[1]                 region,
               (array_agg(h.tz      order by h.ts))[1]                 tz,
               (array_agg(h.dev     order by h.ts))[1]                 dev,
               (array_agg(h.os      order by h.ts))[1]                 os,
               (array_agg(h.br      order by h.ts))[1]                 br,
               (array_agg(h.inapp   order by h.ts))[1]                 inapp,
               (array_agg(h.lang    order by h.ts))[1]                 lang,
               (array_agg(h.blang   order by h.ts))[1]                 blang,
               (array_agg(h.asorg   order by h.ts))[1]                 asorg,
               coalesce((array_agg(h.src order by h.ts) filter (where h.src is not null))[1], 'unknown') src,
               (array_agg(h.path    order by h.ts))[1]                 entry,
               bool_or(h.sid in (select sid from e where name in ('game_start', 'game_end'))) played
          from h group by h.sid
    ),
    ser as (
        select b from generate_series(
            date_trunc(v_unit, p_from at time zone 'Asia/Seoul'),
            (p_to at time zone 'Asia/Seoul') - interval '1 second',
            ('1 ' || v_unit)::interval) b
    ),
    hb as (
        select date_trunc(v_unit, ts at time zone 'Asia/Seoul') b,
               count(distinct vid) v, count(distinct sid) ss, count(*) pv, sum(dur) ms
          from h group by 1
    ),
    eb as (
        select date_trunc(v_unit, ts at time zone 'Asia/Seoul') b, count(*) n
          from e where name = 'game_end' group by 1
    ),
    pe as (   -- 페이지별 플레이 수(상관 서브쿼리로 쓰면 페이지 수 × 이벤트 × 조회로 폭발한다)
        select h.path, count(*) n
          from e join h on h.id = e.pv
         where e.name = 'game_end'
         group by h.path
    ),
    gp as (
        select g.game_id, g.created_at from public.game_plays g
         where g.created_at >= p_from and g.created_at < p_to
    )
    select jsonb_build_object(
        'unit', v_unit,
        'from', p_from, 'to', p_to,
        'kpi',  public._lp_ops_kpi(p_from, p_to, v_f),
        'prev', public._lp_ops_kpi(p_from - v_shift, p_to - v_shift, v_f),
        'prev_from', p_from - v_shift,

        'series', (select coalesce(jsonb_agg(jsonb_build_object(
                        't', to_char(ser.b, 'YYYY-MM-DD"T"HH24:MI'),
                        'v', coalesce(hb.v, 0), 's', coalesce(hb.ss, 0),
                        'pv', coalesce(hb.pv, 0), 'ms', coalesce(hb.ms, 0),
                        'g', coalesce(eb.n, 0)) order by ser.b), '[]'::jsonb)
                     from ser left join hb using (b) left join eb using (b)),

        'countries', (select coalesce(jsonb_agg(x order by x.s desc), '[]'::jsonb) from (
                        select coalesce(country, '??') c, count(*) s, count(distinct vid) v,
                               sum(pages) pv, round(avg(dur)) ms,
                               count(*) filter (where dur >= 10000 or pages >= 2 or played) eng,
                               count(*) filter (where nw) nw
                          from s group by 1 order by 2 desc limit 80) x),

        'cities', (select coalesce(jsonb_agg(x order by x.s desc), '[]'::jsonb) from (
                        select coalesce(country, '??') c, city, region, count(*) s,
                               count(distinct vid) v, round(avg(dur)) ms
                          from s where city is not null
                         group by 1, 2, 3 order by 4 desc limit 40) x),

        'pages', (select coalesce(jsonb_agg(x order by x.pv desc), '[]'::jsonb) from (
                        select h.path p, count(*) pv, count(distinct h.vid) v,
                               round(avg(h.dur)) ms,
                               count(*) filter (where h.sp = 1) ent,
                               coalesce(max(pe.n), 0) plays
                          from h left join pe on pe.path = h.path
                         group by h.path order by 2 desc limit 60) x),

        'sources', (select coalesce(jsonb_agg(x order by x.s desc), '[]'::jsonb) from (
                        select src, count(*) s, count(distinct vid) v, round(avg(dur)) ms,
                               count(*) filter (where dur >= 10000 or pages >= 2 or played) eng
                          from s group by 1 order by 2 desc limit 40) x),

        'keywords', (select coalesce(jsonb_agg(x order by x.n desc), '[]'::jsonb) from (
                        select kw k, min(src) src, count(*) n
                          from h where kw is not null group by kw order by 3 desc limit 30) x),

        'refs', (select coalesce(jsonb_agg(x order by x.n desc), '[]'::jsonb) from (
                        select ref r, count(*) n
                          from h where ref is not null group by ref order by 2 desc limit 30) x),

        'dims', jsonb_build_object(
            'dev',   (select coalesce(jsonb_object_agg(k, n), '{}'::jsonb) from (select coalesce(dev, '?') k, count(*) n from s group by 1) x),
            'os',    (select coalesce(jsonb_object_agg(k, n), '{}'::jsonb) from (select coalesce(os, '?') k, count(*) n from s group by 1) x),
            'br',    (select coalesce(jsonb_object_agg(k, n), '{}'::jsonb) from (select coalesce(br, '?') k, count(*) n from s group by 1) x),
            'inapp', (select coalesce(jsonb_object_agg(k, n), '{}'::jsonb) from (select inapp k, count(*) n from s where inapp is not null group by 1) x),
            'lang',  (select coalesce(jsonb_object_agg(k, n), '{}'::jsonb) from (select coalesce(nullif(lang, ''), '-') k, count(*) n from s group by 1) x),
            'blang', (select coalesce(jsonb_object_agg(k, n), '{}'::jsonb) from (select coalesce(lower(left(blang, 2)), '?') k, count(*) n from s group by 1) x),
            'isp',   (select coalesce(jsonb_object_agg(k, n), '{}'::jsonb) from (select asorg k, count(*) n from s where asorg is not null group by 1 order by 2 desc limit 15) x)
        ),

        'heat', (select coalesce(jsonb_agg(jsonb_build_array(d, hr, n)), '[]'::jsonb) from (
                        select extract(isodow from t0 at time zone 'Asia/Seoul')::int d,
                               extract(hour   from t0 at time zone 'Asia/Seoul')::int hr, count(*) n
                          from s group by 1, 2) x),
        'heat_local', (select coalesce(jsonb_agg(jsonb_build_array(d, hr, n)), '[]'::jsonb) from (
                        select extract(isodow from t0 at time zone coalesce(tz, 'Asia/Seoul'))::int d,
                               extract(hour   from t0 at time zone coalesce(tz, 'Asia/Seoul'))::int hr, count(*) n
                          from s group by 1, 2) x),

        'dwell', (select jsonb_build_array(
                        count(*) filter (where dur < 10000),
                        count(*) filter (where dur >= 10000   and dur < 30000),
                        count(*) filter (where dur >= 30000   and dur < 60000),
                        count(*) filter (where dur >= 60000   and dur < 180000),
                        count(*) filter (where dur >= 180000  and dur < 600000),
                        count(*) filter (where dur >= 600000  and dur < 1800000),
                        count(*) filter (where dur >= 1800000)) from s),
        'depth', (select jsonb_build_array(
                        count(*) filter (where pages = 1), count(*) filter (where pages = 2),
                        count(*) filter (where pages = 3), count(*) filter (where pages between 4 and 5),
                        count(*) filter (where pages >= 6)) from s),
        'visitno', (select jsonb_build_array(
                        count(*) filter (where coalesce(vn, 1) = 1), count(*) filter (where vn = 2),
                        count(*) filter (where vn between 3 and 5), count(*) filter (where vn between 6 and 10),
                        count(*) filter (where vn > 10)) from s),

        'events', (select coalesce(jsonb_agg(x order by x.n desc), '[]'::jsonb) from (
                        select name n0, coalesce(game, '-') g, count(*) n
                          from e group by 1, 2 order by 3 desc limit 60) x),

        'plays_hist', jsonb_build_object(
            'by_game', (select coalesce(jsonb_object_agg(game_id, n), '{}'::jsonb)
                          from (select game_id, count(*) n from gp group by 1) x),
            'total_all', (select count(*) from public.game_plays)),

        'health', jsonb_build_object(
            'rows',       (select reltuples::bigint from pg_class where oid = 'public.lp_hits'::regclass),
            'bytes',      pg_total_relation_size('public.lp_hits') + pg_total_relation_size('public.lp_events'),
            'first',      (select min(ts) from public.lp_hits),
            'last',       (select max(seen) from public.lp_hits),
            'excluded_me', (select count(*) from public.lp_hits where ts >= p_from and ts < p_to and me),
            'excluded_dc', (select count(*) from public.lp_hits where ts >= p_from and ts < p_to and dc and not me))
    ));
end;
$$;
revoke all on function public.lp_ops_board(timestamptz, timestamptz, jsonb) from public, anon;
grant execute on function public.lp_ops_board(timestamptz, timestamptz, jsonb) to authenticated;


-- ---------------------------------------------------------------------
-- 7. lp_ops_sessions — 방문 기록(한 줄 = 한 세션). 누가 · 어디서 · 언제 ·
--    어떤 경로로 들어와 · 무엇을 보고 · 얼마나 머물렀는지.
-- ---------------------------------------------------------------------
create or replace function public.lp_ops_sessions(
    p_from timestamptz, p_to timestamptz, p_f jsonb default '{}'::jsonb,
    p_limit int default 50, p_offset int default 0)
returns jsonb
language plpgsql stable security definer
set search_path = public
as $$
begin
    if not public.is_admin() then
        raise exception 'forbidden' using errcode = '42501';
    end if;
    if p_from is null or p_to is null or p_to <= p_from or p_to - p_from > interval '400 days' then
        raise exception 'bad range';
    end if;

    return (
    with h as (select * from public._lp_ops_hits(p_from, p_to, coalesce(p_f, '{}'::jsonb))),
    s as (
        select h.sid,
               (array_agg(h.vid))[1]                    vid,
               min(h.ts) t0, max(h.seen) t1, count(*) pages, sum(h.dur) dur,
               bool_or(h.is_new) nw, max(h.vn) vn,
               (array_agg(h.country order by h.ts))[1]  country,
               (array_agg(h.region  order by h.ts))[1]  region,
               (array_agg(h.city    order by h.ts))[1]  city,
               (array_agg(h.tz      order by h.ts))[1]  tz,
               (array_agg(h.dev     order by h.ts))[1]  dev,
               (array_agg(h.os      order by h.ts))[1]  os,
               (array_agg(h.br      order by h.ts))[1]  br,
               (array_agg(h.inapp   order by h.ts))[1]  inapp,
               (array_agg(h.lang    order by h.ts))[1]  lang,
               (array_agg(h.blang   order by h.ts))[1]  blang,
               (array_agg(h.asorg   order by h.ts))[1]  asorg,
               (array_agg(h.src order by h.ts) filter (where h.src is not null))[1] src,
               (array_agg(h.ref order by h.ts) filter (where h.ref is not null))[1] ref,
               (array_agg(h.kw  order by h.ts) filter (where h.kw  is not null))[1] kw,
               bool_or(h.me) me, bool_or(h.dc) dc,
               jsonb_agg(jsonb_build_object('p', h.path, 'd', h.dur, 't', h.ts) order by h.ts) pv
          from h group by h.sid
    ),
    pg as (
        select * from s order by t0 desc
         limit least(greatest(coalesce(p_limit, 50), 1), 200)
        offset greatest(coalesce(p_offset, 0), 0)
    ),
    ev as (
        select e.sid, jsonb_agg(jsonb_build_object('n', e.name, 'g', e.game, 't', e.ts) order by e.ts) evs
          from public.lp_events e
         where e.sid in (select sid from pg) and e.ts >= p_from - interval '1 hour'
         group by e.sid
    )
    select jsonb_build_object(
        'total', (select count(*) from s),
        'rows',  coalesce((
            select jsonb_agg(to_jsonb(pg) || jsonb_build_object('ev', coalesce(ev.evs, '[]'::jsonb)) order by pg.t0 desc)
              from pg left join ev using (sid)), '[]'::jsonb))
    );
end;
$$;
revoke all on function public.lp_ops_sessions(timestamptz, timestamptz, jsonb, int, int) from public, anon;
grant execute on function public.lp_ops_sessions(timestamptz, timestamptz, jsonb, int, int) to authenticated;


-- ---------------------------------------------------------------------
-- 8. lp_ops_live — 지금 접속 중(최근 5분 안에 신호가 온 세션)
-- ---------------------------------------------------------------------
create or replace function public.lp_ops_live(p_f jsonb default '{}'::jsonb)
returns jsonb
language plpgsql stable security definer
set search_path = public
as $$
declare
    v_me boolean := coalesce(p_f->>'inc_me', '') = 'true';
begin
    if not public.is_admin() then
        raise exception 'forbidden' using errcode = '42501';
    end if;

    return (
    with cur as (
        select distinct on (sid) sid, vid, path, seen, country, region, city, dev, os, inapp
          from public.lp_hits
         where seen > now() - interval '5 minutes' and (v_me or not me) and not dc
         order by sid, ts desc
    ),
    ss as (
        select sid, min(ts) t0, sum(dur) dur, count(*) pages,
               (array_agg(src order by ts) filter (where src is not null))[1] src
          from public.lp_hits
         where sid in (select sid from cur) and ts > now() - interval '12 hours'
         group by sid
    )
    select jsonb_build_object(
        'now', now(),
        'n',   (select count(*) from cur),
        'rows', coalesce((
            select jsonb_agg(jsonb_build_object(
                       'sid', cur.sid, 'p', cur.path, 'c', cur.country, 'region', cur.region,
                       'city', cur.city, 'dev', cur.dev, 'os', cur.os, 'inapp', cur.inapp,
                       'seen', cur.seen, 't0', ss.t0, 'dur', ss.dur, 'pages', ss.pages, 'src', ss.src)
                   order by cur.seen desc)
              from cur join ss using (sid)), '[]'::jsonb),
        'last30', (select coalesce(jsonb_agg(jsonb_build_array(m, n) order by m), '[]'::jsonb) from (
                       select floor(extract(epoch from now() - seen) / 60)::int m, count(distinct sid) n
                         from public.lp_hits
                        where seen > now() - interval '30 minutes' and (v_me or not me) and not dc
                        group by 1) x)
    ));
end;
$$;
revoke all on function public.lp_ops_live(jsonb) from public, anon;
grant execute on function public.lp_ops_live(jsonb) to authenticated;


-- ---------------------------------------------------------------------
-- 9. lp_ops_days — 일별 요약(장기 추이). 호출 때 밀린 요약을 먼저 채운다.
-- ---------------------------------------------------------------------
create or replace function public.lp_ops_days(p_days int default 400)
returns jsonb
language plpgsql security definer
set search_path = public
as $$
begin
    if not public.is_admin() then
        raise exception 'forbidden' using errcode = '42501';
    end if;
    perform public.lp_stat_housekeep();
    return (
        select coalesce(jsonb_agg(to_jsonb(d) order by d.day), '[]'::jsonb)
          from public.lp_stat_days d
         where d.day >= (now() at time zone 'Asia/Seoul')::date - least(greatest(coalesce(p_days, 400), 1), 3650)
    );
end;
$$;
revoke all on function public.lp_ops_days(int) from public, anon;
grant execute on function public.lp_ops_days(int) to authenticated;


-- 확인: 아래가 5행이면 적용 완료
select proname from pg_proc
 where proname in ('lp_stat_ingest', 'lp_ops_board', 'lp_ops_sessions', 'lp_ops_live', 'lp_ops_days')
 order by proname;
