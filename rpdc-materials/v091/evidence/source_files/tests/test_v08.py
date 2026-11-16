"""v0.8 interaction regression against the real static prototype.

Run after starting a local server, choosing the implemented phase:
  python3 tests/test_v08.py --base-url http://127.0.0.1:4173 --phase A
  python3 tests/test_v08.py --base-url http://127.0.0.1:4173 --phase all
No AI service, social API, or external message is used.
"""
import argparse
import base64
import json
from urllib.parse import urlsplit
import unittest

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--base-url', default='http://127.0.0.1:4173')
parser.add_argument('--chromium', default='/usr/bin/chromium')
parser.add_argument('--phase', choices=('A', 'B', 'C', 'all'), default='all')
OPTIONS, UNITTEST_ARGS = parser.parse_known_args()
KEY = 'refold-v05-experience-data'


class BrowserCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            headless=True, executable_path=OPTIONS.chromium, args=['--no-sandbox'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={'width': 390, 'height': 844}, is_mobile=True,
            has_touch=True, device_scale_factor=1, reduced_motion='reduce')
        self.page = self.context.new_page()
        self.errors = []
        self.failed_images = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('console', lambda m: self.errors.append(m.text) if m.type == 'error' else None)
        self.page.goto(OPTIONS.base_url, wait_until='networkidle')
        expect(self.action('group', 'design')).to_be_attached()

    def tearDown(self):
        self.assertEqual(self.errors, [], 'Uncaught JavaScript/console errors')
        self.context.close()

    def action(self, name, item=None):
        selector = f'[data-action="{name}"]'
        if item is not None:
            selector += f'[data-id="{item}"]'
        return self.page.locator(selector)

    def seed(self, value):
        self.page.evaluate('([k,v])=>localStorage.setItem(k, JSON.stringify(v))', [KEY, value])
        self.page.reload(wait_until='networkidle')

    def state(self):
        return self.page.evaluate('k=>JSON.parse(localStorage.getItem(k)||"{}")', KEY)

    def group(self, group='design'):
        self.action('group', group).click()
        expect(self.action('manage')).to_be_visible()

    def home(self):
        self.page.locator('.pagehead [data-action="home"]').click()
        expect(self.page.locator('#smartShelf')).to_be_attached()

    def settings(self):
        self.action('settings').click()
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

    def ids(self, action='note'):
        return self.action(action).evaluate_all('els=>els.map(el=>el.dataset.id)')

    def order(self):
        return self.page.locator('#smartShelf [data-action="group"]').evaluate_all('els=>els.map(el=>el.dataset.id)')

    def start_manage(self):
        self.action('manage').click()
        self.action('manage-start').click()

    def open_picker(self):
        self.action('manage').click()
        self.action('add-notes').click()

    def toggle_visible(self, group):
        self.settings()
        self.action('display-settings').click()
        self.action('visibility-toggle', group).click()
        self.action('close').click()

    def select(self, note='d1'):
        self.action('select-note', note).click()

    def assert_assets(self):
        self.page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
        self.assertEqual(self.page.evaluate('Array.from(document.images).filter(i=>!i.naturalWidth).map(i=>i.src)'), [])


