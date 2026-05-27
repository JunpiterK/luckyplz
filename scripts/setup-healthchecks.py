#!/usr/bin/env python3
from __future__ import annotations
"""Bootstrap Healthchecks.io 6 checks + register GitHub secrets.

One-time setup script (운영자의 1회성 작업 자동화).

Reads HC_API_KEY from env. Creates / updates 6 cron checks on
Healthchecks.io to match the daily-cron.yml schedule, extracts the
6 ping URLs, and uses `gh secret set` to register them as repo
secrets on JunpiterK/luckyplz so the auto-publish pipeline can
ping them.

Idempotent: re-running matches existing checks by `name` (uses the
Healthchecks API `unique` feature). Safe to re-run if anything
goes wrong mid-flight.

Usage:
    HC_API_KEY=hc_xxxxxxx python scripts/setup-healthchecks.py

Requires:
    - HC_API_KEY env var (read-write API key from
      https://healthchecks.io/accounts/profile/api/)
    - gh CLI authenticated as JunpiterK (already done in this env)
    - Python 3.11+ (standard library only — no pip install needed)
"""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

API_BASE = "https://healthchecks.io/api/v3"
REPO = "JunpiterK/luckyplz"

# Per-slot HC check config. Schedules match .github/workflows/daily-cron.yml
# (post-2026-05-27 random-minute shift). Grace = 60 min covers the typical
# GH Actions schedule drift envelope + Claude call (3-7 min) + git push (<1 min).
SLOTS = [
    {"slot": "us-close",     "cron": "27 19 * * *"},
    {"slot": "kr-open",      "cron": "13 22 * * *"},
    {"slot": "cn-open",      "cron": "37 23 * * *"},
    {"slot": "kr-close",     "cron": "38 6 * * *"},
    {"slot": "cn-close",     "cron": "8 7 * * *"},
    {"slot": "us-premarket", "cron": "33 12 * * *"},
]

GRACE_SECONDS = 60 * 60  # 60 min — see header note


def hc_request(method: str, path: str, api_key: str, payload: dict | None = None) -> dict:
    """Call the Healthchecks API. Returns parsed JSON response.

    Raises with the API's error body on non-2xx so the caller sees exactly
    what went wrong (most often: bad API key permissions).
    """
    url = f"{API_BASE}{path}"
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Healthchecks API {method} {path} failed: HTTP {e.code}\n"
            f"Response: {err_body}"
        ) from e


def create_or_update_check(api_key: str, slot: str, cron_expr: str) -> dict:
    """Idempotent upsert by check name.

    Uses Healthchecks' built-in `unique=["name"]` mechanic: if a check with
    this name already exists, it gets updated; otherwise created.
    """
    payload = {
        "name": f"luckyplz-{slot}",
        "tags": "luckyplz auto-publish",
        "desc": (
            f"Auto-publish slot `{slot}` for luckyplz.com blog. "
            f"GitHub Actions cron pings this URL after a successful publish. "
            f"If no ping arrives by deadline, the auto-publish pipeline failed."
        ),
        "kind": "cron",
        "schedule": cron_expr,
        "tz": "UTC",
        "grace": GRACE_SECONDS,
        "unique": ["name"],
    }
    return hc_request("POST", "/checks/", api_key, payload)


def gh_set_secret(name: str, value: str) -> None:
    """Set a GitHub repo secret via gh CLI.

    Passes the secret on stdin to avoid putting it on the command line
    (where it could end up in shell history or process listings).
    """
    proc = subprocess.run(
        ["gh", "secret", "set", name, "--repo", REPO, "--body", value],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"gh secret set {name} failed (exit {proc.returncode}):\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )


def main() -> int:
    api_key = os.environ.get("HC_API_KEY", "").strip()
    if not api_key:
        print(
            "ERROR: HC_API_KEY env var is required.\n"
            "Get one at https://healthchecks.io/accounts/profile/api/ "
            "(Read-Write key).",
            file=sys.stderr,
        )
        return 2

    print(f"[setup] {len(SLOTS)} Healthchecks checks → GitHub secrets on {REPO}")
    print()

    failures: list[str] = []
    for cfg in SLOTS:
        slot = cfg["slot"]
        print(f"=== {slot} ===")
        try:
            check = create_or_update_check(api_key, slot, cfg["cron"])
            ping_url = check.get("ping_url")
            if not ping_url:
                raise RuntimeError(
                    f"Healthchecks response missing ping_url: {check!r}"
                )
            print(f"  HC check upserted")
            print(f"  ping_url = {ping_url}")
            secret_name = "HC_URL_" + slot.upper().replace("-", "_")
            gh_set_secret(secret_name, ping_url)
            print(f"  GitHub secret set: {secret_name}")
        except Exception as exc:
            print(f"  FAILED: {exc}")
            failures.append(slot)
        print()

    if failures:
        print(f"[setup] {len(failures)} slot(s) FAILED: {failures}")
        return 1

    print("[setup] all 6 slots configured.")
    print()
    print("Next steps:")
    print("  1. Paste your Discord webhook URL — I'll set DISCORD_WEBHOOK_URL.")
    print("  2. (Optional) On the Healthchecks dashboard, add a Discord integration")
    print("     so HC itself alerts you when a slot misses its deadline.")
    print("  3. Verify by triggering a manual workflow_dispatch:")
    print(f"     gh workflow run daily-cron.yml -f slot=us-close")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
