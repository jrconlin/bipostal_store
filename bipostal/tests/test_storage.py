import json
import unittest2

from nose.tools import eq_

from bipostal.storage import (BipostalStorageException, 
            configure_from_settings)
from pyramid import testing

class JSONRequest(testing.DummyRequest):

    def __init__(self, **kw):
        super(JSONRequest, self).__init__(**kw)
        if 'post' in kw:
            self.body = kw['post']

    @property
    def json_body(self):
        return json.loads(self.body, encoding=self.charset)


class DummyAuth(object):

    def set_dummy_return(self, response):
        self.response = response;

    def get_user_id(self, request):
        return self.reponse; 


class StorageTest(unittest2.TestCase):
    __test__ = False
    storage = None

    email = 'email@example.com'
    alias = 'alias@example.com'
    alias2 = 'alias2@example.com'
    origin = 'example.com'
    origin2 = 'example.org'

    def setUp(self):
        self.request = JSONRequest(post=json.dumps({'alias': 
            '123abc@example.com',
            'audience': self.audience}))
        self.request.registry['auth'] = DummyAuth()
        self.request.registry['auth'].set_dummy_return(self.email)

    def test_resolve_alias(self):
        if self.storage is None:
            return;
        self.storage.add_alias(self.email, self.alias)
        ret = self.storage.resolve_alias(self.alias)
        eq_( {'alias': self.alias,
             'status': 'active',
             'email': self.email,
             'user': self.email,
             'origin': None},
              ret)

    def test_bogus_status(self):
        if self.storage is None:
            return
        with self.assertRaises(BipostalStorageException):
            self.storage.add_alias(self.email, 
                    self.alias, status='bogus')

    def test_resolve_alias_unknown_alias(self):
        if self.storage is None:
            return;
        # Return None when we try to resolve an unknown alias?
        eq_(self.storage.resolve_alias('404'), {})

    def test_add_alias(self):
        if self.storage is None:
            return;
        result = self.storage.add_alias(self.email, 
                self.alias,
                origin=self.origin)
        result = self.storage.resolve_alias(self.alias,
                origin=self.origin)
        eq_(self.storage.resolve_alias(self.alias,
            origin=self.origin),
            { 'alias': self.alias,
             'status': 'active',
             'email': self.email,
             'user': self.email,
             'origin': self.origin })
        result = self.storage.get_aliases(self.email)
        eq_(result,
            [{'alias': self.alias,
              'status': 'active',
              'email': self.email,
              'user': self.email,
              'origin': self.origin,
              }])

    def test_get_aliases(self):
        if self.storage is None:
            return;
        self.storage.add_alias(self.email, 
                self.alias, 
                origin=self.origin)
        ff = [{'alias': self.alias,
              'user': self.email,
              'status': 'active',
              'email': self.email,
              'origin': self.origin,
              }]
        fff = self.storage.get_aliases(self.email)
        eq_(fff, ff)
        self.storage.add_alias(self.email, 
                self.alias2, 
                origin=self.origin2)
        key = lambda x: x['alias']
        expected = [{'alias': self.alias2,
                     'status': 'active',
                     'user': self.email,
                     'email': self.email,
                     'origin': self.origin2,
                     },
                    {'alias': self.alias,
                     'status': 'active',
                     'user': self.email,
                     'email': self.email,
                     'origin': self.origin,
                     }]
        import pdb; pdb.set_trace();
        eq_(sorted(self.storage.get_aliases(self.email), 
                key=key),
                sorted(expected, key=key))

    def test_get_aliases_fail_unknown_email(self):
        # Default to [] when we try to get aliases for an unknown email.
        if self.storage is None:
            return;
        eq_(self.storage.get_aliases(self.email), [])

    def test_delete_alias(self):
        if self.storage is None:
            return;
        self.storage.add_alias(self.email, 
                self.alias,
                origin=self.origin)
        deleted = self.storage.delete_alias(self.email, 
                self.alias,
                origin=self.origin)
        eq_(deleted, {
            'alias': self.alias,
            'status': 'deleted',
            'email': self.email, 
            'user': self.email, 
            'origin': self.origin })
        eq_(self.storage.resolve_alias(self.alias,
            origin=self.origin), {})
        eq_(self.storage.get_aliases(self.email), [])
        self.storage.add_alias(self.email, 
                self.alias,
                origin=self.origin)
        eq_(self.storage.resolve_alias(self.alias,
            origin=self.origin),
                {'alias': self.alias,
                    'status': 'active',
                    'email': self.email,
                    'user': self.email,
                    'origin': self.origin})

    def test_delete_alias_unknown_alias(self):
        if self.storage is None:
            return;
        # No effect when we try to delete an unknown alias?
        self.storage.add_alias(self.email, 
                self.alias,
                origin=self.origin)
        self.storage.delete_alias(self.email, 
                self.alias2)
        eq_(self.storage.get_aliases(self.email),
            [{ 'alias': self.alias, 
                'status': 'active', 
                'email': self.email,
                'user': self.email, 
                'origin': self.origin }])
        eq_(self.storage.resolve_alias(self.alias,
            origin=self.origin),
            { 'alias': self.alias,
                'status': 'active', 
                'email': self.email, 
                'user': self.email, 
                'origin': self.origin })

    def test_delete_alias_unknown_email(self):
        if self.storage is None:
            return;
        # No crash when we try to delete an unknown email.
        self.storage.delete_alias(self.email, self.alias)

    def test_alias_for_origin(self):
        if self.storage is None:
            return;
        self.storage.add_alias(self.email, 
                self.alias, 
                origin=self.origin)
        test = self.storage.get_alias_for_origin(self.email,
                self.origin)
        eq_(test[0].get('alias'), self.alias)
        

    def test_disabled_alias(self):
        self.storage.add_alias(self.email, 
                self.alias,
                origin=self.origin)
        self.storage.set_status_alias(self.email, 
                self.alias, 
                origin=self.origin,
                status='inactive')
        #allow "disabled" aliases to resolve. We're rejecting them in 
        # bipostal_milter
        eq_(self.storage.resolve_alias(self.alias,
            origin=self.origin),
                {'alias': self.alias,
                    'status': 'inactive',
                    'email': self.email,
                    'user': self.email,
                    'origin': self.origin})
        #eq_({}, self.storage.resolve_alias(self.alias))

    def test_user(self):
        if self.storage is None:
            return
        user_record = self.storage.create_user(self.email,
                self.email)
        eq_(user_record.get('email'), self.email)
        user_record['metainfo']['android'] = 'android_123'
        user_record1 = self.storage.create_user(self.email,
                self.email,
                user_record['metainfo']);
        eq_(user_record1['metainfo']['android'], "android_123")
        user_record = self.storage.get_user(self.email)
        eq_(user_record1, user_record)
        self.storage.remove_user(self.email, self.email)


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

    def tearDown(self):
        self.storage.flushall(pattern='%@example.com')
