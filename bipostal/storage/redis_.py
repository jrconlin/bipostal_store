import redis


class Storage(object):
    aliases = 'aliases:2:%s-%s'
    emails = 'emails:2:%s'

    def __init__(self, **kw):
        self.redis = redis.Redis(**kw)

    def resolve_alias(self, alias, origin=None):
        #Handle special cases where the origin is already included
        if '!' in alias and origin is None:
            (alias, origin) = alias.split('!', 1)

        if origin is None:
            origin = ''
        data = self.redis.hgetall(self.aliases  % (alias, origin))
        if data:
            data['status'] = data['status'].lower()
            data.update(alias=alias)
            if data.get('origin') == '':
                data['origin'] = None;
        return data

    def add_alias(self, user, alias, origin=None, status='active'):
        if origin is None:
            origin = ''
        rv = {'email': user, 'origin': origin, 'status': status}
        self.redis.hmset(self.aliases % (alias, origin), rv)
        self.redis.sadd(self.emails % user, '%s!%s' % (alias, origin))
        return self.resolve_alias(alias)

    def get_aliases(self, user):
        # XXX: this makes N redis calls, one per alias.
        aliases = self.redis.smembers(self.emails % user)
        return map(self.resolve_alias, aliases)

    def delete_alias(self, user, alias, origin=None):
        if origin is None:
            origin = ''
        self.redis.delete(self.aliases % (alias, origin))
        self.redis.srem(self.emails % user, '%s!%s' % (alias, origin))
        if origin == '':
            origin = None
        return {'email': user,
                'alias': alias,
                'origin': origin,
                'status': 'deleted'}
