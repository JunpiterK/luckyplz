-- =====================================================================
-- Migration: Seed leaderboards with 200 synthetic users — one-time
-- Date:      2026-05-10
-- Purpose:   모든 액션 게임 (snake, pacman, burger, dodge, tetris,
--            tetris-sprint, reaction, quiz) 의 랭킹 보드를 200명의 가상
--            유저 데이터로 채워서 신규 유저가 입장했을 때 텅 빈 leaderboard
--            가 아니라 활기찬 경쟁 환경을 보게 함.
--
-- 닉네임:    영어 표기 200개, 다양한 국가권 분포 (Western/EU/Hispanic/
--            East Asian/South Asian/MENA/Africa/Gamer-style 혼합).
--            profiles.nickname 제약 (^[A-Za-z0-9_\-가-힣]+$, 2-20자) 준수.
--            unique on lower(nickname) 도 확인.
--
-- 점수:      각 게임별 현실적 분포 — top 1% 는 매우 어렵게 도달, 평범한
--            플레이어가 대부분 모이는 mid-tier, 짧은 시도들이 bottom.
--            decay = pow(1 - (rank-1)/199, 2.2) 로 부드러운 power curve.
--            게임별 user 순열은 hashtextextended(uid + game_key) 기반
--            deterministic — 같은 유저가 여러 게임에서 동일 순위가 아니라
--            게임마다 다르게 분포 (현실적: tetris 잘하는 사람이 reaction
--            도 잘하지는 않음).
--
-- 멱등성:    ON CONFLICT DO NOTHING — 재실행해도 안전. 단 처음 실행 후
--            데이터 변경하려면 먼저 cleanup (이메일 'seed_%@luckyplz.local'
--            패턴 으로 식별).
--
-- 롤백:      delete from auth.users where email like 'seed_%@luckyplz.local';
--            (cascade 로 profiles + 모든 _records 자동 삭제)
--
-- 주의:      auth.users 는 Supabase Auth 가 관리하지만 service_role/SQL
--            editor 로는 직접 INSERT 가능. 비밀번호는 의미 없는 dummy
--            (이 user 들은 영원히 로그인 안 함). MAU 빌링 영향 없음.
-- =====================================================================

-- pgcrypto 확장 (crypt + gen_salt) 보장 — Supabase 기본 활성화되어있음
create extension if not exists pgcrypto;

do $$
declare
    /* 200 다양한 영어권/국제 닉네임. profiles.nickname 제약 준수
       (영문/숫자/_/- 만, 2-20자). 중복 없도록 신중히 큐레이션. */
    seed_names text[] := array[
        -- Western Anglophone (40)
        'AlexK','MikeJordan','SamWest','JakeR42','RyanT','TomHill','BenN','JackBauer',
        'LiamGray','NoahP','EthanW','LoganX','MasonV','LucasFox','HenryQ','OwenK',
        'CalebJ','WyattZ','DylanM','CarterB','SarahJ','EmmaR','OliviaR','AvaSterling',
        'MiaMoon','SophiaL','IsabellaP','Charlotte7','AmeliaC','HarperT','EvelynS','AriaY',
        'LaylaW','LilyK','ZoeR','HannahB','RileyJ','AubreyM','EllieD','StellaN',
        -- European (30)
        'LucaB','MarcoP','PietroV','GiuliaR','AndreaT','MattiaC','HansSchmidt','KlausK',
        'OttoM','FriedrichZ','WolfgangX','PierreL','AntoineV','OlivierM','CamilleR','MathieuG',
        'ErikS','LarsN','BjornT','MagnusH','AndersK','FinnD','KarlSt','AntonV',
        'PavelM','IgorN','NikolaiS','SergeiK','YevgeniL','BorisP',
        -- Hispanic/Latino (25)
        'CarlosM','DiegoR','MateoH','SebastianP','PabloV','RicardoT','JavierM','FelipeC',
        'RafaelN','EduardoQ','ManuelG','AntonioS','LuciaR','CamilaF','ValeriaT','GabrielaP',
        'IsabelM','CatalinaV','RenataB','AlejandraR','MarianaG','DanielaH','LunaV','SofiaG',
        'AndreaM',
        -- East Asian (35)
        'HiroshiT','KenjiN','AkiraM','YukiW','SoraK','KaitoF','RenS','RikuO',
        'DaichiH','MeiC','YuiT','SakiM','AoiK','HanaR','WeiL','LinXi',
        'JunZ','MingyuC','BohanW','KazukiS','TakeshiI','MinHo','JunhoP','KyungS',
        'DaehoK','SunghoJ','JihoL','JaewonY','SubinR','YunaP','SoobinK','JiwooM',
        'HaeunC','MingooN','YejunR',
        -- South Asian (15)
        'ArjunR','AdityaS','VikramK','RohanG','KaranM','AryanT','RaviN','KrishnaP',
        'PriyaB','MayaR','TaraS','AnikaK','KavyaM','AishaP','RiyaJ',
        -- MENA / Africa (15)
        'OmarH','AliM','HassanK','LaylaN','ZainR','KarimT','YasminQ','AmalS',
        'FaisalP','TariqV','KofiB','AmaraD','KwameO','ZolaN','TundeA',
        -- Gamer-style handles (40)
        'NeonRider','ShadowFox42','IronFist7','NightHawk_X','VortexZ','NovaStrike',
        'BlazeKing88','FrostByte','GhostWalker','PhantomZ9','MysticDragon','TitanSlash',
        'RogueOne7','ThunderBolt','StormChaser','PixelKnight','ApexPred','SkyRunner',
        'FireStarter','DeepFreeze','WildCard_R','Cipher77','Quasar88','Vector42',
        'Pulse99','Echo7Beta','Zen13K','Atlas21','Phoenix5R','MercuryD',
        'CometRZ','MetaSlash','OrbitX','LunarKnt','SolarFlare1','GalaxyZ',
        'StellarPro','NebulaQ','CosmicAce','VoidWalker'
    ];

    /* 각 user 의 deterministic UUID — gen_random_uuid 는 매 호출 다른 값
       이지만 한 트랜잭션 내에서 array 에 caching 해두면 일관됨. */
    seed_uids uuid[];
    cnt int;
    i int;
    uid uuid;
    nm text;
    seed_email text;
