"""Optional real browser QA. Install playwright; uses installed Edge, isolated profile."""
import argparse
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:18081")
args = parser.parse_args()
output = Path("artifacts")
output.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 1050}, device_scale_factor=1)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(args.url, wait_until="networkidle")
    expect(page.locator("#sync-status")).to_contain_text("Synced")
    title = "Browser check " + str(uuid4())[:8] + " <script>window.xss=1</script>"
    page.locator("#title").fill(title)
    page.locator("#priority").select_option("high")
    page.get_by_role("button", name="Add task").click()
    card = page.locator(".task-card").filter(has=page.get_by_role("heading", name=title, exact=True))
    expect(card).to_be_visible()
    assert page.evaluate("window.xss") is None
    card.locator("select").select_option("in_progress")
    expect(page.locator("#in_progress-list").get_by_role("heading", name=title, exact=True)).to_be_visible()
    card.locator("select").select_option("done")
    expect(page.locator("#done-list").get_by_role("heading", name=title, exact=True)).to_be_visible()
    page.reload(wait_until="networkidle")
    expect(page.locator("#done-list").get_by_role("heading", name=title, exact=True)).to_be_visible()
    page.on("dialog", lambda dialog: dialog.accept())
    card.get_by_role("button", name="Delete " + title, exact=True).click()
    expect(page.get_by_role("heading", name=title, exact=True)).to_have_count(0)
    page.screenshot(path=str(output / "dashboard-desktop.png"), full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    page.screenshot(path=str(output / "dashboard-mobile.png"), full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile horizontal overflow"
    assert not errors, errors
    print("PASS: real browser create, status transitions, reload persistence, delete, XSS text handling, mobile layout; no page errors")
    browser.close()
