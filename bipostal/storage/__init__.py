from bipostal import _resolve_name

def configure_from_settings(object_name, settings):
    config = dict(settings)
    cls = _resolve_name(config.pop('backend'))
    return cls(**config)