begin
    /* 이미 seed 가 들어있으면 abort — 멱등 안전장치 (재실행 시 중복 회피).
       cleanup 을 원하면 위 헤더 주석의 delete 명령 먼저 실행. */
    select count(*) into cnt
    from auth.users
    where email like 'seed_%@luckyplz.local';
    if cnt >= 200 then
        raise notice 'Seed users already present (% rows). Skipping insert. To re-seed, run delete from auth.users where email like ''seed_%%@luckyplz.local''; first.', cnt;
        return;
    end if;

    if array_length(seed_names, 1) <> 200 then
        raise exception 'Seed name array must have exactly 200 entries (got %)', array_length(seed_names, 1);
    end if;

    /* 200 UUID 미리 생성 → array 에 보관해서 후속 INSERT 들이 같은 UUID 참조 */
    seed_uids := array(select gen_random_uuid() from generate_series(1, 200));

    /* ---- 1) auth.users — 최소 컬럼 + Supabase 기본값 활용 ---- */
    for i in 1..200 loop
        uid := seed_uids[i];
        seed_email := 'seed_' || lpad(i::text, 3, '0') || '@luckyplz.local';
        insert into auth.users
            (instance_id, id, aud, role, email, encrypted_password,
             email_confirmed_at, raw_app_meta_data, raw_user_meta_data,
             created_at, updated_at, is_anonymous, is_sso_user)
        values
            ('00000000-0000-0000-0000-000000000000', uid,
             'authenticated', 'authenticated', seed_email,
             crypt('seed-' || i::text || '-' || md5(random()::text), gen_salt('bf')),
             now() - (random() * interval '60 days'),
             '{"provider":"email","providers":["email"]}'::jsonb,
             jsonb_build_object('seed', true, 'rank_seed_idx', i),
             now() - (random() * interval '60 days'),
             now(), false, false)
        on conflict (id) do nothing;
    end loop;

    /* ---- 2) profiles — nickname 은 seed_names 에서 ---- */
    for i in 1..200 loop
        uid := seed_uids[i];
        nm  := seed_names[i];
        insert into public.profiles
            (id, nickname, profile_complete, created_at, updated_at)
        values
            (uid, nm, true,
             now() - (random() * interval '60 days'),
             now() - (random() * interval '30 days'))
        on conflict (id) do nothing;
    end loop;

    raise notice 'Inserted 200 seed users + profiles.';
end $$;


