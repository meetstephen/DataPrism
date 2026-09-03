"""Regression tests for expression, SQL, and export trust boundaries."""
import unittest

from utils.data_engine import validate_calculated_expression
from utils.sql_engine import _validate_query


class SecurityGuardTests(unittest.TestCase):

    def test_calculated_expression_allows_math_on_known_columns(self):
        self.assertTrue(validate_calculated_expression("`Course Cost` / credits", ["Course Cost", "credits"]))

    def test_calculated_expression_rejects_calls_attributes_and_locals(self):
        for expression in ["__import__('os')", "amount.__class__", "@secret", "open('x')", "amount[0]"]:
            with self.subTest(expression=expression):
                with self.assertRaises(ValueError):
                    validate_calculated_expression(expression, ["amount"])

    def test_sql_accepts_read_only_query(self):
        self.assertIsNone(_validate_query("WITH totals AS (SELECT 1 AS n) SELECT * FROM totals"))
        self.assertIsNone(_validate_query("SELECT 'drop table' AS harmless_text"))

    def test_sql_rejects_stacked_or_privileged_statements(self):
        blocked = [
            "SELECT 1; ATTACH DATABASE 'x' AS x",
            "WITH x AS (DELETE FROM data RETURNING *) SELECT * FROM x",
            "PRAGMA database_list",
            "SELECT load_extension('bad')",
        ]
        for query in blocked:
            with self.subTest(query=query):
                self.assertIsNotNone(_validate_query(query))
