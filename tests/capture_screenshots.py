"""Capture actual mobile screenshots using fresh, isolated browser state."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--base-url', default='http://127.0.0.1:4173')
parser.add_argument('--chromium', default='/usr/bin/chromium')
args = parser.parse_args()
output = Path(__file__).resolve().parents[1] / 'screenshots'
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
        capture('correction')
        page.locator('[data-action="exclude"]').click()
        capture('undo')
        page.locator('[data-action="undo"]').click()
        page.locator('.pagehead [data-action="home"]').click()
        page.locator('[data-action="create"]').click()
        page.locator('#albumTitle').fill('设计灵感')
        page.locator('.pagehead strong').click()
        capture('create')
        context.close()
        print(f'{width} × 844: six screenshots saved')
    page = browser.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    page.goto(args.base_url, wait_until='networkidle')
    desktop = page.screenshot(path=str(output / 'desktop_1440.png'))
    (output / 'desktop.png').write_bytes(desktop)
    browser.close()