-- =====================================================================
-- 게임별 records 시드. 각 user 의 게임별 순위는 hashtextextended(uid + game)
-- 으로 부여 — 같은 유저가 game 마다 다른 rank. decay 곡선:
--   normalized t = (rnk - 1) / 199    -- 0..1
--   score = bottom + (top - bottom) * power(1 - t, 2.2)
-- (Lower-is-better 게임 — sprint/reaction — 은 반대로 top + (bottom-top) * power(t, 2.2))
-- 약 ±5% noise 추가 (deterministic hash 로) 해서 깔끔하게 떨어지지 않게.
-- =====================================================================

/* helper — common rank → noise multiplier. ±5% 변동, deterministic. */
-- (인라인으로 SQL 안에 mod-hash 식 사용)


-- 각 게임 섹션은 do 블록 + to_regclass() 검사로 wrap 되어있어 schema 가
-- 배포되지 않은 게임은 자동 skip 됨. 일부 사이트에 reaction 게임 미배포
-- 인 케이스 등에 대비.

-- ----- 1) SNAKE: best_score = foods_eaten * 10. realistic top ~1500. -----
do $seed_snake$
begin
    if to_regclass('public.snake_records') is null then
        raise notice 'snake_records not found, skipping';
        return;
    end if;
    execute $sql$
        with ranked as (
            select id as uid,
                   row_number() over (
                       order by hashtextextended(id::text || 'snake', 1) asc
                   ) as rnk
            from public.profiles
            where id in (select id from auth.users where email like 'seed_%@luckyplz.local')
        ),
        scored as (
            select uid, rnk,
                   greatest(20, (50 + round((1500.0 - 50) * power(1 - (rnk - 1)::numeric / 199, 2.2))
                        ) * (1.0 + ((abs(hashtextextended(uid::text||'snk_n', 0)) % 100) - 50) / 1000.0)
                   )::int as bs
            from ranked
        )
        insert into public.snake_records
            (user_id, best_score, best_foods_eaten, total_games, total_playtime_ms, updated_at)
        select uid,
               bs,
               (bs / 10)::int,
               greatest(3, (60 - rnk / 4) + (abs(hashtextextended(uid::text||'snk_g', 0)) % 20))::int,
               (90000 * greatest(3, (60 - rnk / 4) + (abs(hashtextextended(uid::text||'snk_g', 0)) % 20)))::bigint,
               now() - (rnk * interval '20 minutes')
        from scored
        on conflict (user_id) do nothing;
    $sql$;
end $seed_snake$;


-- ----- 2) PACMAN: realistic top ~220k, mid 30k, bottom 1.5k. -----
do $seed_pacman$
begin
    if to_regclass('public.pacman_records') is null then
        raise notice 'pacman_records not found, skipping';
        return;
    end if;
    execute $sql$
        with ranked as (
            select id as uid,
                   row_number() over (
                       order by hashtextextended(id::text || 'pacman', 2) asc
                   ) as rnk
            from public.profiles
            where id in (select id from auth.users where email like 'seed_%@luckyplz.local')
        ),
        scored as (
            select uid, rnk,
                   greatest(500, (1500 + round((220000.0 - 1500) * power(1 - (rnk - 1)::numeric / 199, 2.2))
                        ) * (1.0 + ((abs(hashtextextended(uid::text||'pac_n', 0)) % 100) - 50) / 1000.0)
                   )::int as bs
            from ranked
        )
        insert into public.pacman_records
            (user_id, best_score, total_games, total_wins, total_playtime_ms, updated_at)
        select uid,
               bs,
               greatest(2, (50 - rnk / 5) + (abs(hashtextextended(uid::text||'pac_g', 0)) % 18))::int,
               case when rnk <= 30 then (abs(hashtextextended(uid::text||'pac_w', 0)) % 4)
                    when rnk <= 80 then (abs(hashtextextended(uid::text||'pac_w', 0)) % 2)
                    else 0 end,
               (140000 * greatest(2, (50 - rnk / 5) + (abs(hashtextextended(uid::text||'pac_g', 0)) % 18)))::bigint,
               now() - (rnk * interval '25 minutes')
        from scored
        on conflict (user_id) do nothing;
    $sql$;
end $seed_pacman$;


