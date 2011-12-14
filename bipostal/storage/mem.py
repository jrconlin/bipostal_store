class Storage(object):

    def __init__(self, **kw):
        self.db = {}

    def resolve_alias(self, alias, origin=''):
        return self.db.get("%s-%s" % (alias, origin), {})

    def add_alias(self, user, alias, origin='', status='active'):
        self.db["%s-%s" % (alias,origin)] = rv = {'email': user,
                               'status': status,
                               'origin': origin,
                               'alias': alias}
        self.db.setdefault(user, []).append("%s-%s" % (alias, origin))
        return rv

    def get_aliases(self, user):
        result = []
        aliases = self.db.get(user, [])
        for alias in aliases:
            elem = alias.split('-',1)
            result.append(self.resolve_alias(alias=elem[0], origin=elem[1]))
        return result

    def delete_alias(self, user, alias, origin=''):
        if "%s-%s" % (alias, origin) in self.db:
            del self.db["%s-%s" % (alias, origin)]
            self.db[user].remove("%s-%s" % (alias, origin))
        return {'email': user,
                'alias': alias,
                'origin': origin,
                'status': 'deleted'}
