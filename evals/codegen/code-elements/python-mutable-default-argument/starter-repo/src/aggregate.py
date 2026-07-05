def collect_request_ids(request_id, seen=[]):
    seen.append(request_id)
    return list(seen)
