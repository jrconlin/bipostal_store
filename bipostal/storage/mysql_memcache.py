# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import memcache
import re
import time
from sqlalchemy import (Table, Column,
        String, Integer, Enum, MetaData, Text,
        create_engine, text)
from bipostal.storage import BipostalStorageException


class Storage(object):

    states = ['active', 'inactive', 'deleted']
    defaultState = 'active'

    def _connect(self):
        try:
            dsn = 'mysql://%s:%s@%s/%s' % (
                    self.config.get('mysql.user', 'user'),
                    self.config.get('mysql.password', 'password'),
                    self.config.get('mysql.host', 'localhost'),
                    self.config.get('msyql.db', 'bipostal')
                    )
            self.engine = create_engine(dsn, pool_recycle=3600)
        except Exception, e:
            logging.error('Could not connect to db "%s"' % repr(e))
            raise

    def __init__(self, **kw):
        try:
            self.config = kw
            self._connect()
            self.metadata = MetaData()
            self.user = Table('user', self.metadata,
                    Column('user', String(255), primary_key=True),
                    Column('email', String(255)),
                    Column('metainfo', Text, nullable=True),
                    )
            self.alias = Table('alias', self.metadata,
                    Column('alias', String(255), primary_key=True),
                    Column('user', String(255)),
                    Column('origin', String(190), nullable=True),
                    Column('created', Integer),
                    Column('status', Enum(self.states,
                        strict=True,
                        default=self.defaultState)),
                    Column('metainfo', Text, nullable=True)
                    )
            self.metadata.create_all(self.engine)
            self._mcache = memcache.Client(re.split('\s*,\s*',
                    kw['memcache.servers']))
        except Exception, ex:
            logging.error("""Could not initialize Storage: "%s" """, str(ex))
            raise ex

    def _resolve_status(self, status):
        if status is None:
            status = self.defaultState
        status = status.lower()
        if status not in self.states:
            raise BipostalStorageException('Invalid state specified. Please use "%s"' %
                    ', '.join(self.states))
        return status
        

    def resolve_alias(self, alias, origin=None, status=None):
        lookup = str('s2u:%s' % str(alias))
        status = self._resolve_status(status)
        mresult = self._mcache.get(lookup)
        if mresult is None:
            logging.info('Cache miss for %s' % alias )
            query = ('select user from alias where ' +
                'alias=:alias and status=:status ')
            if origin is not None:
                query += 'and origin=:origin '
            query += 'limit 1;'
            result = self.engine.execute(text(query), alias=alias,
                        status=status,
                        origin=origin).fetchone()
            if result is None:
                logging.info('No active alias for %s' % alias )
                return {}
            mresult = str(result[0])
            self._mcache.set(lookup, mresult)
            if origin == '':
                origin = None
        return {'email': mresult,
                'origin': origin,
                'alias': alias,
                'status': status}

    def add_alias(self, user, alias, origin=None,
                  status=None,
                  info=None,
                  created=None):
        alias = alias.lower()
        if created is None:
            created = time.time()
        if info is None:
            info = {}
        status = self._resolve_status(status)
        try:
            query = 'select alias from alias where user=:user '
            if origin is not None:
                query += 'and origin=:origin '
            query += 'limit 1;'
            row = self.engine.execute(text(query),
                    user=user,
                    origin=origin).fetchone()
            if row is None:
                logging.debug('Adding new alias %s for user %s' %
                        (alias, user))
                query = ('insert into alias '
                        '(user, origin, alias, status, created) '
                        'values(:user, :origin, :alias, :status, :created);')
                """
                if origin is None:
                    origin = ''
                """
                self.engine.execute(text(query),
                        user=user,
                        origin=origin,
                        alias=alias,
                        status=status,
                        created=int(created))
            else:
                alias = row[0]
                query = ('update alias set status=:status where '
                        'alias=alias')
                if origin is not None:
                    query += 'and origin=:origin '
                self.engine.execute(text(query),
                        status=status,
                        alias=alias,
                        origin=origin)
            self._mcache.set('s2u:%s' % str(alias), str(user))
            if origin == '':
                origin = None
            resp = {'email': user,
                    'alias': alias,
                    'origin': origin,
                    'status': status}
            return resp
        except ValueError, e:
            errstr = """Invalid value for alias creation "%s" """ % str(e)
            logging.error(errstr)
            raise BipostalStorageException(errstr)

    def get_aliases(self, user):
        try:
            query = ('select alias, origin, status '
                        'from alias where '
                        'status != "deleted" and '
                        'user=:user')
            rows = self.engine.execute(text(query),
                    user=user).fetchall()
            result = []
            for row in rows:
                origin = row[1]
                if origin is '':
                    origin = None
                result.append({'alias': row[0],
                               'email': user,
                               'origin': origin,
                               'status': row[2]})
            return result
        except Exception, e:
            logging.error('Could not fetch aliases for user %s "%s"' % (user,
                                                                    str(e)))
            raise

    def set_status_alias(self, user, alias, origin=None, status=None):
        try:
            query = ('update alias set status=:status where user=:user and '
                    'alias=:alias')
            status = self._resolve_status(status)
            if origin is not None:
                query += ' and origin=:origin '
            self.engine.execute(text(query),
                    status=status,
                    user=user,
                    origin=origin,
                    alias=alias)
            # flush the alias (it will be picked up if need be)
            self._mcache.delete('s2u:%s' % str(alias));
            return {'alias': alias,
                    'email': user,
                    'origin': origin,
                    'status': status}
        except Exception, e:
            logging.error('Could not %s alias %s for user %s "%s"' % (
                status, alias, user, str(e)))

    def delete_alias(self, user, alias, origin=None):
        logging.debug('Deleting alias %s for user %s' % (alias, user))
        result = self.set_status_alias(user, alias, origin, status='deleted')
        if result:
            self._mcache.delete('s2u:%s' % str(alias))
        return result

    def disable_alias(self, user, alias, origin=None):
        logging.debug('Disabling alias %s for user %s' % (alias, user))
        result = self.set_status_alias(user, alias, origin, status='inactive')
        if result:
            self._mcache.delete('s2u:%s' % str(alias))
        return result

    def flushall(self, pattern=None):
        logging.debug('Flushing aliases')
        sql = 'delete from alias '
        if pattern is not None:
            sql += 'where alias is like :pattern'
        self.engine.execute(text(sql), pattern=pattern)

    def create_user(self, user, email=None, metainfo=None):
        if email is None:
            email = user
        if metainfo is None or 'created' not in metainfo:
            if metainfo is None:
                metainfo = {}
            metainfo['created'] = int(time.time())
        try:
            logging.debug('Creating user %s' % email)
            self.engine.execute(text('insert into user (user, email, '
                'metainfo) values (:user, :email, metainfo) '
                'on duplicate key update email = :email, '
                'metainfo = :metainfo;'),
                user=user,
                email=email,
                metainfo=json.dumps(metainfo),
                )
            self._mcache.set('uid:%s' % str(user),
                    json.dumps({'created': int(time.time())}))
            return self.get_user(user)
        except Exception, e:
            logging.error("Could not create new user [%s]" %
                repr(e))
            raise

    def get_user(self, user):
        if user is None:
            return None
        row = self.engine.execute(text('select user, email, metainfo '
                'from user where user = :user limit 1;'),
                    user=user).fetchone()
        response = {'user': row[0],
                'email': row[1],
                'metainfo': {}}
        if len(row[2]):
            response['metainfo'] = json.loads(row[2])
        return response

    def remove_user(self, user, email):
        logging.warn("Removing user %s " % user)
        self.engine.execute(text('delete from user where user = :user'),
               user=user)
        self._mcache.delete('uid:%s' % str(user))
        return None


