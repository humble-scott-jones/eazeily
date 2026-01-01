from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:5001/quality-builder'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL)
    page.wait_for_timeout(1500)

    def inner_text(sel):
        try:
            return page.locator(sel).inner_text()
        except Exception as e:
            return f'ERR: {e}'

    print('initial preview:', inner_text('#preview-good'))

    # click industry
    page.click('.industry-btn[data-industry="retail"]')
    print('after industry click preview:', inner_text('#preview-good'))

    # fill business name
    page.fill('#qb-business-name', 'My Test Shop')
    page.wait_for_timeout(200)
    print('after name preview:', inner_text('#preview-good'))

    # click platform
    page.click('.platform-btn[data-platform="instagram"]')
    page.wait_for_timeout(200)
    print('after platform preview:', inner_text('#preview-good'))

    # add service
    page.fill('#qb-services-input', 'Custom Widgets')
    page.press('#qb-services-input', 'Enter')
    page.wait_for_timeout(300)
    print('after service preview:', inner_text('#preview-good'))

    # add audience
    page.fill('#qb-audience-input', 'entrepreneurs')
    page.press('#qb-audience-input', 'Enter')
    page.wait_for_timeout(300)
    print('after audience preview:', inner_text('#preview-good'))

    # add pain
    page.fill('#qb-pain-input', 'wasting money')
    page.press('#qb-pain-input', 'Enter')
    page.wait_for_timeout(300)
    print('after pain preview:', inner_text('#preview-good'))

    # add outcome
    page.fill('#qb-outcome-input', 'save budget')
    page.press('#qb-outcome-input', 'Enter')
    page.wait_for_timeout(300)
    print('after outcome preview:', inner_text('#preview-good'))

    # click cta
    page.click('.cta-intent-btn[data-value="call"]')
    page.wait_for_timeout(300)
    print('after cta preview:', inner_text('#preview-good'))

    # dump quality data by evaluating in page
    try:
        qd = page.evaluate('() => JSON.stringify(window.qualityData)')
        print('qualityData:', qd)
    except Exception as e:
        print('error reading qualityData:', e)

    browser.close()
