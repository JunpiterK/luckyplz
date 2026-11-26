-- Enable Cloudflare Email Sending for notify.luckyplz.com. In Supabase Vault create
-- quiz_mail_cf_account_id and quiz_mail_cf_api_token (Email Sending Write for
-- that account). New applications are held safely until both are configured.
-- To verify, submit one test: /ops/#packageInbox shows the per-recipient
-- provider result and the operator mailbox should contain the matching receipt.
-- To replay a confirmed bounce after fixing the mailbox/suppression, set that
-- outbox row's next_attempt_at to now() and mail_status to 'retry'.
begin;
create extension if not exists pg_net with schema extensions;
create extension if not exists pg_cron;
create schema if not exists quiz_mail;
revoke all on schema quiz_mail from public, anon, authenticated;

create table if not exists quiz_mail.outbox (
    application_id uuid primary key references public.quiz_package_applications(id) on delete cascade,
    enqueued_at timestamptz not null default now(),
    next_attempt_at timestamptz not null default now(),
    attempts integer not null default 0,
    request_id bigint,
    requested_at timestamptz,
    sent_at timestamptz,
    mail_status text not null default 'pending'
        check (mail_status in ('pending','unconfigured','retry','delivered','queued','failed')),
    last_result text
);
revoke all on quiz_mail.outbox from public, anon, authenticated;
alter table quiz_mail.outbox enable row level security;
create index if not exists quiz_mail_due_idx on quiz_mail.outbox(next_attempt_at)
    where sent_at is null;

create or replace function quiz_mail.dispatch(p_receipt text, p_created timestamptz, p_to text)
returns bigint language plpgsql security definer set search_path = '' as $$
declare
    account_id text;
    api_token text;
begin
    select max(decrypted_secret) filter (where name='quiz_mail_cf_account_id'),
           max(decrypted_secret) filter (where name='quiz_mail_cf_api_token')
        into account_id, api_token from vault.decrypted_secrets
        where name in ('quiz_mail_cf_account_id','quiz_mail_cf_api_token');
    if account_id is null or account_id !~ '^[0-9a-f]{32}$' or nullif(btrim(api_token),'') is null then
        return null;
    end if;
    return net.http_post(
        url := 'https://api.cloudflare.com/client/v4/accounts/' || account_id || '/email/sending/send',
        headers := jsonb_build_object('Content-Type','application/json','Authorization','Bearer ' || api_token),
        body := jsonb_build_object('from','notifications@notify.luckyplz.com','to',p_to,
            'subject','[Lucky Please] 기업 퀴즈 패키지 신청 · ' || p_receipt,
            'headers', jsonb_build_object('X-LuckyPlz-Receipt',p_receipt),
            'text', format(E'기업 퀴즈 패키지 신청이 들어왔습니다.\n\n접수번호  %s\n접수 시각  %s (한국 시간)\n\n운영자 계정으로 신청 내용을 확인하세요.\nhttps://luckyplz.com/ops/#packageInbox',
                    p_receipt, to_char(p_created at time zone 'Asia/Seoul','YYYY-MM-DD HH24:MI'))),
        timeout_milliseconds := 15000);
end;
$$;

create or replace function quiz_mail.response_status(p_code integer,p_content text,p_to text)
returns text language plpgsql immutable set search_path = '' as $$
declare
    body jsonb;
    outcome jsonb;
begin
    if p_code in (401,403) then return 'unconfigured'; end if;
    if p_code is null or p_code not between 200 and 299 then return 'retry'; end if;
    body := p_content::jsonb;
    outcome := body->'result';
    if body->'success' is distinct from 'true'::jsonb then return 'retry'; end if;
    if outcome->'permanent_bounces' @> jsonb_build_array(p_to)
        or outcome->'suppressed_recipients' @> jsonb_build_array(p_to) then return 'failed'; end if;
    if outcome->'delivered' @> jsonb_build_array(p_to) then return 'delivered'; end if;
    if outcome->'queued' @> jsonb_build_array(p_to) then return 'queued'; end if;
    return 'retry';
exception when invalid_text_representation then return 'retry';
end;
$$;

