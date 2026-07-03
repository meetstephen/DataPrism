"""Tests for utils/chat_charts.py — the safe replacement for the old
exec()-based chart sandbox in pages/8_Chat_With_Data.py.

Run with:  pytest tests/test_chat_charts.py -v
"""
import pandas as pd
import pytest

from utils.chat_charts import (
    build_chart_from_spec,
    extract_chart_spec,
    strip_chart_spec,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "region": ["North", "South", "East", "West", "North"],
        "revenue": [100, 200, 150, 300, 120],
        "quarter": ["Q1", "Q1", "Q1", "Q1", "Q2"],
    })


# ---------------------------------------------------------------------------
# extract_chart_spec
# ---------------------------------------------------------------------------

class TestExtractChartSpec:
    def test_valid_block(self):
        text = 'Some answer.\n```chartspec\n{"chart_type": "bar", "x": "region", "y": "revenue"}\n```\n'
        spec = extract_chart_spec(text)
        assert spec == {"chart_type": "bar", "x": "region", "y": "revenue"}

    def test_no_block_returns_none(self):
        assert extract_chart_spec("Just a plain text answer, no chart here.") is None

    def test_malformed_json_returns_none(self):
        text = "```chartspec\nnot valid json {{{\n```"
        assert extract_chart_spec(text) is None

    def test_non_dict_json_returns_none(self):
        text = '```chartspec\n["not", "a", "dict"]\n```'
        assert extract_chart_spec(text) is None

    def test_oversized_block_rejected(self):
        text = "```chartspec\n" + ("x" * 5000) + "\n```"
        assert extract_chart_spec(text) is None

    def test_empty_string(self):
        assert extract_chart_spec("") is None
        assert extract_chart_spec(None) is None


# ---------------------------------------------------------------------------
# strip_chart_spec
# ---------------------------------------------------------------------------

class TestStripChartSpec:
    def test_removes_block(self):
        text = 'Answer.\n```chartspec\n{"chart_type": "bar"}\n```\nMore text.'
        cleaned = strip_chart_spec(text)
        assert "chartspec" not in cleaned
        assert "chart_type" not in cleaned
        assert "Answer." in cleaned and "More text." in cleaned


# ---------------------------------------------------------------------------
# build_chart_from_spec — functional correctness
# ---------------------------------------------------------------------------

class TestBuildChartValid:
    def test_bar_chart_with_aggregation(self, sample_df):
        spec = {"chart_type": "bar", "x": "region", "y": "revenue", "agg": "sum"}
        fig = build_chart_from_spec(sample_df, spec)
        assert fig is not None

    def test_line_chart(self, sample_df):
        spec = {"chart_type": "line", "x": "quarter", "y": "revenue"}
        assert build_chart_from_spec(sample_df, spec) is not None

    def test_histogram_no_y_needed(self, sample_df):
        spec = {"chart_type": "histogram", "x": "revenue"}
        assert build_chart_from_spec(sample_df, spec) is not None

    def test_pie_chart(self, sample_df):
        spec = {"chart_type": "pie", "x": "region", "y": "revenue"}
        assert build_chart_from_spec(sample_df, spec) is not None

    def test_color_grouping(self, sample_df):
        spec = {"chart_type": "bar", "x": "region", "y": "revenue", "color": "quarter"}
        assert build_chart_from_spec(sample_df, spec) is not None


# ---------------------------------------------------------------------------
# build_chart_from_spec — security & robustness (the whole point of this module)
# ---------------------------------------------------------------------------

class TestBuildChartSecurity:
    def test_unknown_chart_type_rejected(self, sample_df):
        spec = {"chart_type": "definitely_not_a_real_type", "x": "region"}
        assert build_chart_from_spec(sample_df, spec) is None

    def test_nonexistent_column_rejected(self, sample_df):
        spec = {"chart_type": "bar", "x": "not_a_real_column", "y": "revenue"}
        assert build_chart_from_spec(sample_df, spec) is None

    def test_code_injection_attempt_in_x_is_inert(self, sample_df):
        """A malicious/hallucinated column name must never be evaluated —
        only ever compared against the real DataFrame's column list."""
        spec = {
            "chart_type": "bar",
            "x": "().__class__.__bases__[0].__subclasses__()",
            "y": "revenue",
        }
        assert build_chart_from_spec(sample_df, spec) is None

    def test_code_injection_attempt_in_title_is_inert(self, sample_df):
        spec = {
            "chart_type": "bar", "x": "region", "y": "revenue",
            "title": "__import__('os').system('echo pwned')",
        }
        # Should render fine — title is just text, never executed
        fig = build_chart_from_spec(sample_df, spec)
        assert fig is not None

    def test_empty_dataframe(self):
        spec = {"chart_type": "bar", "x": "a", "y": "b"}
        assert build_chart_from_spec(pd.DataFrame(), spec) is None

    def test_none_dataframe(self):
        spec = {"chart_type": "bar", "x": "a", "y": "b"}
        assert build_chart_from_spec(None, spec) is None

    def test_none_spec(self, sample_df):
        assert build_chart_from_spec(sample_df, None) is None

    def test_invalid_agg_falls_back_to_none(self, sample_df):
        spec = {"chart_type": "bar", "x": "region", "y": "revenue", "agg": "DROP TABLE"}
        # Should not raise; invalid agg just means no aggregation is applied
        fig = build_chart_from_spec(sample_df, spec)
        assert fig is not None

    def test_invalid_color_column_ignored_not_fatal(self, sample_df):
        spec = {"chart_type": "bar", "x": "region", "y": "revenue", "color": "nonexistent"}
        fig = build_chart_from_spec(sample_df, spec)
        assert fig is not None  # bad color falls back to None, chart still renders

    def test_no_exec_reachable_end_to_end(self, sample_df):
        """Full pipeline: a hostile 'model response' containing the classic
        sandbox-escape payload must never execute anything. An invalid `y`
        safely degrades to a count-of-`x` chart (matching plain
        px.bar(df, x=...) behavior) rather than crashing or executing the
        payload string — the payload is only ever compared against real
        column names, never evaluated.
        """
        hostile_response = (
            "Here's your chart.\n```chartspec\n"
            '{"chart_type": "bar", '
            '"x": "region", '
            '"y": "() and __import__(\'os\').system(\'touch /tmp/pwned\')"}\n'
            "```\n"
        )
        spec = extract_chart_spec(hostile_response)
        build_chart_from_spec(sample_df, spec)  # exercised for its side effects only
        # The malicious "y" is not a real column, so it's discarded and the
        # chart falls back to counting rows per region - a legitimate,
        # harmless result. The only thing this test actually needs to prove
        # is that the payload string was never executed:
        import os
        assert not os.path.exists("/tmp/pwned")
