"""Capture actual mobile screenshots using fresh, isolated browser state."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--base-url', default='http://127.0.0.1:4173')
parser.add_argument('--chromium', default='/usr/bin/chromium')
parser.add_argument('--output-dir', type=Path, help='Directory for this run (default: screenshots)')
args = parser.parse_args()
output = args.output_dir or Path(__file__).resolve().parents[1] / 'screenshots'
output.mkdir(exist_ok=True)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path=args.chromium, headless=True, args=['--no-sandbox'])
    for width in (390, 375, 430):
        context = browser.new_context(
            viewport={'width': width, 'height': 844}, device_scale_factor=1,
            is_mobile=True, has_touch=True, reduced_motion='reduce')
        page = context.new_page()
        page.goto(args.base_url, wait_until='networkidle')

        def capture(name):
            page.wait_for_function('Array.from(document.images).every(i => i.complete && i.naturalWidth)')
            page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
            page.screenshot(path=str(output / f'{name}_{width}.png'), animations='disabled')

        capture('home_top')
        page.locator('#appScreen').evaluate(
            '(el) => el.scrollTop = document.querySelector(".primary-tabs").offsetTop - el.offsetTop')
        capture('home')
        page.locator('[data-action="group"][data-id="design"]').click()
        capture('collection')
        page.locator('[data-action="note"][data-id="d1"]').click()
        capture('note_detail')
        page.locator('[data-action="note-menu"]').click()
        capture('correction')
        page.locator('[data-action="note-exclude"]').click()
        page.locator('[data-action="note-back"]').click()
        capture('undo')
        page.locator('[data-action="undo"]').click()
        page.locator('[data-action="manage"]').click()
        page.locator('[data-action="select-note"][data-id="d1"]').click()
        capture('manage')
        page.locator('[data-action="manage-exit"]').click()
        page.locator('[data-action="add-notes"]').click()
        capture('picker')
        page.locator('[data-action="picker-close"]').click()
        page.locator('[data-action="share"]').click()
        capture('share')
        page.locator('.sheet [data-action="share-invite"]').click()
        page.locator('[data-action="share-select"][data-id="d1"]').click()
        capture('share_selection')
        page.locator('[data-action="share-confirm"]').click()
        page.locator('[data-action="friend-toggle"][data-id="lin"]').click()
        capture('friends')
        page.locator('[data-action="friend-confirm"]').click()
        page.locator('[data-action="close"]').click()
        page.locator('.pagehead [data-action="home"]').click()
        page.locator('[data-action="create"]').click()
        page.locator('#albumTitle').fill('设计灵感')
        page.locator('.pagehead strong').click()
        capture('create')
        context.close()
        print(f'{width} × 844: twelve screenshots saved')
    page = browser.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    page.goto(args.base_url, wait_until='networkidle')
    desktop = page.screenshot(path=str(output / 'desktop_1440.png'))
    (output / 'desktop.png').write_bytes(desktop)
    browser.close()
