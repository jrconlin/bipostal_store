import MySQLdb
from DBUtils.SimplePooledDB import PooledDB
import memcache
import re
import logging
import time
import json

class Storage(object):

    def __init__(self, **kw):
        try:
            self.config = kw;
            self._pool = PooledDB(MySQLdb, 5,
                host = kw['mysql.host'],
                user = kw['mysql.user'],
                passwd = kw['mysql.password'])
            self._stable = self.config.get('mysql.alias_db',
                    'bipostal.alias');
            self._utable = self.config.get('mysql.user_db',
                    'bipostal.user');
            self._mcache = memcache.Client(re.split('\s*,\s*',
                    kw['memcache.servers']))
        except Exception, ex:
            logging.error("""Could not initialize Storage: "%s" """, str(ex))

    def resolve_alias(self, alias, origin=None, status='active'):
        lookup = str('s2u:%s' % str(alias))
        mresult = self._mcache.get(lookup)
        if mresult is None:
            connection = self._pool.connection()
            db = connection.cursor()
            logging.info('Cache miss for %s' % alias );
            query = ('select user from %s where alias="%s" ' +
                        'and status="%s" %s limit 1;')
            if origin is not None:
                origin = 'and origin="%s"' % MySQLdb.escape_string(origin)
            else:
                origin = ''
            query = query % (
                 self._stable,
                 MySQLdb.escape_string(alias),
                 MySQLdb.escape_string(status),
                 origin)
            db.execute(query)
            result = db.fetchone()
            connection.close()
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
                  status='active',
                  info=None,
                  created=None):
        connection = self._pool.connection()
        db = connection.cursor()
        if created is None:
            created = time.time()
        if info is None:
            info = {}
        if origin is None:
            origin = ''
        try:
            query = ('select alias from %s where user="%s"' +
                        ' and origin="%s" limit 1;') % (
                            self._stable,
                            MySQLdb.escape_string(user),
                            MySQLdb.escape_string(origin))
            db.execute(query)
            row = db.fetchone()
            if row is None:
                logging.debug('Adding new alias %s for user %s' % 
                        (alias, user))
                query = ('insert into %s ' +
                        '(user,origin,alias,status,created)' +
                        'values("%s","%s","%s","%s",%s);')
                query = query % (
                         self._stable,
                         MySQLdb.escape_string(user),
                         MySQLdb.escape_string(origin),
                         MySQLdb.escape_string(alias),
                         MySQLdb.escape_string(status),
                         int(created))
                db.execute(query)
            else:
                alias = row[0]
                query = ('update %s set status="%s" where ' +
                        'alias="%s" and origin="%s"')
                query = query % (
                        self._stable,
                        MySQLdb.escape_string(status),
                        MySQLdb.escape_string(alias),
                        MySQLdb.escape_string(origin))
                db.execute(query)
            self._mcache.set('s2u:%s' % str(alias), str(user))
            connection.close()
            if origin == '':
                origin = None
            resp = {'email': user,
                    'alias': alias,
                    'origin': origin,
                    'status': status.lower()}
            return resp
        except ValueError, e:
            logging.error("""Invalid value for alias creation "%s" """ %
                          str(e))
            return False

    def get_aliases(self, user, status='active'):
        connection = self._pool.connection()
        db = connection.cursor()
        try:
            query = ('select alias,origin,status ' +
                        'from %s where ' +
                        'user="%s"')
            query = query % (
                        self._stable,
                        MySQLdb.escape_string(user))
            if status.lower() not in ['all', '*', '%']:
                query = query +' and status="%s"' % (
                    MySQLdb.escape_string(status)
                )
            db.execute(query)
            rows = db.fetchall()
            connection.close()
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

    def set_status_alias(self, user, alias, origin=None, status='deleted'):
        try:
            connection = self._pool.connection()
            db = connection.cursor()
            if origin is None:
                origin = ''
            query = ('update %s set status="%s" where user="%s" and ' +
                        'origin="%s" and alias="%s"')
            query = query % (
                        self._stable,
                        MySQLdb.escape_string(status.lower()),
                        MySQLdb.escape_string(user),
                        MySQLdb.escape_string(origin),
                        MySQLdb.escape_string(alias))
            db.execute(query)
            connection.close()
            if origin == '':
                origin = None
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
        result = self.set_status_alias(user, alias, origin, status='disabled')
        if result:
             self._mcache.delete('s2u:%s' % str(alias))
        return result

    def flushall(self):
        connection = self._pool.connection()
        db = connection.cursor()
        logging.debug('Flushing aliases')
        db.execute('delete from %s;' % self._stable)
        self._mcache.flush_all()
        connection.close()

    def create_user(self, user, email=None, metainfo=None):
        if email is None:
            email = user
        if metainfo is None:
            metainfo = {'created': int(time.time())}
        user_record = self._mcache.get('uid:%s' % str(user))
        if user_record is None:
            try:
                connection = self._pool.connection()
                db = connection.cursor()
                logging.debug('Creating user %s' % email)
                db.execute(("insert into %s (user, email, " + 
                    "metainfo) values ('%s', '%s', '%s') " +
                    "on duplicate key update email = '%s' ;") % (
                    self._utable,
                    MySQLdb.escape_string(user),
                    MySQLdb.escape_string(email),
                    MySQLdb.escape_string(json.dumps(metainfo)),
                    MySQLdb.escape_string(email),
                        ))
                self._mcache.set('uid:%s' % str(user), 
                        json.dumps({'created': int(time.time())}))
                return user
            except Exception, e:
                logging.error("Could not create new user [%s]" % 
                    repr(e))
                raise
        return user
