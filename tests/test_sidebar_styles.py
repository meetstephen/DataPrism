"""Regression tests for the sidebar's single-scroll-container contract."""
import unittest

from utils.styles import THEMES, _build_css


class SidebarStyleTests(unittest.TestCase):

    def test_only_sidebar_content_owns_vertical_scrolling(self):
        css = _build_css(THEMES["Enterprise Dark"])
        self.assertEqual(css.count("overflow-y: auto !important"), 1)
        self.assertIn('[data-testid="stSidebar"] > div {', css)
        self.assertIn('[data-testid="stSidebar"] [data-testid="stSidebarContent"] {', css)
        self.assertIn("overflow: hidden !important", css)

    def test_scroll_surface_has_stability_guards(self):
        css = _build_css(THEMES["Enterprise Dark"])
        self.assertIn("overscroll-behavior-y: contain", css)
        self.assertIn("scrollbar-gutter: stable", css)
        self.assertIn("overflow-anchor: none", css)
        self.assertIn("scroll-behavior: auto !important", css)

    def test_sidebar_design_is_compact_and_branded(self):
        css = _build_css(THEMES["Enterprise Dark"])
        self.assertIn(".dp-sidebar-brand", css)
        self.assertIn(".dp-sidebar-footer", css)
        self.assertIn("margin: 0.14rem 0 !important", css)
