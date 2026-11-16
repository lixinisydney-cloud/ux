"""Capture unmodified RE:FOLD v0.9.1 DOM and native Playwright videos.

Windows: py -m pip install playwright; py -m playwright install chromium
py capture_materials.py --mode recordings --output ../ --base-url https://lixinisydney-cloud.github.io/ux/
CDP touch input requires Chromium. No UI injection, state seeding or API calls.
"""
import argparse
import base64
import hashlib
import json
import math
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit, unquote

from playwright.sync_api import sync_playwright, expect

PARSER = argparse.ArgumentParser()
PARSER.add_argument('--base-url', default='https://lixinisydney-cloud.github.io/ux/')
PARSER.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1])
PARSER.add_argument('--repo', type=Path, help='Optional original repo, for existing screenshot reuse')
PARSER.add_argument('--chromium', help='Optional Chromium executable path')
PARSER.add_argument('--mode', choices=['screenshots', 'recordings', 'all'], default='all')
PARSER.add_argument('--verified-transport', action='store_true', help='Cloud only: urllib validates upstream HTTPS; response bytes unmodified')
PARSER.add_argument('--only', help='Optional comma-separated recording numbers, e.g. 3,6')
ARGS = PARSER.parse_args()
OUT = ARGS.output.resolve()
for directory in ['screenshots/high_resolution_2x', 'recordings', 'evidence']:
    (OUT / directory).mkdir(parents=True, exist_ok=True)
CACHE = {}
MANIFEST = {'baseline': '6e9cc55b46a4cfa991b69da1df66e0567c55017c', 'source': ARGS.base_url,
            'capturedAtUTC': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'realPhone': False, 'screenshots': [], 'recordings': [], 'checks': []}


def verified_transport(route):
    url = route.request.url
    parsed = urlsplit(url)
    assert parsed.scheme == 'https' and parsed.hostname == 'lixinisydney-cloud.github.io'
    assert route.request.method in ('GET', 'HEAD')
    if url not in CACHE:
        try:
            response = urllib.request.urlopen(url, timeout=40)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            headers = {k: v for k, v in response.headers.items()
                       if k.lower() not in ('content-length', 'transfer-encoding', 'content-encoding')}
            body = response.read()
            CACHE[url] = response.status, headers, body
            if ARGS.repo and response.status == 200 and parsed.path.startswith('/ux/'):
                local = ARGS.repo / unquote(parsed.path[4:] or 'index.html')
                if local.is_file():
                    assert local.read_bytes() == body, 'Published resource differs: ' + parsed.path
    status, headers, body = CACHE[url]
    route.fulfill(status=status, headers=headers, body=body)


