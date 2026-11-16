"""Browser integration tests for classification JSON, using SYNTHETIC fixtures.

These tests do not call an AI provider. A fixture labelled as a real-file envelope
exercises the same loader contract; it is never evidence of model accuracy.
Run alongside the ordinary UI suite after starting a local static HTTP server:
    python3 tests/test_ai_ui.py --base-url http://127.0.0.1:4173
"""

import argparse
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from playwright.sync_api import expect, sync_playwright


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--base-url", default="http://127.0.0.1:4173")
parser.add_argument("--chromium", default="/usr/bin/chromium")
OPTIONS, UNITTEST_ARGS = parser.parse_known_args()
ROOT = Path(__file__).resolve().parents[1]
RESULT_CACHE_KEY = "refold-classification-cache-v1"
USER_STATE_KEY = "refold-v05-experience-data"


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class AIClassificationUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notes = json.loads((ROOT / "data/notes.json").read_text())
        cls.offline = json.loads(
            (ROOT / "data/classifications.offline.json").read_text()
        )
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            headless=True,
            executable_path=OPTIONS.chromium,
            args=["--no-sandbox"],
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
            is_mobile=True,
            has_touch=True,
            reduced_motion="reduce",
        )
        self.page = self.context.new_page()
        self.js_errors = []
        self.external_requests = []
        self.page.on("pageerror", lambda error: self.js_errors.append(str(error)))
        self.page.on(
            "request",
            lambda request: self.external_requests.append(request.url)
            if urlsplit(request.url).hostname
            not in (urlsplit(OPTIONS.base_url).hostname, None)
            else None,
        )
        self.real_result = self.fixture()
        self.response_kind = "response"
        self.classification_requests = 0

        def result_route(route):
            self.classification_requests += 1
            if self.response_kind == "failure":
                route.abort("failed")
            elif self.response_kind == "placeholder":
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(
                        {"schemaVersion": 1, "mode": "unavailable",
                         "status": "not_run_missing_api_key"}
                    ),
                )
            else:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(self.real_result, ensure_ascii=False),
                )

        self.page.route("**/data/classifications.real.json*", result_route)

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.js_errors, [], "Uncaught JavaScript errors")
        self.assertEqual(self.external_requests, [], "The frontend must not call AI APIs")

    def fixture(self):
        result = copy.deepcopy(self.offline)
        result.update(
            mode="real",
            provider="openai",
            model="browser-test-fixture-not-a-model-run",
            generatedAt=utc_now(),
        )
        return result

    def goto(self, *, offline=False):
        url = OPTIONS.base_url
        if offline:
            split = urlsplit(url)
            query = dict(parse_qsl(split.query))
            query["classification"] = "offline"
            url = urlunsplit(split._replace(query=urlencode(query)))
        self.page.goto(url, wait_until="networkidle")
        expect(self.page.locator("#smartShelf")).to_be_attached()

    def action(self, name, item_id=None):
        selector = f'[data-action="{name}"]'
        if item_id is not None:
            selector += f'[data-id="{item_id}"]'
        return self.page.locator(selector)

    def home(self):
        self.page.locator('.pagehead [data-action="home"]').click()

    def group(self, group_id):
        self.action("group", group_id).click()
        expect(self.page.locator(".pagehead")).to_be_visible()

    def ids(self):
        return self.action("note").evaluate_all("els => els.map(el => el.dataset.id)")

    def cache(self):
        return self.page.evaluate(
            "key => JSON.parse(localStorage.getItem(key) || 'null')", RESULT_CACHE_KEY
        )

    def user_state(self):
        return self.page.evaluate(
            "key => JSON.parse(localStorage.getItem(key) || '{}')", USER_STATE_KEY
        )

    def assert_mode(self, mode):
        footer = self.page.locator(".footer-mock")
        expect(footer).to_have_attribute("data-classification-mode", mode)
        expect(footer).to_contain_text({"offline": "离线模拟", "real": "真实 AI", "precomputed": "Codex AI 语义预分类"}[mode])

    def test_01_real_file_fixture_changes_memberships_not_original_data(self):
        """Synthetic JSON must drive membership rather than old preset answers."""
        assignment = next(a for a in self.real_result["assignments"] if a["noteId"] == "d1")
        assignment["memberships"] = [
            {"groupId": "travel", "reason": "浏览器契约测试夹具，不是模型输出"}
        ]
        assignment["unclassifiedReason"] = None
        self.goto()
        self.assert_mode("real")
        initial_ids = {
            note["id"] for note in self.notes if note["availability"] == "initial"
        }
        for group_id in ("design", "travel", "career", "food", "home", "life"):
            self.group(group_id)
            expected = {
                row["noteId"] for row in self.real_result["assignments"]
                if row["noteId"] in initial_ids
                and any(m["groupId"] == group_id for m in row["memberships"])
            }
            self.assertSetEqual(set(self.ids()), expected, f"Loaded memberships: {group_id}")
            self.home()
        self.group("design")
        self.assertNotIn("d1", self.ids())
        self.assertIn("case-a", self.ids())
        self.assertIn("case-b", self.ids())
        self.home()
        self.group("travel")
        self.assertIn("d1", self.ids())
        self.action("note", "d1").click()
        self.action("note-menu").click()
        expect(self.page.locator(".note-source")).to_contain_text("视觉设计灵感")
        self.action("close").click()
        original_note = next(note for note in self.notes if note["id"] == "d1")
        expect(self.page.locator(".note-gallery img").first).to_have_attribute(
            "src", f'assets/{original_note["cover"]}.webp'
        )
        self.action("note-back").click()
        self.home()
        self.group("career")
        self.assertIn("case-b", self.ids())

    def test_02_case_c_manual_exclusion_survives_same_and_updated_real_file(self):
        """Case C is an actual browser persistence check, not a model-quality test."""
        self.goto()
        self.group("design")
        before = self.ids()
        self.assertIn("d1", before)
        self.action("note", "d1").click()
        self.action("note-menu").click()
        self.action("note-exclude").click()
        self.action("note-back").click()
        self.assertNotIn("d1", self.ids())
        self.assertIn("d1", self.user_state()["exclude"]["design"])
        self.page.reload(wait_until="networkidle")
        self.group("design")
        self.assertNotIn("d1", self.ids())
        self.real_result["model"] = "updated-browser-fixture-not-a-model-run"
        self.real_result["generatedAt"] = utc_now()
        self.page.reload(wait_until="networkidle")
        self.group("design")
        self.assertNotIn("d1", self.ids())
        self.home()
        self.action("album", "视觉设计灵感").click()
        self.assertIn("d1", self.ids())
        print(
            "CASE_C_BROWSER_EVIDENCE "
            + json.dumps(
                {"inputSource": "synthetic_browser_fixture_not_a_real_model_run",
                 "noteId": "d1", "groupId": "design", "initiallyPresent": True,
                 "afterManualRemoval": False, "afterReloadSameResult": False,
                 "afterReloadUpdatedResult": False, "originalAlbumStillContainsNote": True}
            ),
            flush=True,
        )

    def test_03_invalid_real_envelopes_fall_back_and_do_not_enter_cache(self):
        def unknown_note(result):
            result["assignments"][0]["noteId"] = "not-in-dataset"

        def unknown_group(result):
            result["assignments"][0]["memberships"] = [
                {"groupId": "invented-group", "reason": "Invalid fixture"}
            ]

        def missing_note(result):
            result["assignments"].pop()

        def duplicate_note(result):
            result["assignments"][1] = copy.deepcopy(result["assignments"][0])

        def duplicate_membership(result):
            member = result["assignments"][0]["memberships"][0]
            result["assignments"][0]["memberships"].append(copy.deepcopy(member))

        def wrong_hash(result):
            result["datasetHash"] = "0" * 64

        def wrong_type(result):
            result["notesCount"] = "38"

        def future_timestamp(result):
            result["generatedAt"] = (
                datetime.now(timezone.utc) + timedelta(days=2)
            ).isoformat()

        for mutation in (
            unknown_note, unknown_group, missing_note, duplicate_note,
            duplicate_membership, wrong_hash, wrong_type, future_timestamp,
        ):
            with self.subTest(invalid=mutation.__name__):
                self.real_result = self.fixture()
                mutation(self.real_result)
                self.goto()
                self.page.evaluate("localStorage.clear()")
                self.page.reload(wait_until="networkidle")
                self.assert_mode("precomputed")
                self.assertIsNone(self.cache(), "Invalid result must not be cached")
                self.group("design")
                self.assertIn("d1", self.ids())

    def test_04_placeholder_uses_precomputed_and_forced_offline_is_explicit(self):
        self.response_kind = "placeholder"
        self.goto()
        self.assert_mode("precomputed")
        self.assertIsNone(self.cache())
        self.response_kind = "response"
        previous_requests = self.classification_requests
        self.goto(offline=True)
        self.assert_mode("offline")
        self.assertEqual(self.classification_requests, previous_requests)
        self.group("design")
        self.assertIn("d1", self.ids())

    def test_05_valid_cached_real_result_survives_network_failure(self):
        self.goto()
        self.assert_mode("real")
        self.assertIsNotNone(self.cache())
        self.response_kind = "failure"
        self.page.reload(wait_until="networkidle")
        self.assert_mode("real")
        expect(self.page.locator(".footer-mock")).to_contain_text("缓存")
        self.group("design")
        self.assertIn("d1", self.ids())

    def test_06_expired_and_wrong_dataset_cache_are_rejected(self):
        self.goto()
        self.assert_mode("real")
        valid_cache = self.cache()
        self.assertIsNotNone(valid_cache)
        self.response_kind = "failure"
        for invalid in ("expired", "wrong_dataset"):
            with self.subTest(cache=invalid):
                cached = copy.deepcopy(valid_cache)
                if invalid == "expired":
                    cached["cachedAt"] = 0
                else:
                    cached["result"]["datasetHash"] = "0" * 64
                self.page.evaluate(
                    "([key,value]) => localStorage.setItem(key,JSON.stringify(value))",
                    [RESULT_CACHE_KEY, cached],
                )
                self.page.reload(wait_until="networkidle")
                self.assert_mode("precomputed")

    def test_07_mode_change_keeps_custom_order_hidden_groups_and_corrections(self):
        self.goto()
        self.group("design")
        self.action("note", "d1").click()
        self.action("note-menu").click()
        self.action("note-exclude").click()
        self.action("note-back").click()
        self.home()
        self.action("settings").click()
        self.action("sort-start").click()
        self.action("sort-right", "design").click()
        self.action("sort-left", "design").click()
        self.action("hide", "travel").click()
        before = self.user_state()
        self.goto(offline=True)
        after = self.user_state()
        for field in ("exclude", "order", "hidden"):
            self.assertEqual(after[field], before[field])
        expect(self.action("group", "travel")).to_have_count(0)
        self.group("design")
        self.assertNotIn("d1", self.ids())

    def test_08_disabled_storage_keeps_offline_ui_and_undo_working(self):
        """A browser privacy setting must not turn the prototype into a blank page."""
        self.page.add_init_script(
            "Object.defineProperty(window, 'localStorage', {get() {"
            "throw new DOMException('Storage disabled for browser test', 'SecurityError');"
            "}});"
        )
        self.goto(offline=True)
        self.assert_mode("offline")
        self.group("design")
        self.assertIn("d1", self.ids())
        self.action("note", "d1").click()
        self.action("note-menu").click()
        self.action("note-exclude").click()
        self.action("note-back").click()
        self.assertNotIn("d1", self.ids())
        self.action("undo").click()
        self.assertIn("d1", self.ids())


if __name__ == "__main__":
    print("All AI browser inputs below are synthetic contract fixtures; no AI provider is called.")
    unittest.main(argv=[__file__, *UNITTEST_ARGS], verbosity=2)
