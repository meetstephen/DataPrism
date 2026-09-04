"""Real Chromium regression for the common sidebar frame (run separately)."""
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


def main():
    artifacts = Path("navigation-artifacts")
    artifacts.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONUTF8="1")
    with (artifacts / "server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port=8501",
             "--server.headless=true", "--browser.gatherUsageStats=false"],
            stdout=log, stderr=subprocess.STDOUT, env=env,
        )
        try:
            for _ in range(90):
                try:
                    with urlopen("http://localhost:8501/_stcore/health", timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(1)
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": 1365, "height": 768})
                page.goto("http://localhost:8501")
                nav = page.locator('[data-testid="stSidebarNav"]')
                nav.get_by_role("link", name="Report Generator", exact=True).wait_for()
                assert nav.get_by_role("link").count() >= 16
                assert page.get_by_label("Navigate to", exact=True).count() == 0
                sidebar = page.locator('[data-testid="stSidebarContent"]')
                handle = sidebar.element_handle()
                for target in ["Report Generator", "Data Dictionary", "Report Generator"]:
                    link = nav.get_by_role("link", name=target, exact=True)
                    link.scroll_into_view_if_needed()
                    before = sidebar.evaluate("el => el.scrollTop")
                    link.click()
                    page.wait_for_function("name => Array.from(document.querySelectorAll('[data-testid=stSidebarNav] a')).some(a => a.textContent.includes(name) && a.getAttribute('aria-current') === 'page')", arg=target)
                    page.wait_for_timeout(1200)
                    assert handle.evaluate("el => el.isConnected"), "Sidebar was remounted"
                    after = sidebar.evaluate("el => el.scrollTop")
                    assert abs(after - before) <= 3, (target, before, after)
                    assert page.locator('[data-testid="stException"]').count() == 0
                page.screenshot(path=str(artifacts / "desktop.png"), full_page=True)
                page.reload()
                nav.get_by_role("link", name="Report Generator", exact=True).wait_for()
                page.wait_for_function("() => document.querySelector('[data-testid=stSidebarNav] a[aria-current=page]')?.textContent.includes('Report Generator')")
                page.screenshot(path=str(artifacts / "direct-refresh.png"), full_page=True)
                browser.close()
                print("PASS: menu visible, active route correct, sidebar retained, scroll offset stable, direct refresh valid")
        finally:
            server.terminate()
            server.wait(timeout=15)


if __name__ == "__main__":
    main()
