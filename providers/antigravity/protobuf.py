"""
Protobuf Wire Decoder for Antigravity step payloads.
Dynamically parses protobuf wire types (Varint, 64-bit, Length-Delimited, 32-bit).
Decodes discovered wire fields with defensive fallbacks and preserves unknown fields for forensics.
"""

from typing import Dict, List, Any, Optional, Tuple


def read_varint(data: bytes, pos: int) -> Tuple[int, int]:
    """Reads a protobuf varint starting at pos. Returns (value, new_pos)."""
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift > 70:
            raise ValueError("Varint too long")
    raise ValueError("Truncated varint")


def parse_protobuf_wire(data: bytes) -> Tuple[Dict[int, List[Any]], List[Dict[str, Any]]]:
    """
    Parses raw protobuf data into wire fields: {field_num: [values]}.
    Tracks unmapped/unhandled wire entries in unmapped_fields for forensic analysis.
    """
    fields: Dict[int, List[Any]] = {}
    unmapped: List[Dict[str, Any]] = []
    pos = 0
    length = len(data)

    while pos < length:
        try:
            tag, pos = read_varint(data, pos)
            field_num = tag >> 3
            wire_type = tag & 0x07

            if wire_type == 0:  # Varint
                val, pos = read_varint(data, pos)
                fields.setdefault(field_num, []).append(("varint", val))

            elif wire_type == 1:  # 64-bit
                if pos + 8 > length:
                    break
                val = data[pos:pos+8]
                pos += 8
                fields.setdefault(field_num, []).append(("fixed64", val))

            elif wire_type == 2:  # Length-delimited (string, bytes, embedded message)
                val_len, pos = read_varint(data, pos)
                if pos + val_len > length:
                    # Truncated or malformed
                    break
                val = data[pos:pos+val_len]
                pos += val_len
                fields.setdefault(field_num, []).append(("bytes", val))

            elif wire_type == 5:  # 32-bit
                if pos + 4 > length:
                    break
                val = data[pos:pos+4]
                pos += 4
                fields.setdefault(field_num, []).append(("fixed32", val))

            else:
                # Unknown wire type, record for forensics and stop parsing
                unmapped.append({
                    "pos": pos,
                    "field_num": field_num,
                    "wire_type": wire_type
                })
                break

        except Exception as e:
            unmapped.append({"pos": pos, "error": str(e)})
            break

    return fields, unmapped


def extract_user_text_from_payload(payload: bytes) -> Tuple[List[str], Optional[int]]:
    """
    Extracts user turn texts and timestamp epoch from step payload.
    Uses verified wire fields (e.g. Field 19 subfields, Field 5 epoch seconds) with generic fallback.
    """
    if not payload:
        return [], None

    texts: List[str] = []
    ts_epoch: Optional[int] = None

    fields, unmapped = parse_protobuf_wire(payload)

    # 1. Timestamp extraction (verified Field 5 varint in Step 14)
    if 5 in fields:
        for w_type, val in fields[5]:
            if w_type == "varint" and val > 1_600_000_000:
                ts_epoch = val
                break

    # 2. Text extraction from Field 19 (verified user message container)
    if 19 in fields:
        for w_type, val_bytes in fields[19]:
            if w_type == "bytes":
                sub_fields, _ = parse_protobuf_wire(val_bytes)
                # Check subfields 2 or 3 for text
                for sf_num in (2, 3):
                    if sf_num in sub_fields:
                        for sw_type, s_bytes in sub_fields[sf_num]:
                            if sw_type == "bytes":
                                try:
                                    txt = s_bytes.decode("utf-8").strip()
                                    if txt and txt not in texts:
                                        texts.append(txt)
                                except UnicodeDecodeError:
                                    pass

    # 3. Defensive fallback: if no text found via Field 19, scan all length-delimited fields
    if not texts:
        for f_num, items in fields.items():
            for w_type, b_data in items:
                if w_type == "bytes" and len(b_data) > 3:
                    try:
                        decoded = b_data.decode("utf-8").strip()
                        # Plausible user message heuristic
                        if len(decoded) > 5 and not any(c in decoded[:10] for c in ("\x00", "\x01")):
                            if decoded not in texts:
                                texts.append(decoded)
                    except UnicodeDecodeError:
                        pass

    return texts, ts_epoch


def extract_assistant_text_from_payload(payload: bytes) -> List[str]:
    """
    Extracts assistant turn text chunks from step payload.
    Uses verified Field 20 subfield 1 with generic fallback.
    """
    if not payload:
        return []

    texts: List[str] = []
    fields, unmapped = parse_protobuf_wire(payload)

    # 1. Verified Field 20 (assistant response container)
    if 20 in fields:
        for w_type, val_bytes in fields[20]:
            if w_type == "bytes":
                sub_fields, _ = parse_protobuf_wire(val_bytes)
                # Subfield 1 holds text chunks
                if 1 in sub_fields:
                    for sw_type, s_bytes in sub_fields[1]:
                        if sw_type == "bytes":
                            try:
                                txt = s_bytes.decode("utf-8")
                                if txt:
                                    texts.append(txt)
                            except UnicodeDecodeError:
                                pass

    # 2. Defensive fallback: scan length-delimited fields
    if not texts:
        for f_num, items in fields.items():
            for w_type, b_data in items:
                if w_type == "bytes" and len(b_data) > 10:
                    try:
                        decoded = b_data.decode("utf-8")
                        if len(decoded) > 10 and not any(c in decoded[:10] for c in ("\x00", "\x01")):
                            texts.append(decoded)
                    except UnicodeDecodeError:
                        pass

    return texts
