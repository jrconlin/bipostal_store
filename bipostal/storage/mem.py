# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time
from bipostal.storage import BipostalStorageException


class Storage(object):

    key_pattern = "%s-%s"

    states = ['active', 'inactive', 'deleted']
    defaultState = 'active'

    def __init__(self, **kw):
        self.db = {}
        self.user = {}

    def _resolve_status(self, status):
        if status is None:
            status = self.defaultState
        status = status.lower()
        if status not in self.states:
            raise BipostalStorageException('Invalid state specified. Please use "%s"' %
                    ', '.join(self.states))
        return status
        
    def resolve_alias(self, alias, origin=None):
        return self.db.get(self.key_pattern % (alias, origin), {})

    def add_alias(self, user, alias, origin=None, status=None):
        status = self._resolve_status(status)
        key = self.key_pattern % (alias, origin)
        self.db[key] = rv = {'email': user,
                               'status': status,
                               'origin': origin,
                               'alias': alias}
        self.db.setdefault(user, []).append(key)
        return rv

    def get_aliases(self, user):
        result = []
        aliases = self.db.get(user, [])
        for alias in aliases:
            elem = alias.split('-', 1)
            result.append(self.resolve_alias(alias=elem[0], origin=elem[1]))
        return result

    def delete_alias(self, user, alias, origin=None):
        key = self.key_pattern % (alias, origin)
        if key in self.db:
            del self.db[key]
            self.db[user].remove(key)
        return {'email': user,
                'alias': alias,
                'origin': origin,
                'status': 'deleted'}

    def get_user(self, user):
        if user is None:
            return None
        return self.user[user]

    def remove_user(self, user, email):
        if user is None:
            return None
        del self.user[user]

    def create_user(self, user, email=None, metainfo=None):
        if email is None:
            email = user
        if metainfo is None:
            metainfo = {}
        if 'created' not in metainfo:
            metainfo.update({'created': int(time.time())})
        self.user[user] = {'user': user,
                'email': email,
                'metainfo': metainfo}
        return self.user[user]
