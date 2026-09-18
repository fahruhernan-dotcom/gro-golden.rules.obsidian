"""
Robust Timestamp Parser supporting Unix seconds/ms/us, ISO-8601, SQLite datetime, and Protobuf timestamps.
Defaults to Asia/Jakarta timezone.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Tuple
import re

# Fixed offset for Asia/Jakarta (WIB: UTC+7)
WIB_OFFSET = timedelta(hours=7)
WIB_TZ = timezone(WIB_OFFSET, name="Asia/Jakarta")

def parse_timestamp(
    raw_val: Union[int, float, str, bytes, None],
    target_tz: timezone = WIB_TZ
) -> Tuple[datetime, Optional[int]]:
    """
    Parses various timestamp representations into a timezone-aware datetime.
    Returns (datetime_obj, original_epoch_seconds).
    """
    if raw_val is None:
        now = datetime.now(target_tz)
        return now, int(now.timestamp())

    # If bytes, decode if string-like or inspect
    if isinstance(raw_val, bytes):
        try:
            raw_val = raw_val.decode("utf-8").strip()
        except Exception:
            now = datetime.now(target_tz)
            return now, int(now.timestamp())

    # Handle numeric values (int / float)
    if isinstance(raw_val, (int, float)):
        val = float(raw_val)
        if val <= 0:
            now = datetime.now(target_tz)
            return now, int(now.timestamp())
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
    # Normalize Z to +00:00
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


def parse_protobuf_timestamp(sub_bytes: bytes) -> Optional[int]:
    """
    Extracts epoch seconds from a protobuf Timestamp message (Field 1: int64 seconds, Field 2: int32 nanos).
    """
    if not sub_bytes or len(sub_bytes) < 2:
        return None
    pos = 0
    length = len(sub_bytes)
    seconds = None
    while pos < length:
        # read varint key
        k = 0
        s = 0
        while pos < length:
            b = sub_bytes[pos]
            pos += 1
            k |= (b & 0x7F) << s
            if (b & 0x80) == 0:
                break
            s += 7
        fnum = k >> 3
        wtype = k & 0x7
        if wtype == 0:
            val = 0
            s = 0
            while pos < length:
                b = sub_bytes[pos]
                pos += 1
                val |= (b & 0x7F) << s
                if (b & 0x80) == 0:
                    break
                s += 7
            if fnum == 1:
                seconds = val
        elif wtype == 1:
            pos += 8
        elif wtype == 2:
            l = 0
            s = 0
            while pos < length:
                b = sub_bytes[pos]
                pos += 1
                l |= (b & 0x7F) << s
                if (b & 0x80) == 0:
                    break
                s += 7
            pos += l
        elif wtype == 5:
            pos += 4
        else:
            break
    if seconds and 1000000000 < seconds < 3000000000:
        return seconds
    return None


def format_dt(dt: datetime) -> dict:
    """Convenience formatter for standard filenames and frontmatter."""
    return {
        "iso": dt.isoformat(),
        "date": dt.strftime("%Y-%m-%d"),
        "time": dt.strftime("%H:%M"),
        "file_time": dt.strftime("%H.%M")
    }
