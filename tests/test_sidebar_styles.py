"""Navigation styles must not change geometry when the active page changes."""
from utils.styles import THEMES, _build_css


def test_scrollable_navigation_is_visible():
    css = _build_css(THEMES["Enterprise Dark"])
    assert '[data-testid="stSidebarNav"] a' in css
    assert "max-height: none !important" in css
    assert 'a[aria-current="page"]' in css
    assert "display: none !important" not in css
    assert "_dp_nav_destination" not in css


def test_sidebar_ancestors_have_no_forced_viewport_dimensions():
    css = _build_css(THEMES["Enterprise Dark"])
    assert "100dvh" not in css
    assert '[data-testid="stSidebar"] > div' not in css
    assert "scrollbar-gutter: stable" in css
