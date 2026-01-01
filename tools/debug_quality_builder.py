from playwright.sync_api import sync_playwright
import time

URL = 'http://127.0.0.1:5001/quality-builder'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    print('Navigating to', URL)
    page.goto(URL)
    # wait a bit for client JS to run
    page.wait_for_timeout(2000)
    # save screenshot
    screenshot_path = 'debug_qb_screenshot.png'
    page.screenshot(path=screenshot_path, full_page=True)
    print('Saved screenshot to', screenshot_path)
    # dump some selectors
    def safe_text(selector):
        try:
            return page.locator(selector).inner_text()
        except Exception as e:
            return f'ERROR: {e}'

    selectors = ['#qb-industries', '.industry-btn[data-industry="retail"]', '#qb-business-name', '#preview-good', '#quality-next-step', '#brand-kit-form']
    for sel in selectors:
        print('---', sel)
        try:
            el = page.query_selector(sel)
            if el is None:
                print('not found')
            else:
                box = el.bounding_box()
                print('bounding_box:', box)
                text = safe_text(sel)
                print('text:', text[:200])
        except Exception as e:
            print('error:', e)

    # save full page HTML
    html = page.content()
    with open('debug_qb_page.html', 'w') as f:
        f.write(html)
    print('Saved HTML to debug_qb_page.html')
    browser.close()
