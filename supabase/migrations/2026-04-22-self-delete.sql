-- =====================================================================
-- Migration: Self-account deletion
-- Date:      2026-04-22
-- Purpose:   Let a regular user delete their own account from the /me/
--            profile editor. Cascades through auth.users → profiles →
--            friendships → messages → reactions etc. The admin_audit_log
--            captures the event so post-hoc forensics still work.
--
-- Policy:
--   * super_admin cannot self-delete via this RPC — they must demote
--     themselves to a regular user first (or have another super_admin
--     run admin_delete_user on them). Prevents a momentary lapse from
--     leaving the project with zero super_admins.
--   * All other roles (user, admin) can self-delete.
-- =====================================================================

create or replace function public.delete_my_account()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        snapshot jsonb;
begin
    if me is null then raise exception 'not_authenticated'; end if;

    /* Snapshot before delete so the audit row still shows who + what. */
    select jsonb_build_object(
        'nickname', nickname,
        'email', email,
        'role', role,
        'self_deleted', true,
        'created_at', created_at
    ) into snapshot from public.profiles where id = me;

    /* Safety: block self-delete for super_admin. */
    if exists(
        select 1 from public.profiles where id = me and role = 'super_admin'
    ) then
        raise exception 'super_admin_cannot_self_delete';
    end if;

    /* Write audit BEFORE the delete — otherwise the admin_id FK set
       null behaviour would still let the row survive, but writing
       the snapshot first is cleaner for forensic reading. */
    insert into public.admin_audit_log (admin_id, action, target_id, metadata)
    values (me, 'self_delete', me, coalesce(snapshot, '{}'::jsonb));

    /* auth.users delete cascades to every FK'd table. */
    delete from auth.users where id = me;

    return jsonb_build_object('ok', true);
end;
$$;
grant execute on function public.delete_my_account() to authenticated;
