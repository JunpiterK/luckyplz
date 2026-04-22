-- =====================================================================
-- Migration: Quiz Battle (real-time party trivia, Kahoot-style)
-- Date:      2026-04-22
-- Purpose:   Host creates a room; guests join via QR/code; host pushes
--            questions via Realtime broadcast; guests tap one of 4
--            colored answers; server aggregates scores into a shared
--            leaderboard. Per-game record (final score) persisted to
--            quiz_attempts for personal best tracking.
--
--            Question bank lives entirely server-side so clients can't
--            cheat by peeking at the DOM. Host fetches N random
--            questions via RPC at game start, broadcasts them live.
--            Diverse category mix (K팝·연예·스포츠·상식·7080·2020 current)
--            so mixed-age parties aren't alienated.
-- =====================================================================

create table if not exists public.quiz_questions (
    id          bigserial   primary key,
    category    text        not null check (category in (
                                'kpop','variety','sports','general',
                                'retro','latest','history','world')),
    era         text        not null check (era in ('classic','modern','current')),
    difficulty  int         not null default 2 check (difficulty between 1 and 5),
    question    text        not null check (length(question) between 4 and 400),
    options     jsonb       not null,   -- ["A","B","C","D"] (exactly 4)
    correct     int         not null check (correct between 0 and 3),
    hint        text,                    -- optional one-liner shown on reveal
    source      text,                    -- credit or source tag, optional
    created_at  timestamptz not null default now(),
    constraint quiz_options_shape check (jsonb_typeof(options)='array' and jsonb_array_length(options)=4)
);
create index if not exists quiz_q_category_idx on public.quiz_questions (category);
create index if not exists quiz_q_era_idx      on public.quiz_questions (era);

alter table public.quiz_questions enable row level security;
drop policy if exists "quiz_questions_select" on public.quiz_questions;
create policy "quiz_questions_select"
    on public.quiz_questions for select using (true);


create table if not exists public.quiz_attempts (
    id              bigserial   primary key,
    user_id         uuid        not null references auth.users(id) on delete cascade,
    score           int         not null check (score >= 0 and score <= 99999999),
    correct_count   int         not null check (correct_count >= 0 and correct_count <= 100),
    total_count     int         not null check (total_count >= 1 and total_count <= 100),
    rank_in_room    int,
    room_size       int         check (room_size is null or room_size between 1 and 200),
    duration_ms     int         not null check (duration_ms between 0 and 3600000),
    categories      text[],
    created_at      timestamptz not null default now()
);
create index if not exists quiz_attempts_user_idx  on public.quiz_attempts (user_id, created_at desc);
create index if not exists quiz_attempts_score_idx on public.quiz_attempts (score desc);

alter table public.quiz_attempts enable row level security;
drop policy if exists "quiz_attempts_select_all" on public.quiz_attempts;
create policy "quiz_attempts_select_all"
    on public.quiz_attempts for select using (true);


create table if not exists public.quiz_records (
    user_id         uuid        primary key references auth.users(id) on delete cascade,
    best_score      int         not null,
    best_accuracy   int         not null default 0,   -- percent 0-100
    total_games     int         not null default 0,
    total_correct   int         not null default 0,
    total_questions int         not null default 0,
    updated_at      timestamptz not null default now()
);
create index if not exists quiz_records_best_idx on public.quiz_records (best_score desc);

alter table public.quiz_records enable row level security;
drop policy if exists "quiz_records_select_all" on public.quiz_records;
create policy "quiz_records_select_all"
    on public.quiz_records for select using (true);


create or replace function public._quiz_refresh_record()
returns trigger
language plpgsql security definer
set search_path = public
as $$
declare
    pct int;
begin
    pct := case when new.total_count > 0
                then least(100, greatest(0, (new.correct_count * 100) / new.total_count))
                else 0 end;
    insert into public.quiz_records
           (user_id, best_score, best_accuracy, total_games, total_correct, total_questions, updated_at)
    values (new.user_id, new.score, pct, 1, new.correct_count, new.total_count, now())
    on conflict (user_id) do update
      set best_score      = greatest(public.quiz_records.best_score, new.score),
          best_accuracy   = greatest(public.quiz_records.best_accuracy, pct),
          total_games     = public.quiz_records.total_games + 1,
          total_correct   = public.quiz_records.total_correct + new.correct_count,
          total_questions = public.quiz_records.total_questions + new.total_count,
          updated_at      = now();
    return new;
