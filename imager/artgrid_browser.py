import random
import time
import webbrowser

from playwright.sync_api import sync_playwright

from imager.config import (
    ARTGRID_FIRST_RESULT_SELECTOR,
    ARTGRID_SEARCH_BASE,
    BROWSER_NAVIGATION_TIMEOUT_MS,
    BROWSER_OPEN_DELAY_MIN,
    BROWSER_OPEN_DELAY_MAX,
    BROWSER_SELECTOR_TIMEOUT_MS,
    CHROMIUM_CDP_URL,
)


def open_first_result(search_url: str) -> None:
    webbrowser.open(search_url)
    time.sleep(random.uniform(BROWSER_OPEN_DELAY_MIN, BROWSER_OPEN_DELAY_MAX))


def connect_chromium(cdp_url: str | None = None) -> tuple:
    url = cdp_url or CHROMIUM_CDP_URL
    playwright = sync_playwright().start()
    browser = playwright.chromium.connect_over_cdp(url)
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.pages[0] if context.pages else context.new_page()
    return playwright, browser, page


def open_nth_result_via_chromium(page, search_url: str, n: int) -> None:
    page.goto(search_url, timeout=BROWSER_NAVIGATION_TIMEOUT_MS)
    try:
        loc = page.locator(ARTGRID_FIRST_RESULT_SELECTOR).nth(n)
        loc.wait_for(state="attached", timeout=BROWSER_SELECTOR_TIMEOUT_MS)
        href = loc.get_attribute("href")
        if href and not href.startswith("http"):
            base = ARTGRID_SEARCH_BASE.rstrip("/")
            href = base + ("/" + href.lstrip("/"))
        if href:
            page.goto(href, timeout=BROWSER_NAVIGATION_TIMEOUT_MS)
    except Exception as e:
        print(f"[browser] Could not find result {n + 1}: {e}")
    time.sleep(random.uniform(BROWSER_OPEN_DELAY_MIN, BROWSER_OPEN_DELAY_MAX))


def open_first_result_via_chromium(page, search_url: str) -> None:
    print("[browser] Opening search URL")
    open_nth_result_via_chromium(page, search_url, 0)
