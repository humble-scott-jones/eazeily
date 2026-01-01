from playwright.sync_api import sync_playwright
import time

BASE = 'http://127.0.0.1:5001'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_context().new_page()
    page.goto(f"{BASE}/app", wait_until='networkidle')
    page.wait_for_selector('#industries', timeout=5000)
    page.click('[data-industry="retail"]')
    page.click('#next')
    page.wait_for_selector('#brand-kit-form', timeout=5000)

    def detailed_check(selector, label):
        el = page.query_selector(selector)
        if not el:
            print(f"{label}: NOT FOUND")
            return
        info = page.evaluate(r"""
            sel => {
                const el = document.querySelector(sel);
                if (!el) return {exists:false};
                const cs = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return {
                    exists: true,
                    display: cs.display,
                    visibility: cs.visibility,
                    opacity: cs.opacity,
                    width: rect.width,
                    height: rect.height,
                    offsetWidth: el.offsetWidth,
                    offsetHeight: el.offsetHeight,
                    className: el.className,
                    inlineStyle: el.getAttribute('style'),
                    hiddenAttr: el.hasAttribute('hidden'),
                    ariaHidden: el.getAttribute('aria-hidden')
                };
            }
        """, selector)
        print(f"{label}: {info}")

    detailed_check('#example-comparison', 'before toggle')
    print('Clicking toggle')
    page.click('#show-example-toggle')
    time.sleep(0.3)
    detailed_check('#example-comparison', 'after toggle')

    browser.close()