end;
$$;
drop trigger if exists quiz_refresh_record on public.quiz_attempts;
create trigger quiz_refresh_record
    after insert on public.quiz_attempts
    for each row execute function public._quiz_refresh_record();


-- RPC: fetch N random questions, optionally filtered by category list.
-- Public (callable by anon + authed) because the quiz room itself is
-- PIN-gated and the questions are not sensitive; letting anon guests
-- fetch a fresh shuffle is simpler than routing everything through the
-- host and re-broadcasting. Hard cap count=30 so a curious caller
-- can't scrape the whole bank with one call.
create or replace function public.quiz_random_questions(
    p_categories text[] default null,
    p_count      int    default 10
) returns setof public.quiz_questions
language sql security definer
set search_path = public
as $$
    select *
      from public.quiz_questions
     where (p_categories is null or array_length(p_categories,1) is null
            or category = any(p_categories))
     order by random()
     limit greatest(1, least(p_count, 30));
$$;
grant execute on function public.quiz_random_questions(text[], int) to authenticated, anon;


-- RPC: record a finished game. Server derives NOTHING on score here
-- because the score is already a deterministic function of the
-- correct_count + speed that the host aggregated during the live
-- match; pushing full per-question timing data into the DB just to
-- re-derive would blow up write volume with little benefit. We DO
-- clamp score to a sane ceiling so a compromised client can't submit
-- a billion. Rate-limit 30/hour/user as usual.
create or replace function public.record_quiz_attempt(
    p_score         int,
    p_correct_count int,
    p_total_count   int,
    p_rank_in_room  int,
    p_room_size     int,
    p_duration_ms   int,
    p_categories    text[]
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        prior_best int;
        recent_count int;
        clamped_score int;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    if p_total_count < 1 or p_total_count > 100 then raise exception 'bad_total'; end if;
    if p_correct_count < 0 or p_correct_count > p_total_count then raise exception 'bad_correct'; end if;
    if p_duration_ms < 1000 then raise exception 'too_short'; end if;
    if p_score < 0 then raise exception 'bad_score'; end if;

    /* Cap score at 2000 per question (correct 1000 + full speed 1000). */
    clamped_score := least(p_score, p_total_count * 2000);

    select count(*) into recent_count
      from public.quiz_attempts
     where user_id = me and created_at > now() - interval '1 hour';
    if recent_count >= 30 then raise exception 'rate_limited'; end if;

    select best_score into prior_best from public.quiz_records where user_id = me;

    insert into public.quiz_attempts
        (user_id, score, correct_count, total_count, rank_in_room,
         room_size, duration_ms, categories)
    values (me, clamped_score, p_correct_count, p_total_count,
            p_rank_in_room, p_room_size, p_duration_ms, p_categories);

    return jsonb_build_object(
        'ok', true,
        'score', clamped_score,
        'is_personal_best', prior_best is null or clamped_score > prior_best,
        'prior_best', coalesce(prior_best, 0)
    );
end;
$$;
grant execute on function public.record_quiz_attempt(int,int,int,int,int,int,text[]) to authenticated;


create or replace function public.quiz_leaderboard(
    p_scope text default 'world',
    p_limit int   default 50
) returns table (
    rnk             int,
    user_id         uuid,
    nickname        text,
    avatar_url      text,
    best_score      int,
    best_accuracy   int,
    total_games     int,
    achieved_at     timestamptz
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
            select (row_number() over (order by r.best_score desc, r.updated_at asc))::int,
                   r.user_id, p.nickname, p.avatar_url,
                   r.best_score, r.best_accuracy, r.total_games, r.updated_at
            from public.quiz_records r
            join public.profiles p on p.id = r.user_id
            order by r.best_score desc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id, max(score) as best_today, min(created_at) as first_at
                from public.quiz_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            )
            select (row_number() over (order by t.best_today desc, t.first_at asc))::int,
                   t.user_id, p.nickname, p.avatar_url,
                   t.best_today, coalesce(r.best_accuracy,0), coalesce(r.total_games,0), t.first_at
            from today_attempts t
            join public.profiles p on p.id = t.user_id
            left join public.quiz_records r on r.user_id = t.user_id
            order by t.best_today desc, t.first_at asc
            limit greatest(1, least(p_limit, 100));
    else
        return query
            with friend_ids as (
                select case when user_a = me then user_b else user_a end as fid
                from public.friendships
                where (user_a = me or user_b = me) and status = 'accepted'
                union
                select me
            )
            select (row_number() over (order by r.best_score desc, r.updated_at asc))::int,
                   r.user_id, p.nickname, p.avatar_url,
                   r.best_score, r.best_accuracy, r.total_games, r.updated_at
            from public.quiz_records r
            join public.profiles p on p.id = r.user_id
            where r.user_id in (select fid from friend_ids)
            order by r.best_score desc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.quiz_leaderboard(text, int) to authenticated, anon;


-- =====================================================================
-- Initial question bank — ~60 questions across 7 categories mixing
-- classic (90/00년대), modern (2010s), and current (2020~2026) eras
-- so parties with both 20대 and 40/50대 keep everyone engaged.
-- answers order is fixed in the `options` array; `correct` is the
-- 0-based index. Sources omitted for brevity.
-- =====================================================================

insert into public.quiz_questions (category, era, difficulty, question, options, correct) values
  -- K-POP — classic
  ('kpop','classic',2,'1990년대를 대표하는 혼성 듀오 "너에게 난, 나에게 넌"을 부른 그룹은?',   '["자전거 탄 풍경","유재하 앤드 이소라","오석준","롤러코스터"]'::jsonb, 0),
  ('kpop','classic',3,'H.O.T.의 데뷔 앨범 타이틀곡은?',                                    '["캔디","전사의 후예","행복","We Are The Future"]'::jsonb, 1),
  ('kpop','classic',2,'핑클의 리더이자 센터였던 멤버는?',                                    '["이진","이효리","옥주현","성유리"]'::jsonb, 1),
  ('kpop','classic',3,'서태지와 아이들의 은퇴 당시 마지막 앨범 타이틀곡은?',                   '["Come Back Home","교실 이데아","필승","하여가"]'::jsonb, 0),
  -- K-POP — modern
  ('kpop','modern',2,'BLACKPINK 멤버가 아닌 사람은?',                                        '["지수","제니","로제","미나"]'::jsonb, 3),
  ('kpop','modern',2,'BTS의 데뷔 연도는?',                                                   '["2011년","2012년","2013년","2014년"]'::jsonb, 2),
  ('kpop','modern',3,'TWICE의 데뷔곡은?',                                                    '["CHEER UP","TT","OOH-AHH하게","LIKEY"]'::jsonb, 2),
  ('kpop','modern',3,'싸이의 "강남스타일"이 유튜브에서 10억 뷰를 넘긴 해는?',                  '["2012년","2013년","2014년","2015년"]'::jsonb, 0),
  -- K-POP — current (2023~2026)
  ('kpop','current',3,'뉴진스가 소속된 기획사는?',                                            '["SM","JYP","HYBE 산하 ADOR","YG"]'::jsonb, 2),
  ('kpop','current',3,'2024년 걸그룹 데뷔한 ILLIT 소속사는?',                                '["HYBE","SM","JYP","빅히트 뮤직"]'::jsonb, 0),
  ('kpop','current',3,'"Super Shy"를 부른 그룹은?',                                           '["NewJeans","IVE","aespa","LE SSERAFIM"]'::jsonb, 0),
  ('kpop','current',4,'aespa 멤버 중 카리나의 본명은?',                                       '["유지민","지젤","김민정","닝닝"]'::jsonb, 0),

  -- 연예 (drama, variety)
  ('variety','classic',2,'"무한도전" MC로 가장 오래 활동한 인물은?',                           '["박명수","정준하","유재석","노홍철"]'::jsonb, 2),
  ('variety','classic',3,'"1박2일" 시즌 1의 PD로 유명한 사람은?',                             '["나영석","신원호","김태호","이명한"]'::jsonb, 0),
  ('variety','modern',2,'"런닝맨" 고정 멤버 중 "왕코"로 불리는 사람은?',                      '["김종국","이광수","하하","지석진"]'::jsonb, 1),
  ('variety','current',2,'2024년 화제의 "흑백요리사"에 출연한 유명 셰프가 아닌 사람은?',        '["이연복","최현석","에드워드 리","강호동"]'::jsonb, 3),
  ('variety','current',3,'2023~24 화제의 드라마 "선재 업고 튀어" 주인공 남자 배우는?',          '["변우석","박형식","송강","남주혁"]'::jsonb, 0),
  ('variety','modern',3,'"기생충"으로 아카데미 작품상을 받은 감독은?',                         '["박찬욱","봉준호","김지운","이창동"]'::jsonb, 1),
  ('variety','current',3,'넷플릭스 "오징어 게임"의 감독은?',                                   '["봉준호","황동혁","연상호","류승완"]'::jsonb, 1),

  -- 스포츠
  ('sports','classic',2,'"야구의 신"으로 불리는 한국 야구 전설은?',                            '["이승엽","선동열","박찬호","양준혁"]'::jsonb, 1),
  ('sports','classic',2,'2002 한일 월드컵 한국 축구 대표팀 감독은?',                           '["히딩크","박항서","허정무","최용수"]'::jsonb, 0),
  ('sports','modern',2,'손흥민이 주장으로 뛰는 EPL 클럽은?',                                   '["맨체스터 유나이티드","토트넘","첼시","아스날"]'::jsonb, 1),
  ('sports','modern',3,'류현진이 MLB에 데뷔한 팀은?',                                         '["LA 다저스","토론토 블루제이스","피츠버그","뉴욕 메츠"]'::jsonb, 0),
  ('sports','current',3,'2024 파리 올림픽 한국 양궁 여자 단체전 결과는?',                      '["금메달","은메달","동메달","4강 탈락"]'::jsonb, 0),
  ('sports','current',4,'손흥민이 2023-24 시즌 EPL 득점 순위 몇 위에 올랐나?',                 '["1위","2위","3위","4위"]'::jsonb, 2),
  ('sports','modern',3,'박지성이 뛴 EPL 팀은?',                                                '["첼시","맨체스터 시티","맨체스터 유나이티드","리버풀"]'::jsonb, 2),

  -- 일반 상식
  ('general','classic',1,'대한민국의 수도는?',                                                 '["부산","서울","인천","대구"]'::jsonb, 1),
  ('general','classic',2,'태양계에서 가장 큰 행성은?',                                         '["지구","목성","토성","해왕성"]'::jsonb, 1),
  ('general','classic',2,'인간 DNA의 염기 수는 대략 몇 개?',                                   '["30억 쌍","3천만 쌍","30억 개 단일가닥","3억 쌍"]'::jsonb, 0),
  ('general','classic',3,'빛의 속도는 초속 약 몇 km?',                                         '["3만","30만","300만","3000만"]'::jsonb, 1),
  ('general','modern',2,'ChatGPT를 만든 회사는?',                                              '["Google","OpenAI","Meta","Anthropic"]'::jsonb, 1),
  ('general','current',3,'2024년 노벨 평화상 수상자 단체는?',                                  '["WHO","일본 원수폭피해자단체협의회","UN 난민기구","국경없는의사회"]'::jsonb, 1),
  ('general','current',3,'2024년 한국에서 가장 많이 팔린 자동차 브랜드는?',                    '["현대","기아","테슬라","BMW"]'::jsonb, 0),
  ('general','classic',2,'"햄릿"을 쓴 작가는?',                                                '["셰익스피어","찰스 디킨스","토마스 하디","조지 오웰"]'::jsonb, 0),
  ('general','classic',3,'한국에서 발명된 금속활자는?',                                        '["직지심체요절","훈민정음","고려대장경","조선왕조실록"]'::jsonb, 0),

  -- 7080·90·00 추억 (retro)
  ('retro','classic',2,'1990년대 인기 애니메이션 "천사소녀 네티"의 한국어 주제가를 부른 사람은?', '["이선희","장혜진","박선주","박정현"]'::jsonb, 2),
  ('retro','classic',3,'"응답하라 1988"의 주인공 덕선이 역을 맡은 배우는?',                    '["박보검","류혜영","혜리","김새론"]'::jsonb, 2),
  ('retro','classic',2,'80년대 "태양은 가득히"를 부른 가수는?',                                '["전영록","김흥국","김수철","최성수"]'::jsonb, 0),
  ('retro','classic',3,'1994년 월드컵에서 홍명보가 골을 넣은 상대팀은?',                       '["스페인","독일","볼리비아","미국"]'::jsonb, 3),
  ('retro','classic',2,'추억의 게임 "메이플스토리"가 출시된 해는?',                            '["2001년","2003년","2005년","2007년"]'::jsonb, 1),
  ('retro','classic',3,'"라면공장", "응가게", "총게임" — 이 게임들이 공통으로 돌아가던 기기는?', '["플레이스테이션","오락실(아케이드)","PC방","닌텐도"]'::jsonb, 1),

  -- 한국사·지리
  ('history','classic',2,'조선을 건국한 사람은?',                                              '["이성계","이방원","정도전","왕건"]'::jsonb, 0),
  ('history','classic',2,'세종대왕이 만든 문자는?',                                            '["한자","한글(훈민정음)","이두","구결"]'::jsonb, 1),
  ('history','classic',3,'임진왜란이 일어난 해는?',                                            '["1392년","1492년","1592년","1692년"]'::jsonb, 2),
  ('history','classic',2,'한국의 가장 큰 섬은?',                                                '["제주도","울릉도","강화도","거제도"]'::jsonb, 0),
  ('history','classic',3,'고구려를 세운 인물은?',                                              '["김유신","온조","주몽(동명성왕)","박혁거세"]'::jsonb, 2),
  ('history','classic',2,'광복절은 몇 월 며칠?',                                                '["3월 1일","6월 25일","8월 15일","10월 3일"]'::jsonb, 2),

  -- 세계 상식
  ('world','classic',2,'"자유의 여신상"을 미국에 선물한 나라는?',                              '["영국","프랑스","스페인","독일"]'::jsonb, 1),
  ('world','classic',2,'세계에서 가장 긴 강은?',                                                '["나일강","아마존강","양쯔강","미시시피강"]'::jsonb, 0),
  ('world','classic',3,'달에 처음 착륙한 우주인은?',                                            '["유리 가가린","닐 암스트롱","버즈 올드린","존 글렌"]'::jsonb, 1),
  ('world','modern',2,'UN 본부가 있는 도시는?',                                                '["런던","파리","뉴욕","제네바"]'::jsonb, 2),
  ('world','classic',2,'세계에서 가장 큰 나라 (면적 기준)는?',                                  '["중국","미국","러시아","캐나다"]'::jsonb, 2),
  ('world','current',3,'2024년 기준 세계 인구 1위 국가는?',                                    '["중국","인도","미국","인도네시아"]'::jsonb, 1),

  -- 최신 시사 (latest)
  ('latest','current',3,'2024년 화제가 된 AI 영상 생성 도구 "Sora"를 만든 회사는?',              '["Google DeepMind","OpenAI","Meta","Runway"]'::jsonb, 1),
  ('latest','current',3,'2024년 한국 1인 가구 비율은 대략?',                                    '["20%","30%","40%","50%"]'::jsonb, 2),
  ('latest','current',3,'2025년 현재 삼성전자 회장은?',                                         '["이재용","이건희","김기남","한종희"]'::jsonb, 0),
  ('latest','current',4,'2024년 노벨 문학상 수상자는?',                                         '["무라카미 하루키","한강","마거릿 애트우드","살만 루슈디"]'::jsonb, 1),
  ('latest','current',3,'아이폰 15 시리즈의 커넥터 타입은?',                                    '["Lightning","USB-C","MagSafe","Thunderbolt"]'::jsonb, 1)
on conflict do nothing;
