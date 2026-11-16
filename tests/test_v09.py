"""RE v0.9 native structure and real interaction regression.

Round 1 checks the functional native components. Round 2 checks motion, pointer
input, reduced motion and repeated actions. No social message or paid API is used.
"""
import argparse
import base64
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

from playwright.sync_api import expect
from test_v08 import BrowserCase

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--round', choices=('1', '2', 'all'), default='all')
parser.add_argument('--screenshot-dir', type=Path)
OPTIONS, _ = parser.parse_known_args()


class NativeStructure(BrowserCase):
    def test_01_collection_native_hierarchy_and_action_sheet(self):
        self.group()
        expect(self.page.locator('.collection-nav [data-action="share"]')).to_be_visible()
        expect(self.page.locator('.collection-nav [data-action="manage"]')).to_have_count(0)
        expect(self.page.locator('.collection-heading h1')).to_have_text('设计与创作')
        expect(self.page.locator('.collection-heading [data-action="manage"]')).to_be_visible()
        expect(self.page.locator('.collection-members [data-action="share-invite"]')).to_be_visible()
        expect(self.page.locator('.collection-count')).to_contain_text('笔记')
        expect(self.page.locator('.collection-tools')).to_have_count(0)
        expect(self.action('add-notes')).to_have_count(0)
        self.action('manage').click()
        sheet = self.page.locator('.action-sheet')
        expect(sheet).to_be_visible()
        self.assertEqual(sheet.locator('[data-action]').evaluate_all('els=>els.map(e=>e.dataset.action)'),
                         ['add-notes', 'manage-start', 'close'])
        self.assertEqual(sheet.locator('.choice').count(), 0)
        self.action('add-notes').click()
        expect(self.page.locator('.pagehead')).to_contain_text('所有帖子')
        self.action('picker-close').click()
        self.action('manage').click()
        self.action('manage-start').click()
        expect(self.page.locator('.pagehead')).to_contain_text('已选择 0 篇')
        expect(self.action('batch-remove')).to_be_disabled()

    def test_02_share_to_is_direct_native_sheet_with_svg_channels(self):
        self.group()
        self.action('share').click()
        dialog = self.page.locator('[role="dialog"]')
        expect(dialog).to_be_visible()
        expect(dialog).to_contain_text('分享至')
        expect(self.action('share-create')).to_have_count(0)
        expect(self.action('share-preview')).to_have_count(0)
        self.assertGreaterEqual(self.action('share-friend').count(), 3)
        for button in self.action('share-friend').all():
            expect(button.locator('img')).to_be_visible()
            self.assertTrue(button.inner_text().strip())
        for channel in ('copy', 'native', 'wechat', 'moments', 'qq', 'weibo'):
            button = self.action('share-channel', channel)
            expect(button).to_be_visible()
            expect(button.locator('svg')).to_be_attached()
            self.assertTrue(button.inner_text().strip())
        expect(self.action('close').locator('svg')).to_be_attached()
        self.assert_assets()

    def test_03_copy_current_scope_directly_to_openable_snapshot(self):
        self.context.grant_permissions(['clipboard-read','clipboard-write'])
        self.group()
        expected=set(self.ids())
        self.action('share').click()
        self.action('share-channel','copy').click()
        expect(self.action('share-confirm')).to_have_count(0)
        self.page.wait_for_function("document.querySelector('.phone').dataset.copyStatus==='copied'")
        link=self.page.evaluate('navigator.clipboard.readText()')
        encoded=urlsplit(link).fragment.removeprefix('share=')
        data=json.loads(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)))
        self.assertEqual(set(data['noteIds']),expected)
        self.assertEqual(set(data),{'v','name','noteIds'})
        self.page.goto(link,wait_until='networkidle')
        expect(self.action('shared-note')).to_have_count(len(expected))

    def test_04_invite_opens_full_settings_and_preserves_private_default(self):
        self.group()
        before = self.state()
        self.action('share-invite').click()
        expect(self.action('friends-cancel')).to_be_visible()
        expect(self.action('friends-done')).to_be_visible()
        expect(self.page.locator('#appScreen')).to_contain_text('共享专辑')
        expect(self.action('friends-toggle')).to_have_attribute('aria-checked', 'false')
        expect(self.action('friend-toggle', 'lin')).to_be_disabled()
        self.assertGreaterEqual(self.page.locator('[data-action="friend-toggle"] img').count(), 3)
        self.action('friends-cancel').click()
        self.assertEqual(self.state(), before, 'Cancel must not mutate personal or copy state')
        self.action('share-invite').click()
        self.action('friends-toggle').click()
        self.action('friend-toggle', 'lin').click()
        expect(self.action('friend-toggle', 'lin')).to_have_attribute('aria-pressed', 'true')
        expected=set(self.page.evaluate('RE_BOOTSTRAP.precomputed.assignments.filter(r=>r.memberships.some(m=>m.groupId==="design")).map(r=>r.noteId).filter(id=>RE_BOOTSTRAP.notes.some(n=>n.id===id&&n.availability==="initial"))'))
        self.action('friends-done').click()
        expect(self.action('share-confirm')).to_have_count(0)
        self.assertEqual(self.state()['copies'][-1]['friends'], ['lin'])
        self.assertEqual(set(self.state()['copies'][-1]['noteIds']),expected)
        expect(self.page.locator('#toastLayer')).to_contain_text('模拟')
        self.action('undo').click()
        self.assertEqual(self.state().get('copies', []), before.get('copies', []))
        self.assertIn('d1', self.ids())

    def test_05_sort_has_no_visible_controls_keyboard_and_visibility_persist(self):
        original = self.order()
        self.settings()
        self.action('sort-start').click()
        expect(self.action('sort-done')).to_be_visible()
        expect(self.page.locator('.sort-tools')).to_have_count(0)
        expect(self.action('hide')).to_have_count(0)
        expect(self.action('sort-left')).to_have_count(0)
        expect(self.action('sort-right')).to_have_count(0)
        self.action('group', original[0]).focus()
        self.page.keyboard.press('ArrowRight')
        self.action('sort-done').click()
        custom = self.order()
        self.assertNotEqual(custom, original)
        self.assertEqual(custom[1], original[0])
        self.settings()
        self.action('display-settings').click()
        expect(self.action('visibility-toggle', 'home')).to_have_attribute('role', 'switch')
        self.action('visibility-toggle', 'home').click()
        self.action('close').click()
        self.assertNotIn('home', self.order())
        self.page.reload(wait_until='networkidle')
        self.assertNotIn('home', self.order())
        self.settings()
        self.action('display-settings').click()
        self.action('visibility-toggle', 'home').click()
        self.action('close').click()
        self.assertEqual(self.order(), custom)
        self.restore_default()
        self.assertEqual(self.order(), original)

    def test_06_multiselect_uses_only_circle_and_cover_overlay(self):
        self.group()
        self.start_manage()
        self.action('select-note', 'd1').click()
        selected = self.action('select-note', 'd1')
        expect(selected).to_have_attribute('aria-pressed', 'true')
        self.assertEqual(selected.evaluate('e=>getComputedStyle(e).outlineStyle'), 'none')
        self.assertEqual(selected.evaluate('e=>getComputedStyle(e).outlineWidth'), '0px')
        expect(selected.locator('.check-circle svg')).to_be_visible()
        self.assertEqual(selected.locator('.check-circle').evaluate('e=>getComputedStyle(e).backgroundColor'), 'rgb(255, 36, 66)')
        self.assertEqual(self.action('select-note', 'd2').locator('.check-circle svg').count(), 0)
        self.action('manage-exit').click()
        self.start_manage()
        expect(self.page.locator('.pagehead')).to_contain_text('已选择 0 篇')

    def test_07_channels_use_system_share_without_false_delivery_claims(self):
        self.page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{window.channelPayload=data}});Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true})")
        self.group()
        expected=set(self.ids())
        for channel in ('wechat','moments','qq','weibo'):
            with self.subTest(channel=channel):
                self.action('share').click()
                self.action('share-channel',channel).click()
                expect(self.action('share-confirm')).to_have_count(0)
                expect(self.page.locator('#toastLayer')).to_contain_text('系统处理')
                data=self.page.evaluate('window.channelPayload')
                encoded=urlsplit(data['url']).fragment.removeprefix('share=')
                payload=json.loads(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)))
                self.assertEqual(set(payload['noteIds']),expected)
                self.assertNotIn('发送成功',self.page.locator('#toastLayer').inner_text())

    def test_07b_native_share_uses_confirmed_scope_and_copy_fallback(self):
        self.context.grant_permissions(['clipboard-read', 'clipboard-write'])
        self.page.evaluate("""() => {
            Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{window.nativePayload=data}});
            Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});
        }""")
        self.group()
        self.action('share').click()
        self.action('share-channel','native').click()
        expect(self.action('share-confirm')).to_have_count(0)
        data=self.page.evaluate('window.nativePayload')
        encoded=urlsplit(data['url']).fragment.removeprefix('share=')
        payload=json.loads(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)))
        self.assertEqual(set(payload['noteIds']),set(self.ids()))
        self.page.evaluate("Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>false})")
        self.action('share').click()
        self.action('share-channel','native').click()
        self.page.wait_for_function("document.querySelector('.phone').dataset.copyStatus==='copied'")
        self.assertEqual(self.page.evaluate('navigator.clipboard.readText()'),data['url'])

    def test_07c_clipboard_denial_is_honest_openable_fallback(self):
        self.page.evaluate("""() => {
            Object.defineProperty(navigator.clipboard,'writeText',{configurable:true,value:async()=>{throw Error('test denied')}});
            document.execCommand=()=>false;
        }""")
        self.group()
        self.action('share').click()
        self.action('share-channel','copy').click()
        expect(self.action('share-confirm')).to_have_count(0)
        link=self.page.locator('.share-link input')
        expect(link).to_be_visible()
        self.assertIn('#share=',link.input_value())
        expect(self.page.locator('.phone')).to_have_attribute('data-copy-status','manual')
        expect(self.page.locator('#toastLayer')).to_contain_text('未允许自动复制')
        self.assertNotIn('已复制',self.page.locator('#toastLayer').inner_text())


