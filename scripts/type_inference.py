import re
from datetime import datetime
from decimal import Decimal

_BOOLEAN_VALUES = {"true", "false"}
_INTEGER_RE = re.compile(r"^-?\d+$")
_NUMERIC_RE = re.compile(r"^-?\d+\.\d+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")


def _clean_numeric(value):
    return value.replace("$", "").replace(",", "").replace("%", "").strip()


def infer_column_type(values):
    non_blank = [v for v in values if v not in (None, "")]
    if not non_blank:
        return "TEXT"

    if all(v.strip().lower() in _BOOLEAN_VALUES for v in non_blank):
        return "BOOLEAN"

    cleaned = [_clean_numeric(v) for v in non_blank]
    if all(_INTEGER_RE.match(v) for v in cleaned):
        return "BIGINT"
    if all(_NUMERIC_RE.match(v) or _INTEGER_RE.match(v) for v in cleaned):
        return "NUMERIC"
    if all(_DATE_RE.match(v) for v in non_blank):
        return "DATE"
    if all(_TIMESTAMP_RE.match(v) for v in non_blank):
        return "TIMESTAMPTZ"
    return "TEXT"


def convert_value(value, pg_type):
    if value in (None, ""):
        return None
    if pg_type == "BOOLEAN":
        return value.strip().lower() == "true"
    if pg_type == "BIGINT":
        return int(_clean_numeric(value))
    if pg_type == "NUMERIC":
        return Decimal(_clean_numeric(value))
    if pg_type == "DATE":
        return datetime.strptime(value, "%Y-%m-%d").date()
    if pg_type == "TIMESTAMPTZ":
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S%z")
    return value
