"""Capture current RE flows in fresh browser state; no network social action."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--base-url',default='http://127.0.0.1:4173')
parser.add_argument('--chromium',default='/usr/bin/chromium')
parser.add_argument('--output-dir',type=Path)
args=parser.parse_args()
output=args.output_dir or Path(__file__).resolve().parents[1]/'screenshots'
output.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
    for width in (390,375,430):
        context=browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True,reduced_motion='reduce')
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(args.base_url,wait_until='networkidle')
        def action(name,item=None):
            return page.locator(f'[data-action="{name}"]'+(f'[data-id="{item}"]' if item else ''))
        def capture(name):
            page.wait_for_function('Array.from(document.images).every(i=>i.complete&&i.naturalWidth)')
            page.screenshot(path=str(output/f'{name}_{width}.png'),animations='disabled')
        capture('home_top')
        page.locator('#smartShelf').scroll_into_view_if_needed()
        capture('home')
        action('settings').click()
        capture('home_menu')
        action('sort-start').click()
        capture('sort')
        action('sort-done').click()
        action('group','design').click()
        capture('collection')
        action('note','d1').click()
        capture('note_detail')
        action('note-back').click()
        action('manage').click()
        action('manage-start').click()
        action('select-note','d1').click()
        capture('manage')
        action('manage-exit').click()
        action('share').click()
        capture('share')
        action('close').click()
        action('share-invite').click()
        action('friends-toggle').click()
        action('friend-toggle','lin').click()
        capture('friends')
        action('friends-done').click()
        capture('shared_state')
        assert not errors,errors
        context.close()
        print(f'{width}x844: ten actual flow screenshots saved')
    page=browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce')
    page.goto(args.base_url,wait_until='networkidle')
    page.screenshot(path=str(output/'desktop_1440.png'))
    page.locator('#simulateDemo').click()
    page.screenshot(path=str(output/'desktop_demo_1440.png'))
    browser.close()