-- ----- 3) BURGER (BurgerTime): top ~150k, level 30 cap. -----
do $seed_burger$
begin
    if to_regclass('public.burger_records') is null then
        raise notice 'burger_records not found, skipping';
        return;
    end if;
    execute $sql$
        with ranked as (
            select id as uid,
                   row_number() over (
                       order by hashtextextended(id::text || 'burger', 3) asc
                   ) as rnk
            from public.profiles
            where id in (select id from auth.users where email like 'seed_%@luckyplz.local')
        ),
        scored as (
            select uid, rnk,
                   greatest(800, (2000 + round((150000.0 - 2000) * power(1 - (rnk - 1)::numeric / 199, 2.2))
                        ) * (1.0 + ((abs(hashtextextended(uid::text||'bur_n', 0)) % 100) - 50) / 1000.0)
                   )::int as bs
            from ranked
        )
        insert into public.burger_records
            (user_id, best_score, best_level, total_games, total_burgers, total_playtime_ms, updated_at)
        select uid,
               bs,
               case when rnk <= 10 then 20 + (abs(hashtextextended(uid::text||'bur_lv', 0)) % 11)
                    when rnk <= 50 then 10 + (abs(hashtextextended(uid::text||'bur_lv', 0)) % 11)
                    when rnk <= 120 then 4 + (abs(hashtextextended(uid::text||'bur_lv', 0)) % 8)
                    else 1 + (abs(hashtextextended(uid::text||'bur_lv', 0)) % 5) end,
               greatest(2, (45 - rnk / 5) + (abs(hashtextextended(uid::text||'bur_g', 0)) % 16))::int,
               (4 * greatest(2, (45 - rnk / 5) + (abs(hashtextextended(uid::text||'bur_g', 0)) % 16)))::int,
               (180000 * greatest(2, (45 - rnk / 5) + (abs(hashtextextended(uid::text||'bur_g', 0)) % 16)))::bigint,
               now() - (rnk * interval '30 minutes')
        from scored
        on conflict (user_id) do nothing;
    $sql$;
end $seed_burger$;


-- ----- 4) DODGE (Space-Z): score = 10 pts/sec, 20분 cap = 12000.
-- 4분 cap (2400) 도달이 진입 장벽. phase 2 상승 (+80%) 으로 12000 거의 불가능.
-- top 5-10 명만 8000+, mid 는 2000-5000 (4-8분), bottom 은 200-1500. -----
do $seed_dodge$
begin
    if to_regclass('public.dodge_records') is null then
        raise notice 'dodge_records not found, skipping';
        return;
    end if;
    execute $sql$
        with ranked as (
            select id as uid,
                   row_number() over (
                       order by hashtextextended(id::text || 'dodge', 4) asc
                   ) as rnk
            from public.profiles
            where id in (select id from auth.users where email like 'seed_%@luckyplz.local')
        ),
        scored as (
            select uid, rnk,
                   case when rnk <= 3 then 11000 + (abs(hashtextextended(uid::text||'dge_top', 0)) % 900)
                        when rnk <= 10 then 7500 + (abs(hashtextextended(uid::text||'dge_t10', 0)) % 3500)
                        when rnk <= 30 then 4000 + (abs(hashtextextended(uid::text||'dge_t30', 0)) % 3500)
                        when rnk <= 80 then 1500 + (abs(hashtextextended(uid::text||'dge_t80', 0)) % 2500)
                        when rnk <= 150 then 500 + (abs(hashtextextended(uid::text||'dge_t150', 0)) % 1000)
                        else 100 + (abs(hashtextextended(uid::text||'dge_btm', 0)) % 400)
                   end as bs
            from ranked
        )
        insert into public.dodge_records
            (user_id, best_score, total_games, total_playtime_ms, updated_at)
        select uid,
               bs,
               greatest(2, (40 - rnk / 6) + (abs(hashtextextended(uid::text||'dge_g', 0)) % 14))::int,
               (bs * 100 * greatest(2, (40 - rnk / 6) + (abs(hashtextextended(uid::text||'dge_g', 0)) % 14)) * 6 / 10)::bigint,
               now() - (rnk * interval '15 minutes')
        from scored
        on conflict (user_id) do nothing;
    $sql$;
end $seed_dodge$;


