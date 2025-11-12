from playwright.sync_api import sync_playwright

def test_playwright_hello():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://example.com')
        assert page.title() == 'Example Domain'
        browser.close()