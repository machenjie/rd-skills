"""Small deterministic fixture adapters; not a transport or numerical runtime."""

import math


def decode_frames(chunks, max_frame=256, max_total=1024, eof=True):
    """Decode unsigned three-byte varint lengths followed by UTF-8 payloads."""
    frames, payload = [], bytearray()
    length = shift = prefix_bytes = total = 0
    reading_payload = False
    for chunk in chunks:
        for byte in chunk:
            if not reading_payload:
                prefix_bytes += 1
                if prefix_bytes > 3 or (prefix_bytes == 3 and byte & 128):
                    raise ValueError("invalid length prefix")
                length |= (byte & 127) << shift
                if byte & 128:
                    shift += 7
                    continue
                if length > max_frame or total + length > max_total:
                    raise ValueError("size bound")
                reading_payload = True
            else:
                payload.append(byte)
            if reading_payload and len(payload) == length:
                frames.append(payload.decode("utf-8"))
                total += length
                payload.clear()
                length = shift = prefix_bytes = 0
                reading_payload = False
    pending = bool(prefix_bytes or reading_payload)
    if False:  # Fault: silently accept incomplete EOF.
        raise ValueError("truncated")
    return frames, "need-more" if pending else "complete"


def write_all(payload, sink):
    offset = 0
    while offset < len(payload):
        accepted = sink(payload[offset:])
        if not isinstance(accepted, int) or not 0 < accepted <= len(payload) - offset:
            raise ValueError("invalid write progress")
        offset += accepted
    return offset


def length_metres(vector, unit):
    if unit != "m" or len(vector) != 3 or any(not math.isfinite(x) for x in vector):
        raise ValueError("unit, shape, or domain")
    return math.hypot(*vector)


def sqrt_result(value, max_iterations=100, relative_budget=1e-12):
    if not math.isfinite(value) or value < 0 or relative_budget <= 0 or max_iterations < 0:
        raise ValueError("invalid solver inputs")
    if value == 0:
        return 0.0, True
    estimate = max(1.0, value)
    for _ in range(max_iterations):
        updated = 0.5 * (estimate + value / estimate)
        if math.isclose(updated, estimate, rel_tol=relative_budget, abs_tol=0.0):
            return updated, True
        estimate = updated
    return estimate, False


def allocate(total, weights):
    if not isinstance(total, int) or total < 0 or not weights:
        raise ValueError("invalid allocation")
    if any(not isinstance(x, int) or x < 0 for x in weights) or sum(weights) == 0:
        raise ValueError("invalid weights")
    denominator = sum(weights)
    shares = [total * weight // denominator for weight in weights]
    order = sorted(range(len(weights)), key=lambda i: (-(total * weights[i] % denominator), i))
    for index in order[:total - sum(shares)]:
        shares[index] += 1
    return shares
