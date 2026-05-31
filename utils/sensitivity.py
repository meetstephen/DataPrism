"""PII / sensitive data detection and masking utilities."""
import pandas as pd
import re


# Patterns for common PII types
_PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "ip_address": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
}

# Column name heuristics for PII
_SENSITIVE_NAME_KEYWORDS = [
    "email", "phone", "tel", "mobile", "ssn", "social_security",
    "credit_card", "card_number", "passport", "license", "address",
    "zip", "postal", "dob", "date_of_birth", "birth",
    "first_name", "last_name", "full_name", "name", "surname",
    "ip_address", "ip", "password", "pwd", "secret",
]


def detect_sensitive_columns(df):
    """Detect columns that likely contain PII or sensitive data.

    Returns a list of dicts with keys: column, sensitivity_type, confidence, sample_match.
    """
    if df is None or df.empty:
        return []

    results = []

    for col in df.columns:
        col_lower = col.lower().replace(" ", "_")

        # Check column name heuristics
        name_match = None
        for keyword in _SENSITIVE_NAME_KEYWORDS:
            if keyword in col_lower:
                name_match = keyword
                break

        # Check content patterns for string columns
        content_match = None
        sample = None
        if df[col].dtype == "object":
            sample_vals = df[col].dropna().head(100).astype(str)
            for pii_type, pattern in _PII_PATTERNS.items():
                matches = sample_vals.apply(lambda x: bool(pattern.search(str(x))))
                match_rate = matches.sum() / len(sample_vals) if len(sample_vals) > 0 else 0
                if match_rate > 0.3:
                    content_match = pii_type
                    matched_vals = sample_vals[matches]
                    sample = str(matched_vals.iloc[0]) if len(matched_vals) > 0 else None
                    break

        # Determine confidence and report
        if content_match and name_match:
            results.append({
                "column": col,
                "sensitivity_type": content_match,
                "confidence": "high",
                "reason": f"Column name contains '{name_match}' and content matches {content_match} pattern",
                "sample_match": sample,
            })
        elif content_match:
            results.append({
                "column": col,
                "sensitivity_type": content_match,
                "confidence": "high",
                "reason": f"Content matches {content_match} pattern",
                "sample_match": sample,
            })
        elif name_match:
            results.append({
                "column": col,
                "sensitivity_type": name_match,
                "confidence": "medium",
                "reason": f"Column name contains '{name_match}'",
                "sample_match": None,
            })

    return results


def mask_column(df, column, mask_type="partial"):
    """Mask values in a column for privacy.

    Args:
        df: DataFrame (not mutated - returns a copy).
        column: Column name to mask.
        mask_type: 'partial' (show first/last chars), 'full' (replace all), 'hash' (SHA256 hash).

    Returns (masked_df, rows_affected) tuple.
    """
    import hashlib

    df = df.copy()
    series = df[column]
    rows_affected = int(series.notna().sum())

    if mask_type == "full":
        df[column] = series.apply(lambda x: "***REDACTED***" if pd.notna(x) else x)
    elif mask_type == "hash":
        df[column] = series.apply(
            lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:12] if pd.notna(x) else x
        )
    else:  # partial
        def _partial_mask(val):
            if pd.isna(val):
                return val
            s = str(val)
            if len(s) <= 4:
                return "****"
            return s[:2] + "*" * (len(s) - 4) + s[-2:]
        df[column] = series.apply(_partial_mask)

    return df, rows_affected
