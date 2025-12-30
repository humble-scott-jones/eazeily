from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:5001/app'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL)
    page.wait_for_timeout(1500)
    print('industries present (text):', page.locator('#industries').inner_text()[:200])
    first_html = page.evaluate("() => document.getElementById('industries')?.children[0]?.outerHTML || null")
    print('first industries child html ->', first_html)
    try:
        retail_html = page.eval_on_selector('[data-industry="retail"]', 'el => el.outerHTML')
    except Exception:
        retail_html = None
    print('retail button html ->', retail_html)
    # check whether early handler marker exists on the retail button
    try:
           # attempt to invoke attachEarlyIndustryHandlers from the page to force attachment
           invoked = page.evaluate("() => { try { if (typeof attachEarlyIndustryHandlers === 'function') { attachEarlyIndustryHandlers(); return true; } return false; } catch(e){ return 'err:'+e.toString(); } }")
           print('attachEarlyIndustryHandlers invoked ->', invoked)
           has_marker = page.eval_on_selector('[data-industry="retail"]', 'el => el.dataset._handler_attached || null')
    except Exception:
        has_marker = None
    print('retail._handler_attached before click ->', has_marker)
    page.click('[data-industry="retail"]')
    page.wait_for_timeout(200)
    # inspect answers from window (if available)
    try:
        ans = page.evaluate('() => JSON.stringify(window.answers || null)')
        print('answers after click:', ans)
    except Exception as e:
        print('error reading answers:', e)
    try:
        has_marker_after = page.eval_on_selector('[data-industry="retail"]', 'el => el.dataset._handler_attached || null')
    except Exception:
        has_marker_after = None
    print('retail._handler_attached after click ->', has_marker_after)
    # click next
    # Dispatch a click event directly and capture any synchronous errors
    try:
        dispatch_res = page.evaluate("() => { try { document.getElementById('next').dispatchEvent(new MouseEvent('click', { bubbles: true })); return 'dispatched'; } catch (e) { return 'err:'+e.toString(); } }")
    except Exception as e:
        dispatch_res = f'exception:{e}'
    print('dispatch next result ->', dispatch_res)
    page.wait_for_timeout(200)
    # Try invoking showStep(2) directly to see if it reveals the panel
    try:
        invoked_show = page.evaluate("() => { try { if (typeof showStep === 'function') { showStep(2); return 'ok'; } return 'no-showStep'; } catch(e) { return 'err:'+e.toString(); } }")
    except Exception:
        invoked_show = None
    print('invoked showStep(2) ->', invoked_show)
    # check if step advanced by checking visibility of brand-kit-form
    # inspect computed style and bounding box for #brand-kit-form
    try:
        cs = page.evaluate("() => { const el = document.getElementById('brand-kit-form'); if (!el) return null; const s = getComputedStyle(el); const rect = el.getBoundingClientRect(); const parent = el.closest('.step-panel'); const pRect = parent ? parent.getBoundingClientRect() : null; const pStyle = parent ? getComputedStyle(parent) : null; return { display: s.display, visibility: s.visibility, opacity: s.opacity, width: rect.width, height: rect.height, parent: { display: pStyle ? pStyle.display : null, visibility: pStyle ? pStyle.visibility : null, width: pRect ? pRect.width : null, height: pRect ? pRect.height : null } }; }")
    except Exception:
        cs = None
    print('brand-kit-form computed ->', cs)
    browser.close()
