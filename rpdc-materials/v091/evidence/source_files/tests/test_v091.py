"""v0.9.1 interaction reduction, immutable snapshots and native reading.

Uses shipped simulated data and actual browser input. Native share is stubbed
only when verifying the system API handoff; no social message is sent.
"""
import base64
import copy
import json
from pathlib import Path
from urllib.parse import urlsplit
import unittest

from playwright.sync_api import expect
from test_v08 import BrowserCase

ROOT=Path(__file__).resolve().parents[1]
KEY='refold-v05-experience-data'


def payload(link):
    encoded=urlsplit(link).fragment.removeprefix('share=')
    return json.loads(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)))


def legacy_link(base,ids,name='旧版共享副本'):
    data=json.dumps({'v':1,'name':name,'noteIds':ids},ensure_ascii=False).encode()
    return base.split('#')[0]+'#share='+base64.urlsafe_b64encode(data).decode().rstrip('=')


class FinalReduction(BrowserCase):
    def copy_group(self):
        self.context.grant_permissions(['clipboard-read','clipboard-write'])
        self.action('share').click()
        self.action('share-channel','copy').click()
        self.page.wait_for_function("document.querySelector('.phone').dataset.copyStatus==='copied'")
        expect(self.page.locator('.phone')).to_have_attribute('data-page','group')
        expect(self.action('share-select')).to_have_count(0)
        expect(self.action('share-confirm')).to_have_count(0)
        return self.page.evaluate('navigator.clipboard.readText()')

    def test_01_copy_snapshots_whole_current_group_without_later_sync(self):
        self.group()
        expected=set(self.ids())
        originalAlbums=self.page.evaluate('RE_BOOTSTRAP.notes.map(n=>[n.id,n.originalAlbum])')
        link=self.copy_group()
        self.assertEqual(set(payload(link)['noteIds']),expected)
        first=copy.deepcopy(self.state()['copies'][0])
        self.home()
        self.save_note('new2')
        self.group()
        self.assertIn('new2',self.ids())
        currentOrder=self.ids()
        secondLink=self.copy_group()
        self.assertEqual(set(payload(secondLink)['noteIds']),expected|{'new2'})
        self.assertEqual(self.state()['copies'][0],first)
        self.assertEqual(self.page.evaluate('RE_BOOTSTRAP.notes.map(n=>[n.id,n.originalAlbum])'),originalAlbums)
        self.page.goto(secondLink,wait_until='networkidle')
        self.assertEqual(self.ids('shared-note'),currentOrder)
        self.page.goto(link,wait_until='networkidle')
        self.assertEqual(set(self.ids('shared-note')),expected)
        expect(self.action('shared-note','new2')).to_have_count(0)

    def test_02_snapshot_respects_manual_preferences_and_global_unsaves(self):
        self.seed({'exclude':{'design':['d1']},'manual':{'design':['t1']},'removed':['d2'],'hidden':['life']})
        self.group()
        expected=set(self.ids())
        self.assertIn('t1',expected)
        self.assertNotIn('d1',expected)
        self.assertNotIn('d2',expected)
        before=self.state()
        link=self.copy_group()
        self.assertEqual(set(payload(link)['noteIds']),expected)
        after=self.state()
        for field in ('exclude','manual','removed','hidden'):
            self.assertEqual(before[field],after[field])

    def test_03_channels_handoff_directly_and_friends_only_record_locally(self):
        self.page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{window.systemShares=[...(window.systemShares||[]),data]}})")
        self.page.evaluate("Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true})")
        self.group()
        expected=set(self.ids())
        for channel in ('native','wechat','moments','qq','weibo'):
            self.action('share').click()
            self.action('share-channel',channel).click()
            expect(self.action('share-confirm')).to_have_count(0)
            expect(self.page.locator('.phone')).to_have_attribute('data-page','group')
        shares=self.page.evaluate('window.systemShares')
        self.assertEqual(len(shares),5)
        for item in shares:
            self.assertEqual(set(payload(item['url'])['noteIds']),expected)
        before=len(self.state()['copies'])
        self.action('share').click()
        self.action('share-friend','lin').click()
        expect(self.page.locator('.sheet')).to_have_count(0)
        expect(self.page.locator('#toastLayer')).to_contain_text('未发送消息')
        self.assertEqual(len(self.state()['copies']),before+1)
        last=self.state()['copies'][-1]
        self.assertEqual(set(last['noteIds']),expected)
        self.assertEqual(last['demoShares'][0]['friendId'],'lin')

    def test_04_empty_group_disables_share_and_cannot_create_empty_copy(self):
        self.group()
        ids=self.ids()
        self.home()
        self.seed({'exclude':{'design':ids}})
        self.group()
        expect(self.action('share')).to_be_disabled()
        expect(self.page.locator('.no-results')).to_contain_text('添加后即可分享')
        self.action('share-invite').click()
        self.action('friends-toggle').click()
        expect(self.action('friends-toggle')).to_have_attribute('aria-checked','false')
        expect(self.page.locator('#toastLayer')).to_contain_text('暂无笔记')
        self.action('friends-done').click()
        self.assertEqual(self.state().get('copies',[]),[])

    def test_05_friends_done_creates_current_snapshot_and_preserves_legacy_copy(self):
        legacy={'id':'legacy','sourceGroup':'design','name':'旧版快照','noteIds':['d1'],'friends':['lin'],'sharingEnabled':True,'createdAt':'2026-11-01T00:00:00Z','customLegacyField':'keep'}
        initial={'copies':[legacy],'exclude':{'design':['d2']},'manual':{'design':['t1']},'hidden':['life']}
        self.seed(initial)
        base=self.page.url
        self.group()
        expected=set(self.ids())
        self.action('share-invite').click()
        expect(self.action('friends-toggle')).to_have_attribute('aria-checked','true')
        expect(self.action('friend-toggle','lin')).to_have_attribute('aria-pressed','true')
        self.action('friend-toggle','qiao').click()
        self.action('friends-done').click()
        expect(self.action('manage')).to_be_visible()
        expect(self.action('share-confirm')).to_have_count(0)
        state=self.state()
        self.assertEqual(state['copies'][0],legacy)
        current=state['copies'][-1]
        self.assertEqual(set(current['noteIds']),expected)
        self.assertEqual(set(current['friends']),{'lin','qiao'})
        self.assertEqual(state['groupSharing']['design']['copyId'],current['id'])
        expect(self.page.locator('.member-avatars img')).to_have_count(2)
        expect(self.page.locator('.member-avatars img[alt="乔乔在路上"]')).to_have_attribute('src','assets/author-travel.svg')
        self.page.goto(legacy_link(base,['d1']),wait_until='networkidle')
        self.assertEqual(self.ids('shared-note'),['d1'])
        self.action('shared-note','d1').click()
        expect(self.page.locator('.native-note')).to_be_visible()
        expect(self.page.locator('#noteReadBar')).to_be_visible()
        self.assertEqual(self.state(),state)

    def test_06_cancel_off_and_undo_preserve_personal_and_historical_state(self):
        old={'id':'legacy','sourceGroup':'design','name':'旧版快照','noteIds':['d1'],'friends':['lin'],'sharingEnabled':True}
        self.seed({'copies':[old],'groupSharing':{'design':{'enabled':True,'copyId':'legacy'},'home':{'enabled':False,'copyId':None}},'hidden':['life'],'exclude':{'design':['d2']}})
        self.group()
        before=self.state()
        expected=self.ids()
        self.action('share-invite').click()
        self.action('friend-toggle','an').click()
        self.action('friends-cancel').click()
        self.assertEqual(self.state(),before)
        self.action('share-invite').click()
        self.action('friends-toggle').click()
        self.action('friends-done').click()
        state=self.state()
        self.assertFalse(state['groupSharing']['design']['enabled'])
        self.assertEqual(state['copies'],before['copies'])
        self.assertEqual(self.ids(),expected)
        for field in ('hidden','exclude'):
            self.assertEqual(state[field],before[field])
        self.action('undo').click()
        self.assertEqual(self.state()['groupSharing'],before['groupSharing'])
        self.assertEqual(self.state()['copies'],before['copies'])
        self.assertEqual(self.ids(),expected)

    def test_07_home_sheet_has_only_three_actions_and_cancel_without_handle(self):
        self.settings()
        sheet=self.page.locator('.home-settings-sheet')
        self.assertEqual(sheet.locator('[data-action]').evaluate_all('els=>els.map(e=>e.dataset.action)'),['sort-start','display-settings','smart-toggle','close'])
        expect(sheet.locator('.handle')).to_have_count(0)
        expect(sheet.locator('h3')).to_have_count(0)
        expect(sheet.locator('.choice')).to_have_count(0)
        self.action('close').click()
        expect(self.page.locator('.ai-mark')).to_have_count(1)
        expect(self.page.locator('#smartShelf .ai-mark')).to_have_count(0)
        expect(self.page.locator('.phone [data-action="simulate"]')).to_have_count(0)
        expect(self.page.locator('.phone [data-action="about"]')).to_have_count(0)
        self.settings()
        self.action('sort-start').click()
        self.action('sort-done').click()
        expect(self.page.locator('#toastLayer')).to_contain_text('顺序已保存')
        self.group()
        expect(self.page.locator('#toastLayer')).to_be_empty()
        self.action('share').click()
        expect(self.page.locator('.native-share-sheet .handle')).to_have_count(1)

    def test_08_restore_default_and_desktop_demo_are_outside_app_menu(self):
        self.seed({'order':['home','life','food','career','travel','design'],'hidden':['food'],'exclude':{'design':['d1']}})
        self.settings()
        self.action('sort-start').click()
        expect(self.page.locator('.sort-banner [data-action="sort-auto"]')).to_have_text('恢复默认')
        self.action('sort-auto').click()
        self.action('sort-done').click()
        self.assertIsNone(self.state()['order'])
        self.assertEqual(self.state()['hidden'],['food'])
        self.assertEqual(self.state()['exclude'],{'design':['d1']})
        self.toggle_visible('food')
        self.assertIn('food',self.order())
        expect(self.page.locator('#simulateDemo')).to_be_hidden()
        self.save_note('new1')
        self.assertEqual(self.order()[0],'home')
        self.page.set_viewport_size({'width':1440,'height':900})
        expect(self.page.locator('.brief #simulateDemo')).to_be_visible()
        expect(self.page.locator('.prototype-about')).to_be_visible()
        self.assertEqual(self.page.locator('#appScreen [data-action="save-note"]').count(),0)
        self.group('home')
        self.assertIn('new1',self.ids())

    def test_09_reading_page_is_native_static_and_preserves_preferences(self):
        self.seed({'liked':['d1'],'comments':{'d1':['PRIVATE OLD COMMENT']},'hidden':['life'],'exclude':{}})
        before=self.state()
        self.group()
        self.action('note','d1').click()
        expect(self.page.locator('.note-native-head .note-author img')).to_be_visible()
        expect(self.page.locator('.note-follow')).to_have_text('关注')
        expect(self.page.locator('.note-share-display svg')).to_be_visible()
        expect(self.page.locator('.reading-comment')).to_have_attribute('readonly','')
        expect(self.page.locator('.reading-metric')).to_have_count(3)
        for metric in self.page.locator('.reading-metric').all():
            expect(metric.locator('svg')).to_be_visible()
            self.assertTrue(any(c.isdigit() for c in metric.inner_text()))
            metric.click()
        self.page.locator('.note-follow').click()
        self.page.locator('.note-share-display').click()
        self.page.locator('.reading-comment').click()
        expect(self.page.locator('.sheet')).to_have_count(0)
        expect(self.page.locator('#toastLayer')).to_be_empty()
        expect(self.action('note-menu')).to_have_count(0)
        self.assertEqual(self.state(),before)
        self.assertNotIn('PRIVATE OLD COMMENT',self.page.locator('#appScreen').inner_text())
        note=next(n for n in json.loads((ROOT/'data/notes.json').read_text()) if n['id']=='d1')
        expect(self.page.locator('.note-body')).to_contain_text(note['body'].split('\n\n')[0])
        self.action('note-back').click()
        self.exclude_note('d1')
        self.assertNotIn('d1',self.ids())
        self.action('undo').click()
        self.assertIn('d1',self.ids())

    def test_10_multiple_local_images_swipe_and_indicator_without_data_changes(self):
        script=(ROOT/'data/offline-bundle.js').read_text()
        bundle=json.loads(script.split('globalThis.RE_BOOTSTRAP=',1)[1].rstrip(';\n'))
        note=next(n for n in bundle['notes'] if n['id']=='d1')
        note['images']=['assets/design_type.webp','assets/design_motion.webp']
        self.page.route('**/data/offline-bundle.js',lambda route:route.fulfill(content_type='application/javascript',body='globalThis.RE_BOOTSTRAP='+json.dumps(bundle,ensure_ascii=False)+';'))
        self.page.reload(wait_until='networkidle')
        self.group()
        self.action('note','d1').click()
        rail=self.page.locator('.note-gallery')
        expect(rail.locator('img')).to_have_count(2)
        expect(self.page.locator('.gallery-pagination')).to_have_text('1/2')
        box=rail.bounding_box()
        x,y=box['x']+box['width']-35,box['y']+130
        session=self.context.new_cdp_session(self.page)
        session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
        for step in range(1,9):
            session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-32*step,'y':y}]})
        session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        expect(self.page.locator('.gallery-pagination')).to_have_text('2/2')
        rail.focus()
        self.page.keyboard.press('ArrowLeft')
        expect(self.page.locator('.gallery-pagination')).to_have_text('1/2')
        self.assert_assets()
        session.detach()

    def test_11_responsive_reading_bar_images_and_gallery_return(self):
        for width,height in ((375,844),(390,844),(430,844),(1440,900)):
            with self.subTest(width=width):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.reload(wait_until='networkidle')
                self.group()
                self.action('note','d4').scroll_into_view_if_needed()
                top=self.page.locator('#appScreen').evaluate('e=>e.scrollTop')
                self.action('note','d4').click()
                self.assert_assets()
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                self.assertLessEqual(self.page.locator('#appScreen').evaluate('e=>e.scrollWidth-e.clientWidth'),1)
                bar=self.page.locator('#noteReadBar').bounding_box()
                phone=self.page.locator('.phone').bounding_box()
                self.assertAlmostEqual(bar['y']+bar['height'],phone['y']+phone['height']-(8 if width>=900 else 0),delta=2)
                self.page.locator('#appScreen').evaluate('e=>e.scrollTop=e.scrollHeight')
                self.assertEqual(self.page.locator('#noteReadBar').bounding_box(),bar)
                self.action('note-back').click()
                self.assertAlmostEqual(self.page.locator('#appScreen').evaluate('e=>e.scrollTop'),top,delta=3)

    def test_12_clipboard_denied_falls_back_to_openable_link_not_confirmation(self):
        self.page.evaluate("Object.defineProperty(navigator.clipboard,'writeText',{configurable:true,value:async()=>{throw Error('test permission denial')}});document.execCommand=()=>false")
        self.group()
        expected=set(self.ids())
        self.page.locator('#appScreen').evaluate('e=>e.scrollTop=250')
        previous=self.page.locator('#appScreen').evaluate('e=>e.scrollTop')
        # Use a real pointer on the visible sticky header; locator.click() itself
        # scrolls its original layout position into view before dispatching.
        box=self.action('share').bounding_box()
        self.page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2)
        self.action('share-channel','copy').click()
        link=self.page.locator('.share-link input')
        expect(link).to_be_visible()
        self.assertEqual(set(payload(link.input_value())['noteIds']),expected)
        expect(self.page.locator('.phone')).to_have_attribute('data-copy-status','manual')
        expect(self.action('share-confirm')).to_have_count(0)
        expect(self.page.locator('#toastLayer')).to_contain_text('未允许自动复制')
        self.assertNotIn('已复制',self.page.locator('#toastLayer').inner_text())
        self.action('copy-preview').click()
        self.action('share-exit').click()
        self.assertAlmostEqual(self.page.locator('#appScreen').evaluate('e=>e.scrollTop'),previous,delta=3)


if __name__=='__main__':
    unittest.main(argv=[__file__],verbosity=2)