class Session:
    def __init__(self, browser, recording=None, desktop=False):
        self.events = []
        self.started = time.monotonic()
        self.desktop = desktop
        opts = dict(viewport={'width': 1440 if desktop else 390, 'height': 900 if desktop else 844},
                    device_scale_factor=1 if desktop else 2, is_mobile=not desktop,
                    has_touch=not desktop, reduced_motion='no-preference' if recording else 'reduce',
                    locale='zh-CN', timezone_id='Asia/Shanghai', color_scheme='dark')
        self.recording = recording
        if recording:
            opts.update(record_video_dir=str(OUT.parent / 'raw_recordings'),
                        record_video_size={'width': 1440 if desktop else 390, 'height': 900 if desktop else 844})
        self.context = browser.new_context(**opts)
        self.context.grant_permissions(['clipboard-read', 'clipboard-write'])
        if ARGS.verified_transport:
            self.context.route('https://lixinisydney-cloud.github.io/**', verified_transport)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('console', lambda msg: self.errors.append(msg.text) if msg.type == 'error' else None)
        self.cdp = self.context.new_cdp_session(self.page)
        self.video = self.page.video
        self.page.goto(ARGS.base_url, wait_until='networkidle')
        expect(self.page.locator('body')).to_have_attribute('data-version', '0.9.1')
        self.pause(1250)
        self.event('Open final v0.9.1 in fresh isolated context')

    def event(self, message, **data):
        self.events.append({'seconds': round(time.monotonic() - self.started, 2), 'action': message, **data})

    def pause(self, ms=1000):
        self.page.wait_for_timeout(ms)

    def action(self, action, id=None):
        if action == 'home':
            return self.page.locator('.pagehead [data-action="home"]')
        return self.page.locator('[data-action="' + action + '"]' + ('[data-id="' + id + '"]' if id else ''))

    def tap(self, action, id=None, pause=900):
        target = self.action(action, id)
        expect(target).to_be_visible()
        expect(target).to_be_enabled()
        target.scroll_into_view_if_needed()
        box = target.bounding_box()
        assert box
        x, y = box['x'] + box['width']/2, box['y'] + box['height']/2
        if self.desktop:
            self.page.mouse.click(x, y)
        else:
            self.page.touchscreen.tap(x, y)
        self.event('Tap ' + action, id=id)
        self.pause(pause)

    def ids(self, action='note'):
        return self.action(action).evaluate_all('(els)=>els.map(el=>el.dataset.id)')

    def state(self):
        return self.page.evaluate('JSON.parse(localStorage.getItem("refold-v05-experience-data")||"{}")')

    def swipe(self, x1, y1, x2, y2, duration=750):
        self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x1, 'y': y1}]})
        steps = max(16, int(duration / 35))
        for i in range(1, steps+1):
            t = i/steps
            # Slower ending reduces unintended inertial overshoot.
            t = 1 - (1-t)**1.5
            self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x1+(x2-x1)*t, 'y': y1+(y2-y1)*t}]})
            self.pause(duration/steps)
        self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        self.event('Real Chromium touch swipe', start=[x1, y1], end=[x2, y2])
        self.pause(1100)

    def group(self, id='design'):
        self.tap('group', id)
        expect(self.page.locator('.collection-count')).to_be_visible()

    def screenshot(self, name, primary=False):
        self.page.wait_for_function('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
        self.pause(150)
        path = OUT / 'screenshots/high_resolution_2x' / name
        self.page.screenshot(path=str(path))
        if primary:
            shutil.copy2(path, OUT / 'screenshots' / name)
        self.event('Actual DOM screenshot', file=name)
        MANIFEST['screenshots'].append({'file': 'screenshots/high_resolution_2x/'+name,
            'origin': 'new actual DOM capture', 'viewport': {'width': 1440 if self.desktop else 390, 'height': 900 if self.desktop else 844},
            'deviceScaleFactor': 1 if self.desktop else 2, 'page': self.page.locator('.phone').get_attribute('data-page'),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})

    def finish(self):
        self.page.wait_for_function('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
        overflow = self.page.evaluate('document.documentElement.scrollWidth > innerWidth')
        assert not overflow, 'Document horizontal overflow'
        assert not self.errors, self.errors
        self.event('End checks: no console/page errors; all current images loaded; no document overflow')
        self.pause(1300 if self.recording else 100)
        self.context.close()
        if self.recording:
            path = OUT / 'recordings' / (self.recording+'.webm')
            self.video.save_as(str(path))
            self.video.delete()
            MANIFEST['recordings'].append({'file': 'recordings/'+path.name, 'events': self.events,
                'viewport': '1440x900 desktop (actual demo control)' if self.desktop else '390x844 Chromium touch emulation',
                'realPhone': False, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        else:
            MANIFEST['checks'].append({'events': self.events})

    def long_press_reorder(self, screenshots=False):
        source = self.action('group', 'career')
        box = source.bounding_box()
        x, y = box['x']+box['width']/2, box['y']+55
        self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
        self.pause(720)
        expect(self.action('sort-done')).to_be_visible()
        self.event('Held touch 720ms; existing 450ms long-press entered sorting')
        if screenshots:
            self.screenshot('06_reorder_mode.png', primary=True)
        target = self.action('group', 'design').bounding_box()
        end_x, end_y = target['x']+target['width']/2, target['y']+55
        for step in range(1, 25):
            self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x+(end_x-x)*step/24, 'y': y+(end_y-y)*step/24}]})
            self.pause(38)
        self.pause(250)
        self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        self.pause(1100)
        self.event('Dragged career card before design with same held touch')
        self.tap('sort-done')
        assert self.state()['order'][0] == 'career', self.state().get('order')
        if screenshots:
            self.screenshot('07_reorder_result.png', primary=True)


