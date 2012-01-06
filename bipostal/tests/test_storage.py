import unittest2

from nose.tools import eq_

from bipostal.storage import configure_from_settings


class StorageTest(unittest2.TestCase):
    __test__ = False
    storage = None

    email = 'email@example.com'
    alias = 'alias@example.com'
    alias2 = 'alias2@example.com'

    def test_resolve_alias(self):
        if self.storage is None:
            return;
        self.storage.add_alias(self.email, self.alias)
        ret = self.storage.resolve_alias(self.alias)
        eq_(ret,
            {'email': self.email,
             'origin': None,
             'status': 'active',
             'alias': self.alias})

    def test_resolve_alias_unknown_alias(self):
        if self.storage is None:
            return;
        # Return None when we try to resolve an unknown alias?
        eq_(self.storage.resolve_alias('404'), {})

    def test_add_alias(self):
        if self.storage is None:
            return;
        result = self.storage.add_alias(self.email, self.alias)
        result = self.storage.resolve_alias(self.alias)
        eq_(self.storage.resolve_alias(self.alias),
            {'email': self.email,
             'status': 'active',
             'origin': None,
             'alias': self.alias})
        result = self.storage.get_aliases(self.email)
        eq_(result,
            [{'alias': self.alias,
              'status': 'active',
              'origin': None,
              'email': self.email}])

    def test_get_aliases(self):
        if self.storage is None:
            return;
        self.storage.add_alias(self.email, self.alias, origin='example.com')
        eq_(self.storage.get_aliases(self.email),
            [{'alias': self.alias,
              'status': 'active',
              'origin': 'example.com',
              'email': self.email}])

        self.storage.add_alias(self.email, self.alias2, origin='example.org')
        key = lambda x: x['alias']
        expected = [{'alias': self.alias2,
                     'status': 'active',
                     'origin': 'example.org',
                     'email': self.email},
                    {'alias': self.alias,
                     'status': 'active',
                     'origin': 'example.com',
                     'email': self.email}]
        eq_(sorted(self.storage.get_aliases(self.email), key=key),
            sorted(expected, key=key))

    def test_get_aliases_fail_unkwown_email(self):
        # Default to [] when we try to get aliases for an unknown email.
        if self.storage is None:
            return;
        eq_(self.storage.get_aliases(self.email), [])

    def test_delete_alias(self):
        if self.storage is None:
            return;
        self.storage.add_alias(self.email, self.alias)
        deleted = self.storage.delete_alias(self.email, self.alias)
        eq_(deleted, {'email': self.email, 'origin': None,
                      'alias': self.alias, 'status': 'deleted'})
        eq_(self.storage.resolve_alias(self.alias), {})
        eq_(self.storage.get_aliases(self.email), [])

    def test_delete_alias_unknown_alias(self):
        if self.storage is None:
            return;
        # No effect when we try to delete an unknown alias?
        self.storage.add_alias(self.email, self.alias)
        self.storage.delete_alias(self.email, self.alias2)
        eq_(self.storage.get_aliases(self.email),
            [{'alias': self.alias, 'origin': None,
              'status': 'active', 'email': self.email}])
        eq_(self.storage.resolve_alias(self.alias),
            {'email': self.email, 'origin': None,
             'status': 'active', 'alias': self.alias})

    def test_delete_alias_unknown_email(self):
        if self.storage is None:
            return;
        # No crash when we try to delete an unknown email.
        self.storage.delete_alias(self.email, self.alias)


class MemStorageTest(StorageTest):
    __test__ = True

    def setUp(self):
        settings = {'backend': 'bipostal.storage.mem.Storage'}
        self.storage = configure_from_settings('storage', settings)

"""
class RedisStorageTest(StorageTest):
    __test__ = True

    def setUp(self):
        # Use a separate db for testing.
        try:
            import redis
        except ImportError, e:
            print ("Redis not found. skipping tests.")
            self.storage = None
            return 
        settings = {'backend': 'bipostal.storage.redis_.Storage',
                    'db': 1,
                    'host': 'localhost',
                    'port': 6379,
                    }
        self.storage = configure_from_settings('storage', settings)
        # Clear out the db for testing.
        #self.storage.redis.flushall()
"""

class MysqlMemcacheTest(StorageTest):
    __test__ = True

    def setUp(self):
        try:
            import memcache
            import MySQLdb
        except ImportError, e:
            print ("Missing Components for MyswlMemcache. Skipping tests. %s" %
                    str(e))
        settings = {'backend': 'bipostal.storage.mysql_memcache.Storage',
                    'mysql.user': 'rw',
                    'mysql.password': 'rw',
                    'mysql.host': 'localhost',
                    'mysql.user_db': 'bipostal.user',
                    'memcache.servers': 'localhost:11211'}
        self.storage = configure_from_settings('storage', settings)
        self.storage.flushall()
