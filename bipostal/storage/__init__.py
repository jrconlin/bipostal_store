from bipostal import _resolve_name

def get_group(group_name, dictionary):
    if group_name is None:
        return dictionary
    else:
        result = {}
        trim = len(group_name)+1
        for key in filter(lambda x: x.startswith(group_name), dictionary):
                result[key[trim:]] = dictionary[key]
        return result

def configure_from_settings(object_name, settings):
    config = dict(settings)
    if 'backend' not in config:
        if '%s.backend' % object_name in config:
           config = get_group(object_name, config)
    cls = _resolve_name(config.pop('backend'))
    return cls(**config)
