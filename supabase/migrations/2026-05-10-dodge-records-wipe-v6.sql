-- =====================================================================
-- Migration: Dodge (Space-Z) records wipe — v6 difficulty rebalance
-- Date:      2026-05-10
-- Purpose:   2026-05-10 까지 진행된 Space-Z 대규모 리워크 (Sprint A-I 20-zone
--            로드맵 + difficulty v6 phase 2) 로 게임 자체의 난이도/길이 곡선이
--            크게 달라짐. 이전 기록은 다른 게임 의 기록과 같다고 보기 어려움:
--              · 게임 길이 1330s → 1200s (정확히 20분, Sprint I)
--              · 4분 cap 위에 phase 2 추가 → 20분에 이전 cap 의 1.79 배 (+80%)
--                난이도 (difficulty v6, 2026-05-10)
--              · 신규 zone 5개 추가 (Asteroid Belt, Vega/Altair, Pleiades,
--                Orion Nebula, TON 618) — zone idx shift 로 mission/hazard
--                매핑 변경
--              · 4개 BOUNDARY INFO 마커 추가 (Sprint H)
--            기존 score (centi-second 기준 duration_ms/100) 가 새 게임과
--            동등하지 않으니 한 번 깨끗하게 비우고 v6 에서 새로 누적.
--
-- 주의:      1회성 마이그레이션. 실행 후 모든 유저의 Space-Z 기록 (개별 attempt
--            + best score 요약) 이 삭제됨. tetris/snake/pacman/burger/brick
--            /starship-lander/reaction 등 다른 액션 게임 기록은 영향 없음.
--            (이전 2026-05-02 wipe 와 같은 패턴)
--
-- 실행 후:   유저가 다시 플레이하면 v6 기록이 자동 누적됨. redeploy 없이
--            Supabase SQL editor 에서 한 번만 실행. 테이블 스키마/RPC/RLS
--            모두 그대로, 데이터만 비움.
-- =====================================================================

-- 개별 attempts (최근 20회 등) 모두 삭제
truncate table public.dodge_attempts restart identity;

-- 베스트 기록 요약 (world_rank 계산 base) 모두 삭제
truncate table public.dodge_records;
