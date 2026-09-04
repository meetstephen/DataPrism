"""Regression tests for the compact, non-scroll-dependent navigation shell."""
import unittest

from utils.styles import THEMES, _build_css


class SidebarStyleTests(unittest.TestCase):

    def test_streamlit_owns_sidebar_scrolling(self):
        css = _build_css(THEMES["Enterprise Dark"])
        self.assertNotIn("overflow-y: auto !important", css)
        self.assertNotIn('[data-testid="stSidebar"] > div {', css)
        self.assertNotIn('[data-testid="stSidebar"] [data-testid="stSidebarContent"] {', css)

    def test_long_native_navigation_is_hidden(self):
        css = _build_css(THEMES["Enterprise Dark"])
        self.assertIn('[data-testid="stSidebarNav"] {', css)
        self.assertIn("display: none !important", css)

    def test_current_page_indicator_is_fixed_and_branded(self):
        css = _build_css(THEMES["Enterprise Dark"])
        self.assertIn(".dp-current-page", css)
        self.assertIn(".dp-sidebar-brand", css)
        self.assertIn(".dp-sidebar-footer", css)
        self.assertIn('[data-testid="stSelectbox"]', css)

