from playwright.sync_api import sync_playwright
import time

BASE = 'http://127.0.0.1:5001'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    def on_console(msg):
        print('BROWSER-CONSOLE:', msg.type, msg.text)
    page.on('console', on_console)

    page.goto(f"{BASE}/app", wait_until='networkidle')
    page.wait_for_selector('#industries', timeout=5000)
    page.click('[data-industry="retail"]')
    page.click('#next')
    page.wait_for_selector('#brand-kit-form', timeout=5000)
    # Install a long-running MutationObserver to capture any DOM changes
    page.evaluate("""
        () => {
            window.__brandkit_mutation_log = window.__brandkit_mutation_log || [];
            try {
                const obs = new MutationObserver((mutations) => {
                    const now = Date.now();
                    mutations.forEach(m => {
                        try {
                            const record = {
                                ts: now,
                                type: m.type,
                                target: (m.target && (m.target.id || m.target.className || m.target.nodeName)) || null,
                                added: m.addedNodes && m.addedNodes.length ? Array.from(m.addedNodes).map(n => (n.id||n.className||n.nodeName)) : [],
                                removed: m.removedNodes && m.removedNodes.length ? Array.from(m.removedNodes).map(n => (n.id||n.className||n.nodeName)) : [],
                                attrName: m.attributeName || null,
                                bkAudienceValue: (document.getElementById('bk-audience') && document.getElementById('bk-audience').value) || ''
                            };
                            window.__brandkit_mutation_log.push(record);
                            console.log('BRANDKIT_MUTATION_OBS', record);
                        } catch (e) { /* ignore */ }
                    });
                });
                obs.observe(document.body, { childList: true, subtree: true, attributes: true, characterData: true });
                window.__brandkit_mutation_observer = obs;
            } catch(e) { console.log('BRANDKIT_MUTATION_OBS: failed to attach', String(e)); }
        }
    """)
    # Install a value-watcher on the bk-audience input to capture property writes
    page.evaluate("""
        () => {
            try {
                window.__brandkit_value_changes = window.__brandkit_value_changes || [];
                const el = document.getElementById('bk-audience');
                if (el) {
                    const origDesc = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value');
                    if (origDesc && origDesc.configurable) {
                        Object.defineProperty(el, 'value', {
                            configurable: true,
                            enumerable: true,
                            get() { return origDesc.get.call(this); },
                            set(v) {
                                try { window.__brandkit_value_changes.push({ ts: Date.now(), old: origDesc.get.call(this), new: v }); } catch(e){}
                                return origDesc.set.call(this, v);
                            }
                        });
                        console.log('BRANDKIT_VALUE_WATCHER: installed');
                    } else {
                        console.log('BRANDKIT_VALUE_WATCHER: could not install - descriptor missing');
                    }
                } else {
                    console.log('BRANDKIT_VALUE_WATCHER: bk-audience not found');
                }
            } catch(e) { console.log('BRANDKIT_VALUE_WATCHER: error', String(e)); }
        }
    """)
    # install a global recorder to capture bubbled click events
    page.evaluate("""
        () => {
            window.__click_log = [];
            document.addEventListener('click', function(e){
                try { window.__click_log.push({ tag: e.target.tagName, cls: e.target.className, outer: e.target.outerHTML.slice(0,200) }); } catch (err) { window.__click_log.push({err: String(err)}); }
            }, true);
        }
    """)

    # find first audience chip
    chip = page.query_selector('.chip-suggestion[data-target="bk-audience"]')
    if not chip:
        print('No chip found')
    else:
        info = page.eval_on_selector('.chip-suggestion[data-target="bk-audience"]', '(el) => ({ outer: el.outerHTML, rootNode: el.getRootNode() && (el.getRootNode().nodeName || el.getRootNode().constructor && el.getRootNode().constructor.name) })')
        print('Chip info:', info)
        print('Clicking chip:', chip.inner_text())
        chip.click()
        time.sleep(0.3)
        val = page.evaluate("() => document.getElementById('bk-audience').value")
        print('bk-audience value after click:', repr(val))
        clicks = page.evaluate('() => window.__click_log')
        print('captured click events:', clicks)
    muts = page.evaluate("() => (window.__brandkit_mutation_log || []).slice(0,50)")
    print('brandkit mutation log:', muts)
    val_changes = page.evaluate("() => (window.__brandkit_value_changes || []).slice(0,50)")
    print('brandkit value changes:', val_changes)

    browser.close()
