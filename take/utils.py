
def split_name(name):
    if '.' in name:
        return tuple(name.split('.'))
    else:
        return (name,)


def get_via_name_list(src, name_parts):
    """
    Util to get name sequence from a dict. For instance, `("location","query")`
    would return src["location"]["query"].
    """
    if len(name_parts) > 1:
        for part in name_parts[:-1]:
            if part not in src:
                return None
            src = src[part]
    return src.get(name_parts[-1])


def save_to_name_list(dest, name_parts, value):
    """
    Util to save some name sequence to a dict. For instance, `("location","query")` would save
    to dest["location"]["query"].
    """
    if len(name_parts) > 1:
        for part in name_parts[:-1]:
            if part not in dest:
                dest[part] = {}
            dest = dest[part]
    dest[name_parts[-1]] = value
