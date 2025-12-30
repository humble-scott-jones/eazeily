from playwright.sync_api import sync_playwright
import time

BASE = 'http://127.0.0.1:5001'

console_messages = []
network_events = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    def on_console(msg):
        console_messages.append((msg.type, msg.text))
        print(f"CONSOLE [{msg.type}] {msg.text}")

    def on_request(req):
        network_events.append(("req", req.method, req.url))
        print(f"REQ  {req.method} {req.url}")

    def on_response(resp):
        try:
            status = resp.status
        except Exception:
            status = 'ERR'
        network_events.append(("resp", status, resp.url))
        print(f"RESP {status} {resp.url}")

    page.on("console", on_console)
    page.on("request", on_request)
    page.on("response", on_response)

    print('Navigating to /app')
    page.goto(f"{BASE}/app", wait_until='networkidle')
    time.sleep(0.5)

    try:
        print('Waiting for #industri es selector...')
        page.wait_for_selector('#industries', timeout=5000)
        print('industries visible')
    except Exception as e:
        print('industries not visible:', e)

    # Inspect #industries element and its ancestors for display/hidden classes
    def inspect_visibility_chain(selector):
        el = page.query_selector(selector)
        if not el:
            print(f'{selector}: NOT FOUND')
            return
        outer = page.evaluate("sel => document.querySelector(sel).outerHTML", selector)
        style = page.evaluate("sel => window.getComputedStyle(document.querySelector(sel)).cssText", selector)
        print(f"{selector} outerHTML (truncated): {outer[:1000]}")
        print(f"{selector} computed style: {style}")
        # walk up parents
        parents = page.evaluate("sel => { let el=document.querySelector(sel); let out=[]; while(el){ out.push({tag: el.tagName, classes: el.className}); el = el.parentElement;} return out; }", selector)
        print(f"{selector} ancestor chain (tag/classes):")
        for p in parents[:10]:
            print('  ', p)

    inspect_visibility_chain('#industries')

    def detailed_check(selector):
        exists = page.query_selector(selector) is not None
        info = page.evaluate(r"""
            sel => {
                const el = document.querySelector(sel);
                if (!el) return {exists:false};
                const cs = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                // find any ancestor with 'hidden' class
                let anc = el;
                let hiddenAncestor = null;
                while(anc){
                    if (anc.classList && anc.classList.contains('hidden')){ hiddenAncestor = anc.tagName + ' ' + (anc.className||''); break; }
                    anc = anc.parentElement;
                }
                return {
                    exists: true,
                    display: cs.display,
                    visibility: cs.visibility,
                    opacity: cs.opacity,
                    width: rect.width,
                    height: rect.height,
                    offsetWidth: el.offsetWidth,
                    offsetHeight: el.offsetHeight,
                    hiddenAncestor: hiddenAncestor,
                    className: el.className,
                    inlineStyle: el.getAttribute('style')
                };
            }
        """, selector)
        print(f"detailed {selector}: {info}")

    detailed_check('#industries')
    detailed_check('#next')
    detailed_check('[data-industry="retail"]')
    dims = page.evaluate('() => ({innerWidth: window.innerWidth, innerHeight: window.innerHeight, docClientWidth: document.documentElement.clientWidth, bodyClientWidth: document.body.clientWidth})')
    print('viewport/dimensions:', dims)

    # Click retail industry
    try:
        print('Clicking retail industry')
        page.click('[data-industry="retail"]')
        # after selecting, inspect the next button state
        try:
            print('--- #next detailed state after selection ---')
            detailed_check('#next')
        except Exception:
            pass
        page.click('#next')
    except Exception as e:
        print('click industry failed:', e)

    # Wait for brand kit form
    try:
        print('Waiting for #brand-kit-form')
        page.wait_for_selector('#brand-kit-form', timeout=5000)
        print('brand-kit-form visible')
    except Exception as e:
        print('brand-kit-form not visible:', e)

    # Inspect example comparison
    def show_element_state(selector):
        el = page.query_selector(selector)
        if not el:
            print(f'{selector}: NOT FOUND')
            return
        visible = el.is_visible()
        outer = el.inner_html()[:1000]
        style = page.evaluate("selector => window.getComputedStyle(document.querySelector(selector)).cssText", selector)
        print(f'{selector}: visible={visible} style={style}')
        print(f'{selector} inner_html (truncated): {outer}')

    show_element_state('#example-comparison')

    # Click toggle
    try:
        print('Clicking #show-example-toggle')
        page.click('#show-example-toggle')
        time.sleep(0.3)
    except Exception as e:
        print('click toggle failed:', e)

    show_element_state('#example-comparison')

    # Dump a few helpful selectors
    for sel in ['#bk-audience', '#bk-services-input', '#bk-audience', '#example-comparison']:
        try:
            el = page.query_selector(sel)
            if el:
                print(f'--- {sel} exists; visible={el.is_visible()} ---')
                print(el.inner_html()[:500])
            else:
                print(f'--- {sel} MISSING ---')
        except Exception as e:
            print(f'error querying {sel}:', e)

    print('\nCollected console messages:')
    for t, m in console_messages:
        print(t, m)

    print('\nCollected network events (last 40):')
    for ev in network_events[-40:]:
        print(ev)

    browser.close()