class PhaseA(BrowserCase):
    def test_01_shelf_geometry_click_and_mouse_drag(self):
        """Three full cards and a 16–24px fourth-card hint at 390px."""
        shelf = self.page.locator('#smartShelf')
        shelf.scroll_into_view_if_needed()
        dimensions = shelf.evaluate('''s=>{
            const b=s.getBoundingClientRect(), t=[...s.querySelectorAll('.smart-tile')].map(e=>e.getBoundingClientRect());
            return {right:b.right, third:t[2].right, fourth:t[3].left, width:t[0].width};
        }''')
        self.assertLessEqual(dimensions['third'], dimensions['right'])
        self.assertGreaterEqual(dimensions['right'] - dimensions['fourth'], 16)
        self.assertLessEqual(dimensions['right'] - dimensions['fourth'], 24)
        box = shelf.bounding_box()
        x, y = box['x'] + 290, box['y'] + 45
        self.page.mouse.move(x, y)
        self.page.mouse.down()
        self.page.mouse.move(x - 180, y, steps=12)
        self.page.mouse.up()
        self.assertGreater(shelf.evaluate('e=>e.scrollLeft'), 80)
        expect(self.action('manage')).to_have_count(0)
        expect(self.action('sort-done')).to_have_count(0)
        self.action('group', 'home').click()
        expect(self.action('manage')).to_be_visible()

    def test_02_touch_pan_cancels_long_press(self):
        shelf = self.page.locator('#smartShelf')
        shelf.scroll_into_view_if_needed()
        box = shelf.bounding_box()
        session = self.context.new_cdp_session(self.page)
        x, y = box['x'] + 280, box['y'] + 40
        session.send('Input.dispatchTouchEvent', {'type':'touchStart', 'touchPoints':[{'x':x,'y':y}]})
        for step in range(1, 8):
            session.send('Input.dispatchTouchEvent', {'type':'touchMove', 'touchPoints':[{'x':x-20*step,'y':y}]})
        self.page.wait_for_timeout(520)
        session.send('Input.dispatchTouchEvent', {'type':'touchEnd', 'touchPoints':[]})
        expect(self.action('sort-done')).to_have_count(0)
        expect(self.action('manage')).to_have_count(0)
        self.assertGreater(shelf.evaluate('e=>e.scrollLeft'), 40)
        session.detach()

    def test_03_long_press_does_not_open_and_drag_order_persists(self):
        shelf = self.page.locator('#smartShelf')
        shelf.scroll_into_view_if_needed()
        before = self.order()
        box = self.action('group', before[0]).bounding_box()
        self.page.mouse.move(box['x']+40, box['y']+40)
        self.page.mouse.down()
        self.page.wait_for_timeout(540)
        self.page.mouse.up()
        expect(self.action('sort-done')).to_be_visible()
        expect(self.action('manage')).to_have_count(0)
        source = self.action('group', before[2]).bounding_box()
        target = self.action('group', before[0]).bounding_box()
        self.page.mouse.move(source['x']+source['width']/2, source['y']+40)
        self.page.mouse.down()
        self.page.mouse.move(target['x']+target['width']/2-20, target['y']+40, steps=12)
        self.page.mouse.up()
        self.action('sort-done').click()
        after = self.order()
        self.assertNotEqual(after, before, 'Dragging must change order')
        self.assertEqual(after[0], before[2])
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.order(), after)
        self.restore_default()
        self.assertEqual(self.order(), before)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.order(), before)

    def test_03b_touch_long_press_reorders_without_scrolling_page(self):
        shelf = self.page.locator('#smartShelf')
        shelf.scroll_into_view_if_needed()
        before = self.order()
        source = self.action('group', before[2]).bounding_box()
        session = self.context.new_cdp_session(self.page)
        x, y = source['x']+source['width']/2, source['y']+40
        session.send('Input.dispatchTouchEvent', {'type':'touchStart', 'touchPoints':[{'x':x,'y':y}]})
        self.page.wait_for_timeout(540)
        expect(self.action('sort-done')).to_be_visible()
        initial_top = self.page.locator('#appScreen').evaluate('e=>e.scrollTop')
        target = self.action('group', before[0]).bounding_box()
        end_x, end_y = target['x']+target['width']/2-15, target['y']+40
        for step in range(1, 9):
            session.send('Input.dispatchTouchEvent', {'type':'touchMove', 'touchPoints':[{'x':x+(end_x-x)*step/8,'y':y+(end_y-y)*step/8}]})
        session.send('Input.dispatchTouchEvent', {'type':'touchEnd', 'touchPoints':[]})
        self.assertEqual(self.order()[0], before[2])
        self.assertAlmostEqual(self.page.locator('#appScreen').evaluate('e=>e.scrollTop'), initial_top, delta=3)
        expect(self.action('manage')).to_have_count(0)
        self.action('sort-done').click()
        session.detach()

    def test_04_old_pins_hidden_and_corrections_are_migrated(self):
        self.seed({'pins':['life','travel'], 'hidden':['food'], 'exclude':{'design':['d1']}, 'smartOn':True})
        self.assertEqual(self.order()[:2], ['travel','life'])
        self.assertNotIn('food', self.order())
        self.assertEqual(self.state().get('exclude', {}).get('design'), ['d1'])
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.order()[:2], ['travel','life'])
        self.group('design')
        self.assertNotIn('d1', self.ids())
        expect(self.action('group-menu')).to_have_count(0)
        expect(self.action('pin')).to_have_count(0)
        self.home()
        self.toggle_visible('food')
        self.assertIn('food', self.order())
        self.assertEqual(self.order()[:2], ['travel','life'])

    def test_05_management_starts_empty_and_exit_clears_selection(self):
        self.group()
        self.start_manage()
        expect(self.page.locator('.pagehead')).to_contain_text('已选择 0 篇')
        for name in ('batch-remove', 'batch-add', 'batch-unsave'):
            expect(self.action(name)).to_be_disabled()
        self.select()
        expect(self.page.locator('.pagehead')).to_contain_text('已选择 1 篇')
        self.action('manage-exit').click()
        self.start_manage()
        expect(self.page.locator('.pagehead')).to_contain_text('已选择 0 篇')
        self.action('select-all').click()
        expect(self.page.locator('.pagehead')).to_contain_text(f'已选择 {self.action("select-note").count()} 篇')
        self.action('select-all').click()
        expect(self.page.locator('.pagehead')).to_contain_text('已选择 0 篇')

    def test_06_batch_remove_is_virtual_and_undo_restores(self):
        self.group()
        self.start_manage()
        self.select()
        self.action('batch-remove').click()
        expect(self.action('undo')).to_be_visible()
        self.assertNotIn('d1', self.ids('select-note') + self.ids())
        self.action('undo').click()
        self.assertIn('d1', self.ids('select-note') + self.ids())
        if self.action('manage-exit').count():
            self.action('manage-exit').click()
        self.start_manage()
        self.select()
        self.action('batch-remove').click()
        if self.action('manage-exit').count():
            self.action('manage-exit').click()
        self.home()
        self.action('album', '视觉设计灵感').click()
        self.assertIn('d1', self.ids())
        self.page.reload(wait_until='networkidle')
        self.group()
        self.assertNotIn('d1', self.ids())

    def test_07_batch_add_to_other_group_has_real_membership(self):
        self.group()
        self.start_manage()
        self.select()
        self.action('batch-add').click()
        self.action('target-group', 'travel').click()
        self.action('target-group', 'home').click()
        self.action('target-confirm').click()
        if self.action('manage-exit').count():
            self.action('manage-exit').click()
        self.home()
        for group in ('travel', 'home', 'design'):
            self.group(group)
            self.assertIn('d1', self.ids())
            self.home()
        self.page.reload(wait_until='networkidle')
        self.group('travel')
        self.assertIn('d1', self.ids())

    def test_08_cancel_collection_requires_confirmation_and_syncs_original(self):
        self.group()
        self.start_manage()
        self.select()
        self.action('batch-unsave').click()
        expect(self.action('confirm-unsave')).to_be_visible()
        self.action('close').click()
        self.assertIn('d1', self.ids('select-note'))
        self.action('batch-unsave').click()
        self.action('confirm-unsave').click()
        self.assertNotIn('d1', self.ids('select-note') + self.ids())
        self.action('undo').click()
        self.assertIn('d1', self.ids('select-note') + self.ids())
        if self.action('manage-exit').count():
            self.action('manage-exit').click()
        self.start_manage()
        self.select()
        self.action('batch-unsave').click()
        self.action('confirm-unsave').click()
        if self.action('manage-exit').count():
            self.action('manage-exit').click()
        self.home()
        self.action('album', '视觉设计灵感').click()
        self.assertNotIn('d1', self.ids())
        self.page.reload(wait_until='networkidle')
        self.group()
        self.assertNotIn('d1', self.ids())

    def test_09_stable_cover_after_simulated_save_and_custom_sort(self):
        custom = ['life','home','food','travel','design','career']
        self.seed({'order':custom, 'hidden':[], 'exclude':{}})
        before = self.action('group', 'home').locator('img').get_attribute('src')
        self.save_note('new1')
        after = self.action('group', 'home').locator('img').get_attribute('src')
        self.assertEqual(after, before)
        self.assertEqual(self.order(), custom, 'New favorites must preserve custom group order')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.action('group', 'home').locator('img').get_attribute('src'), before)
        self.assertEqual(self.order(), custom)
        self.restore_default()
        self.assertEqual(self.order()[0], 'home')
        self.assertIsNone(self.state().get('order'))
        self.toggle_visible('home')
        self.assertNotIn('home', self.order())
        self.page.reload(wait_until='networkidle')
        self.assertNotIn('home', self.order())
        self.toggle_visible('home')
        self.assertEqual(self.order()[0], 'home')


