"""Browser regression checks for the RE collection prototype.

Run a server from the repository, then:
    python3 tests/test_ui.py --base-url http://127.0.0.1:4173
Requires Python Playwright and an installed Chromium executable.
"""

import argparse
import unittest

from playwright.sync_api import expect, sync_playwright


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--base-url", default="http://127.0.0.1:4173")
parser.add_argument("--chromium", default="/usr/bin/chromium")
OPTIONS, UNITTEST_ARGS = parser.parse_known_args()


class PrototypeUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            headless=True, executable_path=OPTIONS.chromium, args=["--no-sandbox"]
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            device_scale_factor=1,
            reduced_motion="reduce",
        )
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on(
            "console",
            lambda message: self.errors.append(message.text)
            if message.type == "error"
            else None,
        )
        self.page.goto(OPTIONS.base_url, wait_until="networkidle")

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [], "Browser JavaScript/console errors")

    def action(self, name, item_id=None):
        selector = f'[data-action="{name}"]'
        if item_id is not None:
            selector += f'[data-id="{item_id}"]'
        return self.page.locator(selector)

    def group(self, group_id="design"):
        self.action("group", group_id).click()
        expect(self.page.locator(".collection-heading h1")).to_contain_text(
            {"design": "设计与创作", "travel": "旅行与探索", "home": "家居灵感"}.get(
                group_id, ""
            )
        )

    def home(self):
        self.page.locator('.pagehead [data-action="home"]').click()
        expect(self.page.locator("#smartShelf")).to_be_attached()

    def settings(self):
        self.action("settings").click()
        expect(self.page.locator('[role="dialog"]')).to_be_visible()

    def save_note(self, note_id):
        viewport=self.page.viewport_size.copy()
        self.page.set_viewport_size({'width':1440,'height':900})
        if not self.page.locator('#demoPanel').is_visible():
            self.page.locator('#simulateDemo').click()
        self.action('save-note',note_id).click()
        self.page.set_viewport_size(viewport)

    def restore_default(self):
        self.settings()
        self.action('sort-start').click()
        self.action('sort-auto').click()
        self.action('sort-done').click()

    def exclude_note(self,note_id):
        self.action('manage').click()
        self.action('manage-start').click()
        self.action('select-note',note_id).click()
        self.action('batch-remove').click()

    def assert_images(self):
        self.page.wait_for_function(
            "Array.from(document.images).every(img => img.complete)"
        )
        failed = self.page.evaluate(
            "Array.from(document.images).filter(img => !img.naturalWidth).map(img => img.src)"
        )
        self.assertEqual(failed, [], "Image load failures")

    def assert_no_horizontal_overflow(self):
        dimensions = self.page.evaluate(
            """() => ({
                root: document.documentElement.scrollWidth,
                viewport: innerWidth,
                app: document.querySelector('#appScreen').scrollWidth,
                appWidth: document.querySelector('#appScreen').clientWidth
            })"""
        )
        self.assertLessEqual(dimensions["root"], dimensions["viewport"] + 1)
        self.assertLessEqual(dimensions["app"], dimensions["appWidth"] + 1)

    def test_01_responsive_pages_and_images(self):
        """All principal pages render at 375, 390 and 430 without broken images."""
        for width in (375, 390, 430):
            with self.subTest(width=width):
                self.page.set_viewport_size({"width": width, "height": 844})
                self.page.reload(wait_until="networkidle")
                expect(self.action("create")).to_be_visible()
                self.assert_no_horizontal_overflow()
                self.assert_images()
                self.group()
                self.assertGreater(self.action("note").count(), 0)
                self.assert_no_horizontal_overflow()
                self.assert_images()
                self.action("note", "d1").click()
                expect(self.page.locator('.note-detail')).to_be_visible()
                self.assert_images()
                self.assert_no_horizontal_overflow()
                self.action("note-back").click()
                self.home()
                self.action("create").click()
                self.page.locator("#albumTitle").fill("设计灵感")
                expect(self.action("show-similar")).to_be_visible()
                self.assert_no_horizontal_overflow()
                expect(self.page.locator(".tabbar")).to_be_hidden()

    def test_02_horizontal_vertical_wheel_and_return_position(self):
        """The shelf scrolls sideways and does not trap vertical page movement."""
        shelf = self.page.locator("#smartShelf")
        shelf.scroll_into_view_if_needed()
        shelf.hover()
        self.page.mouse.wheel(230, 0)
        self.page.wait_for_function(
            "document.querySelector('#smartShelf').scrollLeft > 60"
        )
        before_top = self.page.locator("#appScreen").evaluate("el => el.scrollTop")
        self.page.mouse.wheel(0, 120)
        self.page.wait_for_function(
            "previous => document.querySelector('#appScreen').scrollTop > previous + 20",
            arg=before_top,
        )
        tile = self.action("group", "career")
        tile.scroll_into_view_if_needed()
        self.page.wait_for_timeout(250)  # Allow native scroll snapping to settle.
        old_left = shelf.evaluate("el => el.scrollLeft")
        old_top = self.page.locator("#appScreen").evaluate("el => el.scrollTop")
        self.assertGreater(old_left, 0)
        tile.click()
        self.home()
        self.assertAlmostEqual(shelf.evaluate("el => el.scrollLeft"), old_left, delta=3)
        self.assertAlmostEqual(
            self.page.locator("#appScreen").evaluate("el => el.scrollTop"),
            old_top,
            delta=3,
        )

    def test_03_correction_undo_and_original_album(self):
        self.action("album", "视觉设计灵感").click()
        original_ids = self.action("note").evaluate_all("els => els.map(el => el.dataset.id)")
        self.assertIn("d1", original_ids)
        self.home()
        self.group()
        before_count = self.action("note").count()
        self.exclude_note("d1")
        self.assertEqual(self.action("note").count(), before_count - 1)
        expect(self.action("note", "d1")).to_have_count(0)
        expect(self.action("undo")).to_be_visible()
        self.action("undo").click()
        expect(self.action("note", "d1")).to_have_count(1)
        self.assertEqual(self.action("note").count(), before_count)
        self.home()
        self.action("album", "视觉设计灵感").click()
        self.assertEqual(
            self.action("note").evaluate_all("els => els.map(el => el.dataset.id)"),
            original_ids,
        )

    def test_04_correction_survives_reload_without_affecting_original(self):
        self.group()
        self.exclude_note("d1")
        self.page.reload(wait_until="networkidle")
        self.group()
        expect(self.action("note", "d1")).to_have_count(0)
        self.home()
        self.action("album", "视觉设计灵感").click()
        expect(self.action("note", "d1")).to_have_count(1)

    def test_05_new_collection_updates_sort_count_and_persistence(self):
        album_cards = self.page.locator(".collection-list").inner_text()
        self.group("home")
        old_note_count = self.action("note").count()
        self.home()
        self.save_note("new1")
        expect(self.page.locator("#smartShelf [data-action=group]").first).to_have_attribute(
            "data-id", "home"
        )
        self.assertEqual(self.page.locator(".collection-list").inner_text(), album_cards)
        self.group("home")
        self.assertEqual(self.action("note").count(), old_note_count + 1)
        expect(self.action("note", "new1")).to_have_count(1)
        self.page.reload(wait_until="networkidle")
        expect(self.page.locator("#smartShelf [data-action=group]").first).to_have_attribute(
            "data-id", "home"
        )
        self.page.set_viewport_size({"width":1440,"height":900})
        if not self.page.locator("#demoPanel").is_visible():
            self.page.locator("#simulateDemo").click()
        expect(self.action("save-note", "new1")).to_be_disabled()

    def test_06_custom_sort_keeps_priority_until_recent_sort_restored(self):
        self.settings()
        self.action("sort-start").click()
        self.action("group", "design").focus()
        self.page.keyboard.press("ArrowRight")
        self.action("group", "design").focus()
        self.page.keyboard.press("ArrowLeft")
        self.action("sort-done").click()
        self.save_note("new3")
        ordered = self.page.locator("#smartShelf [data-action=group]").evaluate_all(
            "els => els.map(el => el.dataset.id)"
        )
        self.assertEqual(ordered[:2], ["design", "travel"])
        self.restore_default()
        expect(self.page.locator("#smartShelf [data-action=group]").first).to_have_attribute(
            "data-id", "travel"
        )

    def test_07_hide_restore_and_disable_enable(self):
        self.settings()
        self.action("display-settings").click()
        self.action("visibility-toggle", "design").click()
        self.action("close").click()
        expect(self.action("group", "design")).to_have_count(0)
        self.page.reload(wait_until="networkidle")
        expect(self.action("group", "design")).to_have_count(0)
        self.settings()
        self.action("display-settings").click()
        self.action("visibility-toggle", "design").click()
        self.action("close").click()
        expect(self.action("group", "design")).to_have_count(1)
        self.settings()
        self.action("smart-toggle").click()
        expect(self.page.locator("#smartShelf")).to_have_count(0)
        self.page.reload(wait_until="networkidle")
        expect(self.page.locator("#smartShelf")).to_have_count(0)
        self.settings()
        self.action("smart-toggle").click()
        expect(self.action("group", "design")).to_have_count(1)

    def test_08_create_with_similarity_and_permissions(self):
        self.action("create").click()
        expect(self.action("save-album")).to_be_disabled()
        title = self.page.locator("#albumTitle")
        desc = self.page.locator("#albumDesc")
        title.fill("设计灵感")
        desc.fill("回归验证简介")
        expect(self.action("show-similar")).to_be_visible()
        self.action("show-similar").click()
        expect(self.page.locator('[role="dialog"]')).to_contain_text("视觉设计灵感")
        self.action("close").click()
        self.action("toggle-public").click()
        self.action("toggle-shared").click()
        expect(title).to_have_value("设计灵感")
        expect(desc).to_have_value("回归验证简介")
        expect(self.action("toggle-public")).to_have_attribute("aria-checked", "false")
        expect(self.action("toggle-shared")).to_have_attribute("aria-checked", "true")
        self.action("save-album").click()
        created = self.page.locator('[data-action="album"][data-id^="user-"]').filter(has_text="设计灵感")
        expect(created).to_have_count(1)
        expect(created).to_contain_text("共享人")
        expect(created.locator(".tiny-lock svg")).to_have_count(1)
        self.page.reload(wait_until="networkidle")
        expect(created).to_have_count(1)

    def test_09_suggestion_can_be_ignored(self):
        self.action("create").click()
        self.page.locator("#albumTitle").fill("设计灵感")
        expect(self.action("show-similar")).to_be_visible()
        self.action("save-album").click()
        expect(
            self.page.locator('[data-action="album"][data-id^="user-"]').filter(has_text="设计灵感")
        ).to_have_count(1)

    def test_10_manage_menu_escape_backdrop_and_scroll_isolation(self):
        self.group()
        self.action('manage').click()
        expect(self.page.locator('[role="dialog"]')).to_be_visible()
        self.assertTrue(self.page.locator('#appScreen').evaluate('e=>e.inert'))
        self.page.keyboard.press('Escape')
        expect(self.page.locator('.sheet')).to_have_count(0)
        self.action('manage').click()
        self.page.locator('#backdrop').click(position={'x':3,'y':3})
        expect(self.page.locator('.sheet')).to_have_count(0)
        self.action('note','d1').click()
        expect(self.page.locator('.native-note')).to_be_visible()
        expect(self.action('note-menu')).to_have_count(0)
        self.action('note-back').click()
        expect(self.action('manage')).to_be_visible()

if __name__ == "__main__":
    unittest.main(argv=[__file__, *UNITTEST_ARGS], verbosity=2)
