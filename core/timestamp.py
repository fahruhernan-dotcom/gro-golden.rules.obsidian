"""
Universal Timestamp Parser and Formatter.
Supports Unix seconds, ms, us, ISO-8601, SQLite datetimes, and Protobuf timestamps.
Defaults to Asia/Jakarta (UTC+7) timezone formatting.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Tuple, Dict, Any, Optional

try:
    from .config import DEFAULT_TIMEZONE
except ImportError:
    DEFAULT_TIMEZONE = "Asia/Jakarta"


def get_target_timezone(tz_name: str = DEFAULT_TIMEZONE) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("Asia/Jakarta")


def parse_timestamp(
    raw_val: Any,
    tz: Optional[ZoneInfo] = None
) -> Tuple[datetime, Any]:
    """
    Parses timestamp into (datetime_obj, original_verbatim_val).
    Preserves original timestamp while producing localized datetime.
    """
    target_tz = tz or get_target_timezone()

    if raw_val is None:
        now = datetime.now(target_tz)
        return now, now.isoformat()

    # Already a datetime object
    if isinstance(raw_val, datetime):
        if raw_val.tzinfo is None:
            return raw_val.replace(tzinfo=target_tz), raw_val
        return raw_val.astimezone(target_tz), raw_val

    # Protobuf Timestamp dict: {"seconds": ..., "nanos": ...}
    if isinstance(raw_val, dict) and "seconds" in raw_val:
        try:
            sec = int(raw_val["seconds"])
            dt = datetime.fromtimestamp(sec, tz=timezone.utc).astimezone(target_tz)
            return dt, raw_val
        except Exception:
            now = datetime.now(target_tz)
            return now, raw_val

    # If bytes, decode
    if isinstance(raw_val, bytes):
        try:
            raw_val = raw_val.decode("utf-8").strip()
        except Exception:
            now = datetime.now(target_tz)
            return now, raw_val

    # Handle numeric values (int / float)
    if isinstance(raw_val, (int, float)):
        val = float(raw_val)
        if val <= 0:
            now = datetime.now(target_tz)
            return now, raw_val
        # Microseconds (> 1e14)
        if val > 1e14:
            val_sec = val / 1e6
        # Milliseconds (> 1e11)
        elif val > 1e11:
            val_sec = val / 1e3
        else:
            val_sec = val

        try:
            dt = datetime.fromtimestamp(val_sec, tz=timezone.utc).astimezone(target_tz)
            return dt, raw_val
        except (ValueError, OverflowError, OSError):
            now = datetime.now(target_tz)
            return now, raw_val

    # Handle string values
    val_str = str(raw_val).strip()

    # Numeric string
    if val_str.isdigit() or (val_str.replace(".", "", 1).isdigit() and val_str.count(".") <= 1):
        try:
            dt, _ = parse_timestamp(float(val_str), target_tz)
            return dt, raw_val
        except ValueError:
            pass

    # ISO-8601 variations
    norm_iso = val_str.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(norm_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=target_tz)
        else:
            dt = dt.astimezone(target_tz)
        return dt, raw_val
    except ValueError:
        pass

    # SQLite datetime formats: "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DD HH:MM:SS.fff"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S"):
        try:
            dt = datetime.strptime(val_str, fmt).replace(tzinfo=target_tz)
            return dt, raw_val
        except ValueError:
            continue

    # Fallback to current time
    now = datetime.now(target_tz)
    return now, raw_val


def format_dt(dt: datetime) -> Dict[str, str]:
    """
    Returns standard formatting for notes and filenames.
    """
    return {
        "date": dt.strftime("%Y-%m-%d"),
        "time": dt.strftime("%H:%M"),
        "file_time": dt.strftime("%H.%M"),
        "iso": dt.isoformat()
    }