def screenshots(browser):
    reused = {'01_home.png': 'home_top_390.png', '03_ai_collection.png': 'collection_390.png',
              '04_note_detail.png': 'note_detail_390.png', '05_home_menu.png': 'home_menu_390.png',
              '08_batch_manage.png': 'manage_390.png', '10_share_sheet.png': 'share_390.png',
              '11_invite_friends.png': 'friends_390.png', '12_shared_state.png': 'shared_state_390.png',
              '14_desktop_demo.png': 'desktop_1440.png'}
    if ARGS.repo:
        for target, source in reused.items():
            original = ARGS.repo/'screenshots/v091'/source
            shutil.copy2(original, OUT/'screenshots'/target)
            MANIFEST['screenshots'].append({'file': 'screenshots/'+target, 'origin': 'unchanged final tracked screenshot: screenshots/v091/'+source,
                'sha256': hashlib.sha256(original.read_bytes()).hexdigest(), 'deviceScaleFactor': 1})
    s = Session(browser)
    s.screenshot('01_home.png', primary=not ARGS.repo)
    rail = s.page.locator('#smartShelf').bounding_box()
    y = rail['y']+50
    s.swipe(323, y, 191, y, 650)
    assert s.page.locator('#smartShelf').evaluate('el=>el.scrollLeft') > 30
    s.screenshot('02_horizontal_scroll.png', primary=True)
    s.finish()
    s = Session(browser)
    s.tap('settings')
    s.screenshot('05_home_menu.png', primary=not ARGS.repo)
    s.finish()
    s = Session(browser)
    s.long_press_reorder(screenshots=True)
    s.finish()
    s = Session(browser)
    s.group()
    s.screenshot('03_ai_collection.png', primary=not ARGS.repo)
    s.tap('note', 'd1')
    s.screenshot('04_note_detail.png', primary=not ARGS.repo)
    s.swipe(200, 660, 200, 290, 800)
    s.screenshot('04_note_body_and_tags.png', primary=True)
    s.finish()
    s = Session(browser)
    s.group()
    before = s.ids()
    s.tap('manage')
    s.tap('manage-start')
    s.tap('select-note', 'd1')
    s.screenshot('08_batch_manage.png', primary=not ARGS.repo)
    s.tap('batch-remove', pause=550)
    assert 'd1' not in s.ids()
    assert 'd1' in s.state()['exclude']['design']
    assert 'd1' not in s.state().get('removed', [])
    s.event('Virtual correction verified', beforeCount=len(before), afterCount=len(s.ids()), originalSaved=True)
    s.screenshot('09_correction_result.png', primary=True)
    s.tap('home')
    s.tap('album', '视觉设计灵感')
    assert 'd1' in s.ids()
    s.screenshot('09_original_album_retained.png', primary=True)
    s.finish()
    s = Session(browser)
    s.group()
    s.tap('share')
    s.screenshot('10_share_sheet.png', primary=not ARGS.repo)
    s.finish()
    s = Session(browser)
    s.group()
    s.tap('share-invite')
    s.tap('friends-toggle')
    s.tap('friend-toggle', 'lin')
    s.tap('friend-toggle', 'qiao')
    s.screenshot('11_invite_friends.png', primary=not ARGS.repo)
    s.tap('friends-done', pause=550)
    assert s.page.locator('.member-avatars img').count() == 2
    assert s.state()['groupSharing']['design']['enabled'] is True
    s.screenshot('12_shared_state.png', primary=not ARGS.repo)
    s.finish()
    s = Session(browser)
    s.group('home')
    initial = len(s.ids())
    s.screenshot('13_before_new_save.png', primary=True)
    s.tap('home')
    s.page.set_viewport_size({'width': 1440, 'height': 900})
    s.desktop = True
    s.page.locator('#simulateDemo').click()
    s.pause(800)
    s.tap('save-note', 'new1')
    s.page.set_viewport_size({'width': 390, 'height': 844})
    s.desktop = False
    s.pause(700)
    s.group('home')
    assert len(s.ids()) == initial+1 and 'new1' in s.ids()
    s.event('Preset new save verified', beforeCount=initial, afterCount=len(s.ids()), control='desktop Demo only')
    s.screenshot('13_new_save_update.png', primary=True)
    s.finish()
    s = Session(browser, desktop=True)
    s.screenshot('14_desktop_demo.png', primary=not ARGS.repo)
    s.finish()