class PhaseB(BrowserCase):
    def test_10_add_existing_favorites_is_manual_persistent_preference(self):
        self.seed({'exclude':{'design':['d1']}, 'hidden':[], 'pins':[]})
        self.group()
        self.open_picker()
        expect(self.page.locator('.pagehead')).to_contain_text('所有帖子')
        expect(self.action('picker-confirm')).to_be_disabled()
        expect(self.action('picker-toggle', 'd2')).to_be_disabled()
        self.action('picker-toggle', 'd1').click()
        self.action('picker-toggle', 't1').click()
        self.action('picker-confirm').click()
        expect(self.action('manage')).to_be_visible()
        self.assertIn('d1', self.ids())
        self.assertIn('t1', self.ids())
        self.page.reload(wait_until='networkidle')
        self.group()
        self.assertIn('d1', self.ids())
        self.assertIn('t1', self.ids())
        self.open_picker()
        expect(self.action('picker-toggle', 'd1')).to_be_disabled()
        expect(self.action('picker-toggle', 't1')).to_be_disabled()
        self.action('picker-close').click()

    def test_11_note_detail_and_scroll_return(self):
        self.group()
        screen = self.page.locator('#appScreen')
        screen.evaluate('e=>e.scrollTop=500')
        visible = self.action('note', 'd4')
        visible.scroll_into_view_if_needed()
        old_top = screen.evaluate('e=>e.scrollTop')
        visible.click()
        expect(self.page.locator('.note-detail')).to_be_visible()
        expect(self.page.locator('.note-author')).to_be_visible()
        expect(self.page.locator('.note-body')).not_to_be_empty()
        expect(self.page.locator('.note-tags')).not_to_be_empty()
        expect(self.page.locator('.sheet')).to_have_count(0)
        self.assert_assets()
        self.action('note-back').click()
        self.assertAlmostEqual(screen.evaluate('e=>e.scrollTop'), old_top, delta=3)
        self.exclude_note('d1')
        self.assertNotIn('d1', self.ids())
        self.action('undo').click()
        self.assertIn('d1', self.ids())

    def test_12_responsive_detail_and_assets(self):
        for width, height in ((375,844),(390,844),(430,844),(1440,900)):
            with self.subTest(width=width):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.reload(wait_until='networkidle')
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                self.group()
                self.assert_assets()
                self.action('note', 'd1').click()
                self.assert_assets()
                dimensions = self.page.locator('#appScreen').evaluate('e=>[e.scrollWidth,e.clientWidth]')
                self.assertLessEqual(dimensions[0],dimensions[1]+1)
                self.action('note-back').click()
                self.home()


    def test_13_share_snapshot_is_fixed_current_group_and_private_state_isolated(self):
        self.context.grant_permissions(['clipboard-read','clipboard-write'])
        self.group()
        expected=set(self.ids())
        self.action('share').click()
        self.action('share-channel','copy').click()
        self.page.wait_for_function("document.querySelector('.phone').dataset.copyStatus==='copied'")
        link=self.page.evaluate('navigator.clipboard.readText()')
        payload=json.loads(base64.urlsafe_b64decode(urlsplit(link).fragment[6:]+'='*(-len(urlsplit(link).fragment[6:])%4)))
        self.assertEqual(set(payload),{'v','name','noteIds'})
        self.assertEqual(set(payload['noteIds']),expected)
        original=self.state()['copies'][0]
        self.home()
        self.save_note('new2')
        self.assertEqual(self.state()['copies'][0],original)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['copies'][0],original)
        private=self.state()
        self.page.goto(link,wait_until='networkidle')
        expect(self.page.locator('.share-preview')).to_be_visible()
        self.assertEqual(set(self.ids('shared-note')),expected)
        self.assertEqual(self.state(),private)
        expect(self.action('group')).to_have_count(0)
        expect(self.action('manage')).to_have_count(0)
        self.action('shared-note','d1').click()
        expect(self.page.locator('.note-detail')).to_be_visible()
        expect(self.action('note-menu')).to_have_count(0)
        expect(self.action('note-save')).to_have_count(0)
        self.action('shared-note-back').click()
        self.assertEqual(set(self.ids('shared-note')),expected)
        self.assertEqual(self.state(),private)
        recipient=self.browser.new_context(viewport={'width':390,'height':844})
        page=recipient.new_page()
        try:
            page.goto(link,wait_until='networkidle')
            expect(page.locator('[data-action="shared-note"]')).to_have_count(len(expected))
        finally:
            recipient.close()

    def test_14_friend_selection_confirmation_undo_and_persistence(self):
        self.group()
        self.action('share-invite').click()
        expect(self.page.locator('#appScreen')).to_contain_text('共享专辑')
        self.action('friends-toggle').click()
        self.action('friend-toggle', 'lin').click()
        expect(self.action('friend-toggle', 'lin')).to_have_attribute('aria-pressed', 'true')
        self.action('friend-toggle', 'lin').click()
        expect(self.action('friend-toggle', 'lin')).to_have_attribute('aria-pressed', 'false')
        self.action('friend-toggle', 'qiao').click()
        self.action('friends-done').click()
        expect(self.action('share-confirm')).to_have_count(0)
        copy = self.state()['copies'][0]
        self.assertEqual(copy['friends'], ['qiao'])
        expect(self.page.locator('#toastLayer')).to_contain_text('模拟')
        self.action('undo').click()
        self.assertFalse(any('qiao' in c.get('friends', []) for c in self.state().get('copies', [])))
        self.action('share-invite').click()
        if self.action('friends-toggle').get_attribute('aria-checked') != 'true':
            self.action('friends-toggle').click()
        self.action('friend-toggle', 'an').click()
        self.action('friends-done').click()
        expect(self.action('share-confirm')).to_have_count(0)
        self.page.reload(wait_until='networkidle')
        self.group()
        self.action('share-invite').click()
        expect(self.action('friend-toggle', 'an')).to_have_attribute('aria-pressed', 'true')
        expect(self.action('friend-toggle', 'lin')).to_have_attribute('aria-pressed', 'false')
        self.action('friends-toggle').click()
        self.action('friends-done').click()
        self.assertFalse(self.state()['groupSharing']['design']['enabled'])

    def test_15_malformed_share_link_fails_closed(self):
        self.seed({'hidden':['life'], 'exclude':{'design':['d1']}, 'extraAlbums':[{'id':'private','name':'PRIVATE USER ALBUM','covers':['design_grid'],'locked':True,'count':0}]})
        private = self.state()
        self.page.goto(OPTIONS.base_url.rstrip('/') + '/#share=invalid', wait_until='networkidle')
        expect(self.page.locator('.no-results')).to_contain_text('链接无效')
        expect(self.action('group')).to_have_count(0)
        expect(self.action('album')).to_have_count(0)
        self.assertNotIn('PRIVATE USER ALBUM', self.page.locator('#appScreen').inner_text())
        self.assertEqual(self.state(), private)


    def test_18_entering_share_clears_private_undo_toast(self):
        self.group()
        self.start_manage()
        self.select('d1')
        self.action('batch-remove').click()
        expect(self.action('undo')).to_be_visible()
        private = self.state()
        payload = {'v':1,'name':'已确认的演示副本','noteIds':['d2']}
        encoded = base64.urlsafe_b64encode(json.dumps(payload, ensure_ascii=False).encode()).decode().rstrip('=')
        self.page.goto(OPTIONS.base_url.rstrip('/') + '/#share=' + encoded, wait_until='networkidle')
        expect(self.page.locator('.share-preview')).to_be_visible()
        expect(self.action('undo')).to_have_count(0)
        expect(self.page.locator('#toastLayer')).to_be_empty()
        self.assertEqual(self.ids('shared-note'), ['d2'])
        self.assertEqual(self.state(), private)

    def test_19_globally_unsaved_simulated_note_can_be_collected_again_and_undone(self):
        self.save_note('new1')
        self.group('home')
        self.start_manage()
        self.select('new1')
        self.action('batch-unsave').click()
        self.action('confirm-unsave').click()
        self.assertNotIn('new1', self.ids())
        self.home()
        self.save_note('new1')
        self.action('undo').click()
        self.group('home')
        self.assertNotIn('new1', self.ids(), 'Undo recollection must restore globally-unsaved state')
        self.home()
        self.save_note('new1')
        self.page.reload(wait_until='networkidle')
        self.group('home')
        expect(self.action('note', 'new1')).to_have_count(1)