-- ----- 5) TETRIS (Marathon): top ~1.5M, mid 100k, bottom 5k. -----
do $seed_tetris$
begin
    if to_regclass('public.tetris_records') is null then
        raise notice 'tetris_records not found, skipping';
        return;
    end if;
    execute $sql$
        with ranked as (
            select id as uid,
                   row_number() over (
                       order by hashtextextended(id::text || 'tetris', 5) asc
                   ) as rnk
            from public.profiles
            where id in (select id from auth.users where email like 'seed_%@luckyplz.local')
        ),
        scored as (
            select uid, rnk,
                   greatest(2000, (5000 + round((1500000.0 - 5000) * power(1 - (rnk - 1)::numeric / 199, 2.2))
                        ) * (1.0 + ((abs(hashtextextended(uid::text||'tet_n', 0)) % 100) - 50) / 1000.0)
                   )::int as bs
            from ranked
        )
        insert into public.tetris_records
            (user_id, best_score, best_lines, best_level, total_games, total_lines, total_playtime_ms, updated_at)
        select uid,
               bs,
               (bs / 2000)::int + (abs(hashtextextended(uid::text||'tet_l', 0)) % 30),
               case when rnk <= 10 then 18 + (abs(hashtextextended(uid::text||'tet_lv', 0)) % 13)
                    when rnk <= 50 then 8 + (abs(hashtextextended(uid::text||'tet_lv', 0)) % 12)
                    when rnk <= 130 then 3 + (abs(hashtextextended(uid::text||'tet_lv', 0)) % 8)
                    else 1 + (abs(hashtextextended(uid::text||'tet_lv', 0)) % 4) end,
               greatest(3, (60 - rnk / 4) + (abs(hashtextextended(uid::text||'tet_g', 0)) % 20))::int,
               (80 * greatest(3, (60 - rnk / 4) + (abs(hashtextextended(uid::text||'tet_g', 0)) % 20)))::bigint,
               (240000 * greatest(3, (60 - rnk / 4) + (abs(hashtextextended(uid::text||'tet_g', 0)) % 20)))::bigint,
               now() - (rnk * interval '35 minutes')
        from scored
        on conflict (user_id) do nothing;
    $sql$;
end $seed_tetris$;


-- ----- 6) TETRIS SPRINT (40 line 클리어 시간, LOWER better):
-- top ~28s (28000ms), bottom ~5분 (300000ms). -----
do $seed_sprint$
begin
    if to_regclass('public.tetris_sprint_records') is null then
        raise notice 'tetris_sprint_records not found, skipping';
        return;
    end if;
    execute $sql$
        with ranked as (
            select id as uid,
                   row_number() over (
                       order by hashtextextended(id::text || 'tspr', 6) asc
                   ) as rnk
            from public.profiles
            where id in (select id from auth.users where email like 'seed_%@luckyplz.local')
        ),
        scored as (
            select uid, rnk,
                   greatest(25000, (28000 + round((300000.0 - 28000) * power((rnk - 1)::numeric / 199, 2.2))
                        ) * (1.0 + ((abs(hashtextextended(uid::text||'tsp_n', 0)) % 100) - 50) / 1000.0)
                   )::int as ms
            from ranked
        )
        insert into public.tetris_sprint_records
            (user_id, best_duration_ms, total_completes, total_playtime_ms, achieved_at, updated_at)
        select uid,
               ms,
               greatest(1, (35 - rnk / 6) + (abs(hashtextextended(uid::text||'tsp_g', 0)) % 12))::int,
               (ms * greatest(1, (35 - rnk / 6) + (abs(hashtextextended(uid::text||'tsp_g', 0)) % 12)))::bigint,
               now() - (rnk * interval '40 minutes'),
               now() - (rnk * interval '40 minutes')
        from scored
        on conflict (user_id) do nothing;
    $sql$;
end $seed_sprint$;


-- ----- 7) REACTION (반응속도 ms, LOWER better):
-- top 195ms (사람 신경 한계), bottom 380ms (느린 모바일 + 고민형).
-- ⚠ 이 게임은 사이트에 미배포 케이스 다수 — 테이블 없으면 자동 skip. -----
do $seed_reaction$
begin
    if to_regclass('public.reaction_records') is null then
        raise notice 'reaction_records not found (게임 미배포), skipping';
        return;
    end if;
    execute $sql$
        with ranked as (
            select id as uid,
                   row_number() over (
                       order by hashtextextended(id::text || 'react', 7) asc
                   ) as rnk
            from public.profiles
            where id in (select id from auth.users where email like 'seed_%@luckyplz.local')
        ),
        scored as (
            select uid, rnk,
                   greatest(180, (195 + round((380.0 - 195) * power((rnk - 1)::numeric / 199, 1.6))
                        ) + ((abs(hashtextextended(uid::text||'rct_n', 0)) % 20) - 10)
                   )::int as ms
            from ranked
        )
        insert into public.reaction_records
            (user_id, best_ms, total_attempts, avg_ms, updated_at)
        select uid,
               ms,
               greatest(3, (35 - rnk / 8) + (abs(hashtextextended(uid::text||'rct_a', 0)) % 15))::int,
               (ms + 30 + (abs(hashtextextended(uid::text||'rct_avg', 0)) % 50))::int,
               now() - (rnk * interval '12 minutes')
        from scored
        on conflict (user_id) do nothing;
    $sql$;