def record(browser, number):
    names = {1:'Clip_01_home_horizontal',2:'Clip_02_collection_note_return',3:'Clip_03_longpress_reorder',
             4:'Clip_04_correction_undo',5:'Clip_05_new_save_desktop',6:'Clip_06_share_copy_link',7:'Clip_07_invite_friends'}
    s = Session(browser, recording=names[number], desktop=number == 5)
    if number == 1:
        rail = s.page.locator('#smartShelf').bounding_box()
        y = rail['y']+50
        s.swipe(330, y, 70, y, 950)
        assert s.page.locator('#smartShelf').evaluate('el=>el.scrollLeft') > 80
        s.pause(1500)
        s.swipe(70, y, 330, y, 950)
        assert s.action('sort-done').count() == 0
    elif number == 2:
        s.group()
        s.pause(1300)
        s.swipe(210, 690, 210, 335, 1000)
        top = s.page.locator('#appScreen').evaluate('el=>el.scrollTop')
        visible = s.action('note').evaluate_all('(els)=>els.filter(el=>{const r=el.getBoundingClientRect();return r.top>120&&r.bottom<760}).map(el=>el.dataset.id)')
        assert visible
        s.tap('note', visible[0])
        s.pause(1600)
        s.swipe(210, 670, 210, 310, 1000)
        s.pause(1400)
        # Sticky header: tap at its actual displayed position, without locator auto-scrolling.
        b=s.action('note-back').bounding_box()
        s.page.touchscreen.tap(b['x']+b['width']/2, b['y']+b['height']/2)
        s.pause(1400)
        after=s.page.locator('#appScreen').evaluate('el=>el.scrollTop')
        assert abs(after-top)<3, (top, after)
        s.event('Return restored collection scroll', before=top, after=after)
    elif number == 3:
        s.group()
        s.pause(650)
        s.tap('home')
        s.long_press_reorder()
        s.pause(1800)
    elif number == 4:
        s.group()
        initial=len(s.ids())
        s.tap('manage')
        s.tap('manage-start')
        s.pause(1000)
        s.tap('select-note','d1')
        s.pause(850)
        s.tap('batch-remove',pause=1500)
        assert 'd1' not in s.ids() and len(s.ids())==initial-1
        assert 'd1' not in s.state().get('removed',[])
        s.event('Removed virtual association; original saved note retained')
        s.tap('undo',pause=1600)
        assert 'd1' in s.ids() and len(s.ids())==initial
        s.event('Undo restored original collection membership')
    elif number == 5:
        s.page.locator('#simulateDemo').click()
        s.event('Open existing desktop Demo new-save control')
        s.pause(2000)
        s.tap('save-note','new1',pause=1900)
        assert 'new1' in s.state()['savedNew']
        s.group('home')
        assert 'new1' in s.ids()
        s.pause(1800)
    elif number == 6:
        s.group()
        expected=set(s.ids())
        s.tap('share')
        s.pause(2400)
        s.tap('share-channel','copy',pause=1300)
        s.page.wait_for_function('document.querySelector(".phone").dataset.copyStatus==="copied"')
        link=s.page.evaluate('navigator.clipboard.readText()')
        encoded=urlsplit(link).fragment.removeprefix('share=')
        data=json.loads(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)))
        assert set(data['noteIds'])==expected
        assert urlsplit(link).hostname==urlsplit(ARGS.base_url).hostname
        s.event('Actual clipboard read verified static snapshot IDs', noteCount=len(expected), url=link)
        MANIFEST['copiedDemoLink']=link
        s.pause(1800)
    elif number == 7:
        s.group()
        s.tap('share-invite')
        s.pause(1300)
        s.tap('friends-toggle')
        s.tap('friend-toggle','lin')
        s.tap('friend-toggle','qiao')
        s.pause(1700)
        s.tap('friends-done',pause=1700)
        copy=s.state()['copies'][-1]
        assert set(copy['friends'])=={'lin','qiao'}
        expect(s.page.locator('.phone')).to_have_attribute('data-page','group')
        assert s.action('share-confirm').count()==0
        s.event('Saved local simulated friends and returned directly; no messages sent', friendIds=copy['friends'], snapshotCount=len(copy['noteIds']))
    s.finish()
    print('Recorded', names[number], flush=True)


if __name__ == '__main__':
    try:
        with sync_playwright() as playwright:
            launch = dict(headless=True, args=['--no-sandbox'])
            if ARGS.chromium:
                launch['executable_path']=ARGS.chromium
            browser=playwright.chromium.launch(**launch)
            if ARGS.mode in ('screenshots','all'):
                screenshots(browser)
            if ARGS.mode in ('recordings','all'):
                selected=set(map(int,ARGS.only.split(','))) if ARGS.only else set(range(1,8))
                for number in sorted(selected):
                    record(browser,number)
            if MANIFEST.get('copiedDemoLink'):
                s=Session(browser)
                s.page.goto(MANIFEST['copiedDemoLink'],wait_until='networkidle')
                assert len(s.ids('shared-note'))==11
                s.event('Copied public demo link opened successfully in a separate fresh context')
                s.finish()
            browser.close()
        print('All requested captures completed.',flush=True)
    finally:
        MANIFEST['verifiedResources']=[{'url': url, 'status': item[0], 'sha256': hashlib.sha256(item[2]).hexdigest()}
                                       for url,item in CACHE.items()]
        (OUT/'evidence'/('capture_manifest_'+ARGS.mode+('_'+ARGS.only.replace(',','_') if ARGS.only else '')+'.json')).write_text(
            json.dumps(MANIFEST,ensure_ascii=False,indent=2),encoding='utf-8')