-- Requests stay in the logged outbox until the provider accepts the mail.
-- pg_net starts its HTTP request after commit. A rollback discards both rows.
create or replace function quiz_mail.tick(p_application_id uuid default null)
returns void language plpgsql security definer set search_path = '' as $$
declare
    work record;
    reply record;
    req bigint;
    result text;
    recipient constant text := 'luckyplz.contact@gmail.com';
begin
    for work in
        select q.*, a.receipt from quiz_mail.outbox q
        join public.quiz_package_applications a on a.id = q.application_id
        where q.sent_at is null and q.next_attempt_at <= now()
          and (p_application_id is null or q.application_id = p_application_id)
        order by q.next_attempt_at, q.enqueued_at limit 40 for update of q skip locked
    loop
        if work.request_id is not null then
            select r.* into reply from net._http_response r where r.id = work.request_id;
            if not found and work.requested_at > now() - interval '2 minutes' then
                update quiz_mail.outbox set next_attempt_at = now() + interval '30 seconds'
                    where application_id = work.application_id;
                continue;
            end if;
            result := quiz_mail.response_status(reply.status_code,reply.content,recipient);
            if reply.timed_out or reply.error_msg is not null then result := 'retry'; end if;
            if result in ('delivered','queued') then
                update quiz_mail.outbox set sent_at = now(), request_id = null,
                    mail_status = result, last_result = result
                    where application_id = work.application_id;
                continue;
            end if;
            -- The provider controls Message-ID. An ambiguous response gets a retry
            -- with the same receipt; a lost acknowledgement may produce a duplicate.
            update quiz_mail.outbox set request_id = null, mail_status = result,
                next_attempt_at = case when result='failed' then 'infinity'::timestamptz
                    else now() + make_interval(mins => 1 << least(6, greatest(0, work.attempts - 1))) end,
                last_result = coalesce('http_' || reply.status_code::text, 'no_response')
                where application_id = work.application_id;
            continue;
        end if;
        begin
            req := quiz_mail.dispatch(work.receipt, work.enqueued_at, recipient);
        exception when others then
            req := null; -- A broken transport must not roll back a paid-service inquiry.
        end;
        if req is null then
            update quiz_mail.outbox set next_attempt_at = now() + interval '1 minute', mail_status = 'unconfigured', last_result = 'transport_unavailable'
                where application_id = work.application_id;
        else
            update quiz_mail.outbox set request_id = req, requested_at = now(), attempts = attempts + 1,
                next_attempt_at = now() + interval '15 seconds', mail_status = 'pending', last_result = 'submitted'
                where application_id = work.application_id;
        end if;
    end loop;
end;
$$;

create or replace function quiz_mail.enqueue()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
    insert into quiz_mail.outbox(application_id) values (new.id);
    begin
        perform quiz_mail.tick(new.id);
    exception when others then
        -- The committed outbox row lets cron resume after any dispatch failure.
        null;
    end;
    return new;
end;
$$;

revoke all on all functions in schema quiz_mail from public, anon, authenticated;
create or replace trigger quiz_package_mail_enqueued after insert on public.quiz_package_applications
    for each row execute function quiz_mail.enqueue();
select cron.schedule('deliver-quiz-package-mail', '* * * * *', 'select quiz_mail.tick()');

create or replace function public.lp_quiz_package_list(p_limit integer default 50, p_offset integer default 0)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
begin
    if public.is_admin() is not true then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    return jsonb_build_object(
        'total', (select count(*) from public.quiz_package_applications),
        'rows', coalesce((select jsonb_agg(to_jsonb(a) order by a.created_at desc, a.id)
            from (select p.id, p.receipt, p.created_at, p.company, p.contact_name, p.email,
                         p.event_date, p.attendees, p.note, p.source, p.status, p.price_krw, m.mail_status
                  from public.quiz_package_applications p left join quiz_mail.outbox m on m.application_id=p.id
                  order by p.created_at desc, p.id limit greatest(1,least(coalesce(p_limit,50),100))
                  offset greatest(0,coalesce(p_offset,0))) a),'[]'::jsonb)
    );
end;
$$;
revoke all on function public.lp_quiz_package_list(integer,integer) from public, anon;
grant execute on function public.lp_quiz_package_list(integer,integer) to authenticated;
notify pgrst,'reload schema';
commit;