class PhaseC(BrowserCase):
    def test_16_title_mobile_system_bar_and_desktop_shell(self):
        expect(self.page).to_have_title('RE｜智能收藏')
        for width in (375, 390, 430):
            self.page.set_viewport_size({'width':width,'height':844})
            expect(self.page.locator('.status')).to_be_hidden()
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
        self.page.set_viewport_size({'width':1440,'height':900})
        expect(self.page.locator('.status')).to_be_visible()
        self.assertEqual(self.page.locator('.phone').evaluate('e=>e.getBoundingClientRect().width'), 406)
        self.assertEqual(self.page.locator('#appScreen').evaluate('e=>e.clientWidth'), 390)
        expect(self.page.locator('.brief')).to_be_visible()

    def test_17_every_note_has_original_detail_and_local_media(self):
        notes = self.page.evaluate('RE_BOOTSTRAP.notes')
        self.assertEqual(len(notes), 38)
        for note in notes:
            with self.subTest(note=note['id']):
                self.assertTrue(note.get('author', {}).get('name'))
                self.assertTrue(note.get('author', {}).get('avatar'))
                self.assertGreater(len(note.get('body', '')), 30)
                self.assertTrue(note.get('images'))
                self.assertTrue(all(not src.startswith(('http:', 'https:', '//')) for src in note['images']))
        for group, note in (('design','d1'),('travel','t1'),('career','c1'),('home','h1'),('food','f1'),('life','l1')):
            self.group(group)
            self.action('note', note).click()
            self.assert_assets()
            expect(self.page.locator('.note-author img')).to_be_visible()
            self.assertGreater(self.page.locator('.note-gallery img').count(), 0)
            self.action('note-back').click()
            self.home()


if __name__ == '__main__':
    suite = unittest.TestSuite()
    for cls in ([PhaseA] if OPTIONS.phase == 'A' else [PhaseB] if OPTIONS.phase == 'B' else [PhaseC] if OPTIONS.phase == 'C' else [PhaseA, PhaseB, PhaseC]):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
