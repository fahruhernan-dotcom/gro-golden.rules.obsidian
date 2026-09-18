"""
Low-level Protobuf Wire Decoder for Antigravity Steps Payloads.
Safe, read-only binary parser for extracting message text, timestamps, and tool calls.
"""

from typing import List, Optional, Tuple

def decode_protobuf_stream(data: bytes) -> List[Tuple[int, int, bytes]]:
    """
    Parses a raw protobuf byte stream into a list of (field_num, wire_type, raw_bytes_or_val).
    Does not throw exceptions on truncated or malformed streams.
    """
    if not data or not isinstance(data, (bytes, bytearray)):
        return []

    pos = 0
    length = len(data)
    fields: List[Tuple[int, int, bytes]] = []

    while pos < length:
        # Read varint tag
        tag = 0
        shift = 0
        valid_tag = False
        while pos < length and shift < 35:
            b = data[pos]
            pos += 1
            tag |= (b & 0x7F) << shift
            shift += 7
            if (b & 0x80) == 0:
                valid_tag = True
                break

        if not valid_tag or tag == 0:
            break

        field_num = tag >> 3
        wire_type = tag & 0x7

        if wire_type == 0:  # Varint
            v = 0
            s = 0
            while pos < length and s < 70:
                b = data[pos]
                pos += 1
                v |= (b & 0x7F) << s
                s += 7
                if (b & 0x80) == 0:
                    break
            fields.append((field_num, 0, v))

        elif wire_type == 1:  # 64-bit fixed
            if pos + 8 <= length:
                fields.append((field_num, 1, data[pos:pos+8]))
                pos += 8
            else:
                break

        elif wire_type == 2:  # Length-delimited
            # Read length varint
            vlen = 0
            s = 0
            valid_len = False
            while pos < length and s < 35:
                b = data[pos]
                pos += 1
                vlen |= (b & 0x7F) << s
                s += 7
                if (b & 0x80) == 0:
                    valid_len = True
                    break

            if not valid_len or pos + vlen > length:
                # Truncated or invalid length
                if pos < length:
                    fields.append((field_num, 2, data[pos:]))
                break

            fields.append((field_num, 2, data[pos:pos+vlen]))
            pos += vlen

        elif wire_type == 5:  # 32-bit fixed
            if pos + 4 <= length:
                fields.append((field_num, 5, data[pos:pos+4]))
                pos += 4
            else:
                break
        else:
            # Unknown wire type, cannot proceed reliably
            break

    return fields


def extract_user_text_from_payload(payload: bytes) -> Tuple[List[str], Optional[int]]:
    """
    Extracts user prompt strings from Field 19 (subfield 2 or 3) and timestamp from Field 5.
    """
    texts: List[str] = []
    timestamp: Optional[int] = None

    fields = decode_protobuf_stream(payload)
    for fnum, wtype, val in fields:
        if fnum == 5 and wtype == 2 and isinstance(val, bytes):
            # Inspect Field 5 -> Field 1 -> Field 1 for epoch seconds
            sub_fields = decode_protobuf_stream(val)
            for sf_num, sf_type, sf_val in sub_fields:
                if sf_num == 1 and sf_type == 2 and isinstance(sf_val, bytes):
                    ts_fields = decode_protobuf_stream(sf_val)
                    for t_num, t_type, t_val in ts_fields:
                        if t_num == 1 and t_type == 0 and isinstance(t_val, int):
                            if 1500000000 < t_val < 3000000000:
                                timestamp = t_val

        elif fnum == 19 and wtype == 2 and isinstance(val, bytes):
            # Inspect Field 19 -> subfield 2 / 3
            sub_fields = decode_protobuf_stream(val)
            for sf_num, sf_type, sf_val in sub_fields:
                if sf_num in (2, 3) and sf_type == 2 and isinstance(sf_val, bytes):
                    try:
                        text = sf_val.decode("utf-8")
                        if text.strip():
                            texts.append(text.strip())
                    except UnicodeDecodeError:
                        pass

    return texts, timestamp


def extract_assistant_text_from_payload(payload: bytes) -> List[str]:
    """
    Extracts assistant response text from Field 20 (subfield 1).
    """
    texts: List[str] = []
    fields = decode_protobuf_stream(payload)

    for fnum, wtype, val in fields:
        if fnum == 20 and wtype == 2 and isinstance(val, bytes):
            sub_fields = decode_protobuf_stream(val)
            for sf_num, sf_type, sf_val in sub_fields:
                if sf_num == 1 and sf_type == 2 and isinstance(sf_val, bytes):
                    try:
                        text = sf_val.decode("utf-8")
                        if text.strip():
                            texts.append(text.strip())
                    except UnicodeDecodeError:
                        pass

    return texts
