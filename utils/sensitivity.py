"""Sensitivity detection and data masking utilities for PII protection."""
import re
import pandas as pd
import numpy as np


# Regex patterns for common PII
_EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
_PHONE_PATTERN = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
_SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
_CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
_IP_PATTERN = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')

# Column name patterns that suggest sensitive data
_SENSITIVE_NAMES = [
    'email', 'e_mail', 'e-mail', 'mail',
    'phone', 'telephone', 'tel', 'mobile', 'cell',
    'ssn', 'social_security', 'social-security',
    'credit_card', 'creditcard', 'card_number', 'cardnumber',
    'password', 'passwd', 'pwd',
    'address', 'street', 'zip', 'zipcode', 'postal',
    'id_number', 'national_id', 'passport', 'driver_license',
    'dob', 'date_of_birth', 'birth_date', 'birthdate',
    'ip_address', 'ip',
]


def detect_sensitive_columns(df):
    """Scan column names and sample values for patterns indicating personal data.
    Returns a list of (column_name, reason) tuples.
    """
    if df is None or df.empty:
        return []

    sensitive = []

    for col in df.columns:
        col_lower = col.lower().replace(' ', '_')
        reason = None

        # Check column name
        for pattern in _SENSITIVE_NAMES:
            if pattern in col_lower:
                reason = f"Column name matches sensitive pattern: '{pattern}'"
                break

        # If not caught by name, check sample values
        if reason is None:
            sample = df[col].dropna().head(100).astype(str)
            if sample.empty:
                continue

            # Check for email pattern
            email_matches = sample.apply(lambda x: bool(_EMAIL_PATTERN.search(x)))
            if email_matches.sum() > len(sample) * 0.3:
                reason = "Contains email addresses"

            # Check for phone pattern
            elif sample.apply(lambda x: bool(_PHONE_PATTERN.search(x))).sum() > len(sample) * 0.3:
                reason = "Contains phone numbers"

            # Check for SSN pattern
            elif sample.apply(lambda x: bool(_SSN_PATTERN.search(x))).sum() > len(sample) * 0.2:
                reason = "Contains SSN-like patterns"

            # Check for credit card pattern
            elif sample.apply(lambda x: bool(_CREDIT_CARD_PATTERN.search(x))).sum() > len(sample) * 0.2:
                reason = "Contains credit card numbers"

            # Check for IP addresses
            elif sample.apply(lambda x: bool(_IP_PATTERN.search(x))).sum() > len(sample) * 0.3:
                reason = "Contains IP addresses"

        if reason:
            sensitive.append((col, reason))

    return sensitive


def mask_column(df, column):
    """Replace values with masked versions.
    Returns (masked_df, rows_affected).
    Applies appropriate masking based on detected pattern.
    """
    df = df.copy()
    series = df[column].dropna()
    rows_affected = int(series.count())

    if rows_affected == 0:
        return df, 0

    sample = series.head(50).astype(str)

    # Detect type and apply appropriate masking
    email_ratio = sample.apply(lambda x: bool(_EMAIL_PATTERN.search(x))).mean()
    phone_ratio = sample.apply(lambda x: bool(_PHONE_PATTERN.search(x))).mean()
    ssn_ratio = sample.apply(lambda x: bool(_SSN_PATTERN.search(x))).mean()

    if email_ratio > 0.3:
        # Mask emails: j***@example.com
        df[column] = df[column].apply(_mask_email)
    elif phone_ratio > 0.3:
        # Mask phones: ***-***-1234
        df[column] = df[column].apply(_mask_phone)
    elif ssn_ratio > 0.2:
        # Mask SSNs: ***-**-1234
        df[column] = df[column].apply(_mask_ssn)
    else:
        # Generic masking: show first char and last char
        df[column] = df[column].apply(_mask_generic)

    return df, rows_affected


def _mask_email(val):
    """Mask email address: j***@example.com."""
    if pd.isna(val):
        return val
    val = str(val)
    match = _EMAIL_PATTERN.search(val)
    if match:
        email = match.group()
        parts = email.split('@')
        if len(parts) == 2:
            local = parts[0]
            masked_local = local[0] + '***' if len(local) > 0 else '***'
            return masked_local + '@' + parts[1]
    return '***'


def _mask_phone(val):
    """Mask phone number: ***-***-1234."""
    if pd.isna(val):
        return val
    val = str(val)
    # Extract last 4 digits
    digits = re.findall(r'\d', val)
    if len(digits) >= 4:
        return '***-***-' + ''.join(digits[-4:])
    return '***'


def _mask_ssn(val):
    """Mask SSN: ***-**-1234."""
    if pd.isna(val):
        return val
    val = str(val)
    digits = re.findall(r'\d', val)
    if len(digits) >= 4:
        return '***-**-' + ''.join(digits[-4:])
    return '***'


def _mask_generic(val):
    """Generic masking: show first and last char with *** in between."""
    if pd.isna(val):
        return val
    val = str(val)
    if len(val) <= 2:
        return '***'
    return val[0] + '***' + val[-1]
