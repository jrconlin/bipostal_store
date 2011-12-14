
def _resolve_name(name):
    """ Resolve a string into a corresponding object. 
        borrowed from moz-core.
    """
    if name is None:
        return None
    obj = None
    parts = name.split('.')
    cursor = len(parts)
    module_name = parts[:cursor]
    last_xcp = None

    while cursor > 0:
        try:
            obj = __import__('.'.join(module_name))
            break
        except ImportError, e:
            last_xcp = e
            if cursor == 0:
               raise
            cursor -= 1
            module_name = parts[:cursor]
    for part in parts[1:]:
        try:
            obj = getattr(obj, part)
        except AttributeError:
            if last_xcp is not None:
                raise last_xcp
            raise ImportError(name)

    if obj is None:
        if last_xcp is not None:
            raise last_xcp
        raise ImportError(name)

    return obj