end $seed_reaction$;


-- ----- 8) QUIZ (correct_count * 점수 multiplier):
-- top ~25000 (모든 라운드 정답), bottom 800. -----
do $seed_quiz$
begin
    if to_regclass('public.quiz_records') is null then
        raise notice 'quiz_records not found, skipping';
        return;
    end if;
    execute $sql$
        with ranked as (
            select id as uid,
                   row_number() over (
                       order by hashtextextended(id::text || 'quiz', 8) asc
                   ) as rnk
            from public.profiles
            where id in (select id from auth.users where email like 'seed_%@luckyplz.local')
        ),
        scored as (
            select uid, rnk,
                   greatest(300, (800 + round((25000.0 - 800) * power(1 - (rnk - 1)::numeric / 199, 2.0))
                        ) * (1.0 + ((abs(hashtextextended(uid::text||'qz_n', 0)) % 100) - 50) / 1000.0)
                   )::int as bs
            from ranked
        )
        insert into public.quiz_records
            (user_id, best_score, best_accuracy, total_games, total_correct, total_questions, updated_at)
        select uid,
               bs,
               case when rnk <= 20 then 88 + (abs(hashtextextended(uid::text||'qz_acc', 0)) % 13)
                    when rnk <= 80 then 65 + (abs(hashtextextended(uid::text||'qz_acc', 0)) % 25)
                    when rnk <= 150 then 45 + (abs(hashtextextended(uid::text||'qz_acc', 0)) % 25)
                    else 25 + (abs(hashtextextended(uid::text||'qz_acc', 0)) % 25) end,
               greatest(2, (40 - rnk / 6) + (abs(hashtextextended(uid::text||'qz_g', 0)) % 14))::int,
               (7 * greatest(2, (40 - rnk / 6) + (abs(hashtextextended(uid::text||'qz_g', 0)) % 14)))::int,
               (10 * greatest(2, (40 - rnk / 6) + (abs(hashtextextended(uid::text||'qz_g', 0)) % 14)))::int,
               now() - (rnk * interval '18 minutes')
        from scored
        on conflict (user_id) do nothing;
    $sql$;
end $seed_quiz$;


-- =====================================================================
-- 검증
-- =====================================================================
do $$
declare
    n_users int;
    n_profiles int;
    /* 게임별 카운트 — 테이블 없으면 -1 (미배포) 표시. */
    games text[] := array['snake_records','pacman_records','burger_records',
                          'dodge_records','tetris_records','tetris_sprint_records',
                          'reaction_records','quiz_records'];
    g text;
    cnt int;
begin
    select count(*) into n_users
        from auth.users where email like 'seed_%@luckyplz.local';
    select count(*) into n_profiles
        from public.profiles where id in (
            select id from auth.users where email like 'seed_%@luckyplz.local');

    raise notice E'\n============================================\n  Seed Leaderboard Migration Result\n============================================';
    raise notice 'auth.users    : %', n_users;
    raise notice 'profiles      : %', n_profiles;

    foreach g in array games
    loop
        if to_regclass('public.' || g) is null then
            raise notice '% : (미배포 — table not found)', rpad(g, 22);
        else
            execute format(
                'select count(*) from public.%I r where r.user_id in (select id from auth.users where email like ''seed_%%@luckyplz.local'')',
                g
            ) into cnt;
            raise notice '% : %', rpad(g, 22), cnt;
        end if;
    end loop;

    raise notice E'\n각 카운트는 200 이어야 정상. 미배포 게임은 자동 skip 됨.\n낮은 숫자 = 기존 데이터로 ON CONFLICT 발동 또는 check 제약 실패 (raise log 확인).';
end $$;
