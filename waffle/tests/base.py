from django import test
from django.core import cache


class TestCase(test.TransactionTestCase):

    def setUp(self):
        cache.cache.clear()
        super().setUp()


class ReplicationRouter:
    """Router for simulating an environment with DB replication

    This router directs all DB reads to a completely different database than
    writes. This can be useful for simulating an environment where DB
    replication is delayed to identify potential race conditions.

    """
    def db_for_read(self, model, **hints):
        return 'readonly'

    def db_for_write(self, model, **hints):
        return 'default'
