"""Regression tests for Streamlit-owned sidebar navigation and scrolling."""
import unittest

from utils.styles import THEMES, _build_css


class SidebarStyleTests(unittest.TestCase):

    def test_streamlit_owns_sidebar_scrolling(self):
        css = _build_css(THEMES["Enterprise Dark"])
        self.assertNotIn("overflow-y: auto !important", css)
        self.assertNotIn('[data-testid="stSidebar"] > div {', css)
        self.assertNotIn('[data-testid="stSidebar"] [data-testid="stSidebarContent"] {', css)

    def test_native_navigation_is_visible_and_styled(self):
        css = _build_css(THEMES["Enterprise Dark"])
        self.assertIn('[data-testid="stSidebarNav"] {', css)
        self.assertIn("display: block !important", css)
        self.assertIn('a[aria-current="page"]', css)
        self.assertNotIn("display: none !important", css)

    def test_sidebar_design_is_compact_and_branded(self):
        css = _build_css(THEMES["Enterprise Dark"])
        self.assertIn('[data-testid="stSidebarNav"]::before', css)
        self.assertIn('content: "DataPrism"', css)
        self.assertIn(".dp-sidebar-footer", css)
        self.assertIn("min-height: 2.55rem", css)

