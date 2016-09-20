def normalize_cf(cf_json):
    if isinstance(cf_json, dict):
        ref = cf_json.get('Ref')
        if ref is not None:
            return ref
        normalized = {}
        for key, value in cf_json.items():
            normalized[key] = normalize_cf(value)
        return normalized
    if isinstance(cf_json, list):
        return [normalize_cf(f) for f in cf_json]

    return cf_json