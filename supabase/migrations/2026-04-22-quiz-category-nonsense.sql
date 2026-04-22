-- =====================================================================
-- Migration: Quiz — add "nonsense" (넌센스) category
-- Date:      2026-04-22
-- Purpose:   Extend the category CHECK constraint so the question
--            bank can carry Korean-style nonsense/riddle questions
--            (puns, wordplay, 수수께끼) as a distinct category.
--            Needed BEFORE the matching question batch inserts land.
-- =====================================================================

alter table public.quiz_questions
    drop constraint if exists quiz_questions_category_check;

alter table public.quiz_questions
    add constraint quiz_questions_category_check check (category in (
        'kpop','variety','sports','general','retro','latest','history','world','nonsense'
    ));

/* Also update the log_game_play whitelist so future game ids are
   still validated — noop here (no new game id), included for doc. */
