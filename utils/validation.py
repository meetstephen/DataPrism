"""Data validation rules engine for DataPrism.

Lets users declare expectations about their data (non-null, unique, numeric
range, allowed values, regex match) and evaluates them against a DataFrame,
returning a tidy pass/fail report plus per-rule violating-row masks.

All functions are pure (no Streamlit dependency) so they can be unit tested.
"""

import pandas as pd


# Supported rule types and their human-readable labels.
RULE_TYPES = {
    "not_null": "No missing values",
    "unique": "All values unique",
    "range": "Numeric range",
    "allowed_values": "Allowed values only",
    "regex": "Matches pattern",
}


def _coerce_numeric(series: pd.Series) -> pd.Series:
    """Coerce a series to numeric, turning non-parseable entries into NaN."""
    return pd.to_numeric(series, errors="coerce")


def get_violation_mask(df: pd.DataFrame, rule: dict) -> pd.Series:
    """Return a boolean Series marking rows that VIOLATE the given rule.

    A rule is a dict with keys: ``column``, ``rule_type`` and optional
    ``params``. Unknown rule types or missing columns yield an all-False mask.
    """
    column = rule.get("column")
    rule_type = rule.get("rule_type")
    params = rule.get("params", {}) or {}

    if column not in df.columns:
        return pd.Series([False] * len(df), index=df.index)

    series = df[column]

    if rule_type == "not_null":
        return series.isna()

    if rule_type == "unique":
        # Every member of a duplicated group is a violation; NaNs are ignored.
        dup = series.duplicated(keep=False)
        return dup & series.notna()

    if rule_type == "range":
        numeric = _coerce_numeric(series)
        mask = pd.Series([False] * len(df), index=df.index)
        min_val = params.get("min")
        max_val = params.get("max")
        if min_val is not None:
            mask = mask | (numeric < float(min_val))
        if max_val is not None:
            mask = mask | (numeric > float(max_val))
        # Values that cannot be parsed as numbers are violations too.
        mask = mask | (numeric.isna() & series.notna())
        return mask.fillna(False)

    if rule_type == "allowed_values":
        allowed = params.get("allowed", [])
        allowed_set = {str(v).strip() for v in allowed}
        as_str = series.astype("string")
        mask = ~as_str.isin(allowed_set)
        # Ignore genuine missing values for this membership check.
        return (mask & series.notna()).fillna(False)

    if rule_type == "regex":
        pattern = params.get("pattern", "")
        if not pattern:
            return pd.Series([False] * len(df), index=df.index)
        as_str = series.astype("string")
        matches = as_str.str.match(pattern, na=False)
        return (~matches & series.notna()).fillna(False)

    return pd.Series([False] * len(df), index=df.index)


def describe_rule(rule: dict) -> str:
    """Return a short human-readable description of a rule."""
    column = rule.get("column", "?")
    rule_type = rule.get("rule_type")
    params = rule.get("params", {}) or {}

    if rule_type == "not_null":
        return f"`{column}` has no missing values"
    if rule_type == "unique":
        return f"`{column}` values are all unique"
    if rule_type == "range":
        lo = params.get("min")
        hi = params.get("max")
        if lo is not None and hi is not None:
            return f"`{column}` between {lo} and {hi}"
        if lo is not None:
            return f"`{column}` \u2265 {lo}"
        if hi is not None:
            return f"`{column}` \u2264 {hi}"
        return f"`{column}` is numeric"
    if rule_type == "allowed_values":
        allowed = params.get("allowed", [])
        preview = ", ".join(str(v) for v in allowed[:5])
        if len(allowed) > 5:
            preview += ", ..."
        return f"`{column}` only in [{preview}]"
    if rule_type == "regex":
        return f"`{column}` matches /{params.get('pattern', '')}/"
    return f"`{column}`: {rule_type}"


def run_validation(df: pd.DataFrame, rules) -> dict:
    """Evaluate all rules against the DataFrame.

    Returns a dict with:
        ``results``: list of per-rule dicts (rule, status, violations, etc.)
        ``total_rules``, ``passed``, ``failed``: summary counts.
    """
    results = []
    passed = 0
    failed = 0
    total_rows = len(df)

    for rule in rules:
        try:
            mask = get_violation_mask(df, rule)
            violations = int(mask.sum())
        except Exception as exc:  # defensive: a bad regex etc. should not crash
            results.append({
                "rule": describe_rule(rule),
                "column": rule.get("column"),
                "type": rule.get("rule_type"),
                "status": "Error",
                "violations": 0,
                "violation_pct": 0.0,
                "detail": f"Could not evaluate: {exc}",
            })
            failed += 1
            continue

        status = "Pass" if violations == 0 else "Fail"
        if status == "Pass":
            passed += 1
        else:
            failed += 1

        results.append({
            "rule": describe_rule(rule),
            "column": rule.get("column"),
            "type": rule.get("rule_type"),
            "status": status,
            "violations": violations,
            "violation_pct": round(violations / total_rows * 100, 2) if total_rows else 0.0,
            "detail": f"{violations} of {total_rows} rows violate this rule" if violations else "All rows satisfy this rule",
        })

    return {
        "results": results,
        "total_rules": len(results),
        "passed": passed,
        "failed": failed,
    }
