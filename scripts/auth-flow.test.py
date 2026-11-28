"""Offline OAuth browser regression. Run with python scripts/auth-flow.test.py."""

import json
import re
import time
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

try:
    from playwright.sync_api import Error, expect, sync_playwright
except ImportError:
    sync_playwright = None


PUBLIC = Path(__file__).resolve().parents[1] / "public"
ORIGIN = "https://luckyplz.test"
AUTH = ORIGIN + "/auth/"
ROOM = "/games/reversi/?play=friends&lang=ko#friends"
CLIENT = (PUBLIC / "js/supabase-config.js").read_text(encoding="utf-8")
PROJECT = re.search(r"const SUPABASE_URL\s*=\s*'https://([^']+)'", CLIENT)[1]
SESSION_KEY = "sb-" + PROJECT.split(".")[0] + "-auth-token"
ASSETS = {
    "/auth/": ("text/html", "auth/index.html"),
    "/vendor/supabase.min.js": ("text/javascript", "vendor/supabase.min.js"),
    "/js/supabase-config.js": ("text/javascript", "js/supabase-config.js"),
    "/build.json": ("application/json", "build.json"),
}


def session(provider):
    return {
        "access_token": "fixture-access-" + provider,
        "refresh_token": "fixture-refresh-" + provider,
        "token_type": "bearer",
        "expires_in": 3600,
        "expires_at": int(time.time()) + 3600,
        "user": {
            "id": "fixture-" + provider,
            "app_metadata": {"provider": provider},
            "user_metadata": {"nickname": "Lucky"},
        },
    }


@unittest.skipIf(sync_playwright is None, "Install Python Playwright to run browser checks")
class AuthFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.addClassCleanup(cls.pw.stop)
        for opts in ({"channel": "msedge"}, {}):
            try:
                cls.browser = cls.pw.chromium.launch(headless=True, **opts)
                cls.addClassCleanup(cls.browser.close)
                return
            except Error:
                pass
        raise unittest.SkipTest("Install Edge or Playwright Chromium")

    def setUp(self):
        self.ctx = self.browser.new_context(locale="ko-KR", viewport={"width": 390, "height": 844},
                                            service_workers="block")
        self.addCleanup(self.ctx.close)
        self.requests = []
        self.consents = []
        self.page = self.ctx.new_page()
        self.page.set_default_timeout(5000)
        self.ctx.route("**/*", self.respond)  # Every request is local, including redirects.

    def respond(self, route):
        req = route.request
        url = urlsplit(req.url)
        query = parse_qs(url.query)
        path = url.path
        if url.hostname == "luckyplz.test":
            if path in ASSETS:
                mime, file = ASSETS[path]
                return route.fulfill(content_type=mime, body=(PUBLIC / file).read_bytes())
            return route.fulfill(content_type="text/html" if req.is_navigation_request() else "text/plain", body="")
        if url.hostname in ("chooser.test", "kauth.kakao.com"):
            return route.fulfill(content_type="text/html", body="<title>Local provider fixture</title>")
        if url.hostname != PROJECT:
            return route.abort()

        headers = {"Access-Control-Allow-Origin": ORIGIN,
                   "Access-Control-Allow-Headers": req.headers.get("access-control-request-headers", "*"),
                   "Access-Control-Allow-Methods": "GET, POST, OPTIONS"}
        if req.method == "OPTIONS":
            return route.fulfill(status=204, headers=headers)
        self.requests.append((path, query))
        if path == "/auth/v1/authorize":
            return route.fulfill(status=302, headers={"Location": "https://chooser.test/"})
        if path == "/functions/v1/kakao-token":
            return route.fulfill(headers=headers, json={"id_token": "fixture-kakao-token"})
        if path == "/auth/v1/token":
            data = session("kakao" if query["grant_type"] == ["id_token"] else "google")
        elif path in ("/auth/v1/user", "/rest/v1/profiles"):
            provider = req.headers["authorization"].rsplit("-", 1)[-1]
            user = session(provider)["user"]
            data = user if path.endswith("/user") else [
                {"id": user["id"], "nickname": "Lucky", "profile_complete": True}
            ]
        elif path == "/rest/v1/rpc/set_consent":
            self.consents.append((req.headers["authorization"], req.post_data_json))
            data = {"terms_agreed_at": "2026-01-01", "privacy_agreed_at": "2026-01-01"}
        else:
            return route.fulfill(status=404, headers=headers, json={"error": "Unexpected fixture path"})
        return route.fulfill(headers=headers, json=data)

    def start(self, signed_in=False, switch=False):
        if signed_in:
            # Seed a session for the old account once, never overwrite a subsequent login.
            self.page.goto(ORIGIN + "/")
            self.page.evaluate("([key,value])=>localStorage.setItem(key,value)",
                               [SESSION_KEY, json.dumps(session("previous"))])
        query = {"return": ROOM, "lang": "ko"}
        if switch:
            query["switch"] = "1"
        self.page.goto(AUTH + "?" + urlencode(query))

    def choose(self, provider):
        self.page.locator("#signupTerms").check()
        self.page.locator("#signupPrivacy").check()
        self.assertFalse(self.page.locator("#signupMarketing").is_checked())
        self.page.locator("#" + provider + "Btn").click()
        host = "chooser.test" if provider == "google" else "kauth.kakao.com"
        self.page.wait_for_url(lambda u: urlsplit(u).hostname == host)

    def assert_consent(self, provider):
        self.assertEqual(self.consents, [("Bearer fixture-access-" + provider,
                        {"p_terms": True, "p_privacy": True, "p_marketing": False})])

    def test_existing_session_goes_directly_to_room(self):
        self.start(signed_in=True)
        expect(self.page).to_have_url(ORIGIN + ROOM)
        self.assertEqual(self.consents, [])

    def test_google_switch_cancel_and_retry(self):
        self.start(signed_in=True, switch=True)
        self.choose("google")
        options = next(q for path, q in self.requests if path == "/auth/v1/authorize")
        self.assertEqual(options["redirect_to"], [AUTH])
        self.assertEqual(options["prompt"], ["select_account"])
        self.assertIn("code_challenge", options)
        self.page.goto(AUTH + "?error=access_denied&error_description=Cancelled")
        expect(self.page.locator("#msgBox")).to_contain_text("취소")
        self.assertEqual(parse_qs(urlsplit(self.page.url).query)["return"], [ROOM])
        self.assertEqual(self.page.evaluate("async () => (await getSession())?.user?.id"), "fixture-previous")
        self.assertEqual(self.consents, [])
        self.choose("google")
        self.page.goto(AUTH + "?code=local-fixture-code")
        expect(self.page).to_have_url(ORIGIN + ROOM)
        self.assert_consent("google")

    def test_kakao_switch_returns_to_the_same_room(self):
        self.start(signed_in=True, switch=True)
        self.choose("kakao")
        options = parse_qs(urlsplit(self.page.url).query)
        self.assertEqual(options["redirect_uri"], [AUTH])
        self.assertEqual(options["prompt"], ["select_account"])
        self.assertEqual(set(options["scope"][0].split(",")), {"openid", "profile_nickname", "profile_image"})
        self.page.goto(AUTH + "?" + urlencode({"code": "local-fixture-code", "state": options["state"][0]}))
        expect(self.page).to_have_url(ORIGIN + ROOM)
        self.assert_consent("kakao")
        exchanges = [p for p, _ in self.requests if p == "/functions/v1/kakao-token"]
        self.assertEqual(len(exchanges), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
