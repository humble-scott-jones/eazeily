from playwright.sync_api import sync_playwright
import time

BASE = 'http://127.0.0.1:5001'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    page.on('console', lambda msg: print('CONSOLE>>', msg.type, msg.text))

    page.goto(f"{BASE}/app", wait_until='networkidle')
    page.wait_for_selector('#industries', timeout=5000)
    page.click('[data-industry="retail"]')
    page.click('#next')
    page.wait_for_selector('#brand-kit-form', timeout=5000)

    # Attach debug wrapper
    page.evaluate("""
        () => {
            const btn = document.getElementById('show-example-toggle');
            if (btn) {
                btn.addEventListener('click', () => console.log('WRAPPER: button clicked'));
                console.log('WRAPPER: attached');
            } else {
                console.log('WRAPPER: button missing');
            }
        }
    """)

    # Now click
    print('Clicking toggle')
    page.click('#show-example-toggle')
    time.sleep(0.5)

    browser.close()