class NativeMotion(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.emulate_media(reduced_motion='no-preference')

    def test_08_sheet_handle_swipe_and_scrim_close_without_double_actions(self):
        self.group()
        self.action('share').click()
        sheet = self.page.locator('.sheet')
        expect(sheet).to_be_visible()
        self.page.wait_for_timeout(350)
        handle = sheet.locator('.handle')
        box = handle.bounding_box()
        self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
        self.page.mouse.down()
        self.page.mouse.move(box['x'] + box['width']/2, box['y'] + 150, steps=12)
        self.page.mouse.up()
        expect(self.page.locator('.sheet')).to_have_count(0)
        self.action('manage').click()
        self.action('close').click(click_count=2)
        expect(self.page.locator('.sheet')).to_have_count(0)
        self.action('share').click()
        self.page.locator('#backdrop').click(position={'x':3, 'y':3})
        expect(self.page.locator('.sheet')).to_have_count(0)
        expect(self.action('manage')).to_be_enabled()

    def test_09_internal_sheet_scroll_is_not_a_dismiss_gesture(self):
        self.page.set_viewport_size({'width':390, 'height':550})
        self.group()
        self.action('share').click()
        sheet = self.page.locator('.sheet')
        expect(sheet).to_be_visible()
        self.page.wait_for_timeout(350)
        # A gesture begun on content is a normal content interaction, not a handle drag.
        row = self.action('share-channel', 'wechat')
        box = row.bounding_box()
        x, y = box['x']+box['width']/2, box['y']+box['height']/2
        session = self.context.new_cdp_session(self.page)
        session.send('Input.dispatchTouchEvent', {'type':'touchStart', 'touchPoints':[{'x':x,'y':y}]})
        for step in range(1, 6):
            session.send('Input.dispatchTouchEvent', {'type':'touchMove', 'touchPoints':[{'x':x,'y':y+12*step}]})
        session.send('Input.dispatchTouchEvent', {'type':'touchEnd', 'touchPoints':[]})
        expect(sheet).to_be_visible()
        expect(self.page.locator('.native-share')).to_be_visible()
        self.assertFalse(self.state().get('copies',[]))
        session.detach()

    def test_10_navigation_animates_and_returns_to_previous_scroll(self):
        self.group()
        screen = self.page.locator('#appScreen')
        self.page.wait_for_timeout(300)
        self.action('note', 'd4').scroll_into_view_if_needed()
        top = screen.evaluate('e=>e.scrollTop')
        self.action('note', 'd4').dispatch_event('click')
        animations=screen.evaluate('e=>e.getAnimations().map(a=>({state:a.playState,duration:a.effect.getTiming().duration}))')
        self.assertTrue(any(a['state']=='running' and 180<=a['duration']<=300 for a in animations), animations)
        expect(self.page.locator('.note-detail')).to_be_visible()
        self.page.wait_for_timeout(300)
        self.action('note-back').dispatch_event('click')
        self.assertTrue(screen.evaluate('e=>e.getAnimations().some(a=>a.playState==="running")'), 'Return should animate')
        expect(self.action('manage')).to_be_visible()
        self.page.wait_for_timeout(300)
        self.assertAlmostEqual(screen.evaluate('e=>e.scrollTop'), top, delta=3)

    def test_11_dragged_tile_follows_pointer_and_preserves_order(self):
        self.settings()
        self.action('sort-start').click()
        self.page.wait_for_timeout(300)
        source = self.action('group', 'career')
        source.scroll_into_view_if_needed()
        box = source.bounding_box()
        self.page.mouse.move(box['x']+box['width']/2, box['y']+35)
        self.page.mouse.down()
        self.page.mouse.move(box['x']+box['width']/2-40, box['y']+45, steps=6)
        dragging = self.page.locator('.smart-tile.dragging')
        expect(dragging).to_have_count(1)
        ghost = self.page.locator('.sort-drag-ghost')
        expect(ghost).to_be_visible()
        first = ghost.bounding_box()
        self.page.mouse.move(box['x']+box['width']/2-60, box['y']+55, steps=4)
        moved = ghost.bounding_box()
        self.assertLess(moved['x'], first['x']-10)
        self.assertGreater(moved['y'], first['y']+5)
        self.page.mouse.move(box['x']-135, box['y']+45, steps=10)
        self.page.mouse.up()
        self.action('sort-done').click()
        order = self.order()
        self.assertNotEqual(order.index('career'), 2)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.order(), order)

    def test_12_reduced_motion_keeps_complete_functionality(self):
        self.page.emulate_media(reduced_motion='reduce')
        self.action('group', 'design').dispatch_event('click')
        durations = self.page.locator('#appScreen').evaluate('e=>e.getAnimations().map(a=>a.effect.getTiming().duration)')
        self.assertTrue(all(duration <= 10 for duration in durations), durations)
        expect(self.action('manage')).to_be_visible()
        self.action('share').click()
        durations = self.page.locator('.sheet').evaluate('e=>e.getAnimations().map(a=>a.effect.getTiming().duration)')
        self.assertTrue(all(duration <= 10 for duration in durations), durations)
        self.action('close').click()
        self.open_picker()
        expect(self.action('picker-confirm')).to_be_disabled()
        self.action('picker-close').click()
        self.start_manage()
        self.select('d1')
        self.action('batch-remove').click()
        self.action('undo').click()
        self.assertIn('d1', self.ids())

    def test_13_responsive_components_assets_and_repeated_selection(self):
        for width, height in ((375,844), (390,844), (430,844), (1440,900)):
            with self.subTest(width=width):
                self.page.set_viewport_size({'width':width, 'height':height})
                self.page.reload(wait_until='networkidle')
                self.group()
                self.assert_assets()
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                self.assertLessEqual(self.page.locator('#appScreen').evaluate('e=>e.scrollWidth-e.clientWidth'), 1)
                self.start_manage()
                self.action('select-note', 'd1').click(click_count=2)
                expect(self.action('select-note', 'd1')).to_have_attribute('aria-pressed', 'false')
                self.action('select-note', 'd1').click()
                self.action('batch-remove').click()
                self.action('undo').click()
                self.assertIn('d1', self.ids())
                self.home()


    def test_14_touch_handle_and_no_web_animations_fallback(self):
        self.page.evaluate('Element.prototype.animate=undefined;globalThis.structuredClone=undefined')
        self.group()
        self.action('share').click()
        self.page.wait_for_timeout(350)
        handle=self.page.locator('.sheet .handle').bounding_box()
        x,y=handle['x']+handle['width']/2,handle['y']+2
        session=self.context.new_cdp_session(self.page)
        session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
        for step in range(1,10):
            session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y+15*step}]})
        session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        expect(self.page.locator('.sheet')).to_have_count(0)
        session.detach()
        self.action('note','d1').click()
        expect(self.page.locator('.note-detail')).to_be_visible()
        self.action('note-back').click()
        expect(self.action('manage')).to_be_visible()
        self.start_manage()
        self.select('d1')
        self.action('batch-remove').click()
        self.action('undo').click()
        self.assertIn('d1',self.ids())

    def test_15_closing_sheet_cannot_remove_replacement(self):
        self.group()
        self.action('share').click()
        self.page.wait_for_timeout(320)
        self.action('close').dispatch_event('click')
        self.action('manage').dispatch_event('click')
        self.page.wait_for_timeout(350)
        expect(self.page.locator('.action-row')).to_have_count(3)
        self.assertTrue(self.page.locator('#appScreen').evaluate('e=>e.inert'))
        self.action('add-notes').click()
        expect(self.page.locator('.pagehead')).to_contain_text('所有帖子')
        expect(self.page.locator('.sheet')).to_have_count(0)


if __name__ == '__main__':
    classes = [NativeStructure] if OPTIONS.round == '1' else [NativeMotion] if OPTIONS.round == '2' else [NativeStructure, NativeMotion]
    suite = unittest.TestSuite()
    for cls in classes:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
