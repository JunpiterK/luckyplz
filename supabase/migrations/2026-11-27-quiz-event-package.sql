-- Guest intake for the KRW 149,000 corporate quiz. Applications do not create orders or payments.
begin;

create table if not exists public.quiz_package_applications (
    id uuid primary key,
    receipt text not null unique default ('LQ-' || upper(left(replace(gen_random_uuid()::text, '-', ''), 16))),
    created_at timestamptz not null default now(),
    company text not null,
    contact_name text not null,
    email text not null,
    event_date date,
    attendees integer,
    note text not null default '',
    consent_version text not null default '2026-11-27',
    source text not null check (source in ('home', 'quiz', 'direct')),
    price_krw integer not null default 149000,
    status text not null default 'new' check (status in ('new', 'contacted', 'confirmed', 'closed'))
);

create index if not exists quiz_package_created_idx on public.quiz_package_applications (created_at desc, id);
create index if not exists quiz_package_email_idx on public.quiz_package_applications (email, created_at desc);
alter table public.quiz_package_applications enable row level security;
revoke all on table public.quiz_package_applications from public, anon, authenticated;

create or replace function public.lp_quiz_package_apply(
    p_request_id uuid, p_company text, p_contact_name text, p_email text, p_event_date date,
    p_attendees integer, p_note text, p_consent boolean, p_source text
) returns jsonb
language plpgsql security definer set search_path = ''
as $$
declare
    v_company text := btrim(p_company);
    v_contact text := btrim(p_contact_name);
    v_email text := lower(btrim(p_email));
    v_note text := btrim(coalesce(p_note, ''));
    v_source text := coalesce(p_source, 'direct');
    v_today date := (now() at time zone 'Asia/Seoul')::date;
    v_saved public.quiz_package_applications%rowtype;
begin
    if p_consent is not true then
        return jsonb_build_object('ok', false, 'error', 'consent_required');
    end if;
    if p_request_id is null
        or coalesce(length(v_company), 0) not between 1 and 100 or v_company ~ '[[:cntrl:]]'
        or coalesce(length(v_contact), 0) not between 1 and 60 or v_contact ~ '[[:cntrl:]]'
        or coalesce(length(v_email), 0) not between 3 and 254
        or v_email !~ '^[^[:space:][:cntrl:]@<>,;]+@[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$'
        or p_attendees not between 1 and 100000 or length(v_note) > 1000
        or v_source not in ('home', 'quiz', 'direct') then
        return jsonb_build_object('ok', false, 'error', 'invalid_input');
    end if;

    -- The small intake rate allows one short transaction lock to make retries and quotas atomic.
    perform pg_advisory_xact_lock(624911, 149000);
    select * into v_saved from public.quiz_package_applications where id = p_request_id;
    if found then
        if row(v_company, v_contact, v_email, p_event_date, p_attendees, v_note, v_source)
            is distinct from row(v_saved.company, v_saved.contact_name, v_saved.email, v_saved.event_date,
                                 v_saved.attendees, v_saved.note, v_saved.source) then
            return jsonb_build_object('ok', false, 'error', 'request_conflict');
        end if;
        return jsonb_build_object('ok', true, 'receipt', v_saved.receipt);
    end if;
    if p_event_date < v_today or p_event_date > (v_today + interval '3 years')::date then
        return jsonb_build_object('ok', false, 'error', 'invalid_input');
    end if;
    -- Bound repeated mailboxes and bursts across addresses without collecting IPs.
    if exists (select 1 from public.quiz_package_applications
               where email = v_email and created_at >= now() - interval '24 hours' offset 3)
        or exists (select 1 from public.quiz_package_applications
                   where created_at >= now() - interval '10 minutes' offset 199) then
        return jsonb_build_object('ok', false, 'error', 'rate_limited');
    end if;

    insert into public.quiz_package_applications (id, company, contact_name, email, event_date, attendees, note, source)
        values (p_request_id, v_company, v_contact, v_email, p_event_date, p_attendees, v_note, v_source)
        returning * into v_saved;
    return jsonb_build_object('ok', true, 'receipt', v_saved.receipt);
end;
$$;

create or replace function public.lp_quiz_package_list(p_limit integer default 50, p_offset integer default 0)
returns jsonb language plpgsql stable security definer set search_path = ''
as $$
begin
    if public.is_admin() is not true then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    return jsonb_build_object(
        'total', (select count(*) from public.quiz_package_applications),
        'rows', coalesce((select jsonb_agg(to_jsonb(a) order by a.created_at desc, a.id)
            from (select id, receipt, created_at, company, contact_name, email, event_date, attendees,
                         note, source, status, price_krw
                  from public.quiz_package_applications order by created_at desc, id
                  limit greatest(1, least(coalesce(p_limit, 50), 100))
                  offset greatest(0, coalesce(p_offset, 0))) a), '[]'::jsonb)
    );
end;
$$;

create or replace function public.lp_quiz_package_status(p_id uuid, p_expected_status text, p_status text)
returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
    v_status text;
begin
    if public.is_admin() is not true then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    if p_id is null or p_status is null or p_status not in ('new', 'contacted', 'confirmed', 'closed')
        or p_expected_status is null or p_expected_status not in ('new', 'contacted', 'confirmed', 'closed') then
        return jsonb_build_object('ok', false, 'error', 'invalid_input');
    end if;
    select status into v_status from public.quiz_package_applications where id = p_id for update;
    if not found then
        return jsonb_build_object('ok', false, 'error', 'not_found');
    elsif v_status = p_status then
        return jsonb_build_object('ok', true, 'status', v_status);
    elsif v_status <> p_expected_status then
        return jsonb_build_object('ok', false, 'error', 'stale_status');
    end if;
    update public.quiz_package_applications set status = p_status where id = p_id;
    return jsonb_build_object('ok', true, 'status', p_status);
end;
$$;

revoke all on function public.lp_quiz_package_apply(uuid,text,text,text,date,integer,text,boolean,text),
    public.lp_quiz_package_list(integer,integer), public.lp_quiz_package_status(uuid,text,text)
    from public, anon, authenticated;
grant execute on function public.lp_quiz_package_apply(uuid,text,text,text,date,integer,text,boolean,text) to anon, authenticated;
grant execute on function public.lp_quiz_package_list(integer,integer), public.lp_quiz_package_status(uuid,text,text)
    to authenticated;

create extension if not exists pg_cron;
select cron.schedule('purge-expired-quiz-package-intake', '10 15 * * *',
    $job$delete from public.quiz_package_applications where created_at < now() - interval '90 days'$job$);
notify pgrst, 'reload schema';
commit;
