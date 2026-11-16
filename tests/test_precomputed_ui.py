"""Browser checks against the shipped Codex data; no mocked classifications or API."""
import argparse
import copy
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--base-url', default='http://127.0.0.1:4173')
parser.add_argument('--chromium', default='/usr/bin/chromium')
OPTIONS, ARGS = parser.parse_known_args()
ROOT = Path(__file__).resolve().parents[1]


class PrecomputedUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((ROOT / 'data/classifications.precomputed.json').read_text())
        cls.notes = json.loads((ROOT / 'data/notes.json').read_text())
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            executable_path=OPTIONS.chromium, headless=True, args=['--no-sandbox'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
        self.page = self.context.new_page()
        self.errors = []
        self.external = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('console', lambda m: self.errors.append(m.text) if m.type == 'error' else None)
        self.page.on('response', lambda r: self.errors.append(f'HTTP {r.status}: {r.url}') if r.status >= 400 else None)
        self.page.on('request', lambda r: self.external.append(r.url) if urlsplit(r.url).scheme in ('http', 'https') and urlsplit(r.url).netloc != urlsplit(OPTIONS.base_url).netloc else None)

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.external, [], 'No external service calls')

    def goto(self, suffix=''):
        self.page.goto(OPTIONS.base_url.rstrip('/') + '/' + suffix, wait_until='networkidle')
        expect(self.page.locator('.footer-mock')).to_have_attribute('data-classification-mode', 'precomputed')
        expect(self.page.locator('.footer-mock')).to_contain_text('Codex AI 语义预分类')

    def action(self, action, item=None):
        selector = f'[data-action="{action}"]'
        if item is not None:
            selector += f'[data-id="{item}"]'
        return self.page.locator(selector)

    def home(self):
        self.page.locator('.pagehead [data-action="home"]').click()

    def ids(self):
        return self.action('note').evaluate_all('els=>els.map(el=>el.dataset.id)')

    def test_01_all_group_memberships_and_reasons_use_shipped_result(self):
        self.goto()
        initial = {n['id'] for n in self.notes if n['availability'] == 'initial'}
        for group in ('design', 'career', 'travel', 'food', 'home', 'life'):
            self.action('group', group).click()
            expected = {r['noteId'] for r in self.result['assignments'] if r['noteId'] in initial and any(m['groupId'] == group for m in r['memberships'])}
            self.assertEqual(set(self.ids()), expected)
            for row in self.result['assignments']:
                for membership in row['memberships']:
                    if row['noteId'] in initial and membership['groupId'] == group:
                        self.action('note', row['noteId']).click()
                        self.action('note-menu').click()
                        self.page.locator('details.classification summary').click()
                        expect(self.page.locator('details.classification p')).to_have_text(membership['reason'])
                        self.action('close').click()
                        self.action('note-back').click()
            self.home()

    def test_02_correction_undo_reload_original_and_three_new_saves(self):
        self.goto()
        self.action('group', 'design').click()
        self.action('note', 'd1').click()
        self.action('note-menu').click()
        self.action('note-exclude').click()
        self.action('note-back').click()
        self.assertNotIn('d1', self.ids())
        self.action('undo').click()
        self.assertIn('d1', self.ids())
        self.action('note', 'd1').click()
        self.action('note-menu').click()
        self.action('note-exclude').click()
        self.action('note-back').click()
        self.page.reload(wait_until='networkidle')
        self.action('group', 'design').click()
        self.assertNotIn('d1', self.ids())
        self.home()
        self.action('album', '视觉设计灵感').click()
        self.assertIn('d1', self.ids())
        self.home()
        for note, group in (('new1', 'home'), ('new2', 'design'), ('new3', 'travel')):
            self.action('settings').click()
            self.action('simulate').click()
            self.action('save-note', note).click()
            self.action('group', group).click()
            self.assertIn(note, self.ids())
            self.home()
        self.page.reload(wait_until='networkidle')
        for note, group in (('new1', 'home'), ('new2', 'design'), ('new3', 'travel')):
            self.action('group', group).click()
            self.assertIn(note, self.ids())
            self.home()

    def test_03_desktop_and_offline_export(self):
        self.page.set_viewport_size({'width': 1440, 'height': 900})
        self.goto()
        self.assertEqual(self.page.locator('#appScreen').evaluate('e=>e.clientWidth'), 390)
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 1440)
        self.page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
        self.assertTrue(self.page.evaluate('Array.from(document.images).every(i=>i.naturalWidth>0)'))
        self.goto('RE_FOLD_v06_Demo.html')
        self.action('group', 'design').click()
        self.assertIn('case-a', self.ids())
        self.assertIn('case-b', self.ids())

    def test_04_stale_precomputed_data_falls_back_and_never_impersonates_api(self):
        self.goto()
        bundle = self.page.evaluate('RE_BOOTSTRAP')
        for mutation in ('datasetHash', 'provider', 'missing_note'):
            invalid = copy.deepcopy(bundle)
            if mutation == 'missing_note':
                invalid['precomputed']['assignments'].pop()
            else:
                invalid['precomputed'][mutation] = 'openai' if mutation == 'provider' else '0' * 64
            mode = self.page.evaluate('''async bundle => {
                const store = await REClassification.createStore(bundle, {
                    storage: {getItem:()=>null,setItem:()=>{},removeItem:()=>{}},
                    fetcher: async()=>({ok:true,json:async()=>({mode:'unavailable'})})
                });
                await store.refresh(); return store.mode;
            }''', invalid)
            self.assertEqual(mode, 'offline')


if __name__ == '__main__':
    unittest.main(argv=[__file__, *ARGS], verbosity=2)
