from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, override_settings

import waffle
from waffle.models import Flag, Switch, Sample
from waffle.tests.base import TestCase


def get(**kw):
    request = RequestFactory().get('/foo', data=kw)
    request.user = AnonymousUser()
    return request


class CacheFaultToleranceFlagTests(TestCase):
    """Test that flag lookups survive cache failures."""

    def test_flag_is_active_when_cache_get_fails(self):
        Flag.objects.create(name='test-flag', everyone=True)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.get.side_effect = TimeoutError('cache down')
            cache.add.side_effect = TimeoutError('cache down')
            result = waffle.flag_is_active(get(), 'test-flag')
        assert result is True

    def test_flag_is_active_returns_default_when_flag_missing_and_cache_fails(self):
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.get.side_effect = TimeoutError('cache down')
            cache.add.side_effect = TimeoutError('cache down')
            result = waffle.flag_is_active(get(), 'nonexistent-flag')
        assert result is False

    def test_flag_get_all_when_cache_fails(self):
        Flag.objects.create(name='flag1', everyone=True)
        Flag.objects.create(name='flag2', everyone=False)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.get.side_effect = TimeoutError('cache down')
            cache.add.side_effect = TimeoutError('cache down')
            flags = Flag.get_all()
        assert len(flags) == 2
        names = {f.name for f in flags}
        assert names == {'flag1', 'flag2'}

    def test_flag_flush_survives_cache_failure(self):
        flag = Flag.objects.create(name='test-flag', everyone=True)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.delete_many.side_effect = ConnectionError('cache down')
            # Should not raise
            flag.flush()


class CacheFaultToleranceSwitchTests(TestCase):
    """Test that switch lookups survive cache failures."""

    def test_switch_is_active_when_cache_fails(self):
        Switch.objects.create(name='test-switch', active=True)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.get.side_effect = TimeoutError('cache down')
            cache.add.side_effect = TimeoutError('cache down')
            result = waffle.switch_is_active('test-switch')
        assert result is True

    def test_switch_inactive_when_cache_fails(self):
        Switch.objects.create(name='test-switch', active=False)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.get.side_effect = TimeoutError('cache down')
            cache.add.side_effect = TimeoutError('cache down')
            result = waffle.switch_is_active('test-switch')
        assert result is False


class CacheFaultToleranceSampleTests(TestCase):
    """Test that sample lookups survive cache failures."""

    def test_sample_is_active_when_cache_fails(self):
        Sample.objects.create(name='test-sample', percent=100.0)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.get.side_effect = TimeoutError('cache down')
            cache.add.side_effect = TimeoutError('cache down')
            result = waffle.sample_is_active('test-sample')
        assert result is True


class CacheRetryTests(TestCase):
    """Test retry logic in cache wrappers."""

    def test_retry_succeeds_on_second_attempt(self):
        Flag.objects.create(name='retry-flag', everyone=True)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            # First call raises, second succeeds with None (cache miss)
            cache.get.side_effect = [TimeoutError('cache down'), None]
            cache.add.return_value = True
            flag = Flag.get(name='retry-flag', cache_retries=1)
        assert flag.everyone is True
        assert cache.get.call_count == 2

    @override_settings(WAFFLE_CACHE_RETRIES=2)
    def test_global_retries_setting(self):
        Flag.objects.create(name='retry-flag', everyone=True)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            # All 3 attempts (1 + 2 retries) fail
            cache.get.side_effect = TimeoutError('cache down')
            cache.add.side_effect = TimeoutError('cache down')
            flag = Flag.get(name='retry-flag')
        # 1 initial + 2 retries = 3 attempts
        assert cache.get.call_count == 3
        assert flag.everyone is True

    def test_per_call_retries_override_global(self):
        Flag.objects.create(name='retry-flag', everyone=True)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.get.side_effect = TimeoutError('cache down')
            cache.add.side_effect = TimeoutError('cache down')
            flag = Flag.get(name='retry-flag', cache_retries=3)
        # 1 initial + 3 retries = 4 attempts
        assert cache.get.call_count == 4

    def test_public_api_cache_retries(self):
        Flag.objects.create(name='api-flag', everyone=True)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.get.side_effect = TimeoutError('cache down')
            cache.add.side_effect = TimeoutError('cache down')
            result = waffle.flag_is_active(get(), 'api-flag', cache_retries=1)
        assert result is True
        # 1 initial + 1 retry = 2 attempts for get
        assert cache.get.call_count == 2


class CacheFailoverDisabledTests(TestCase):
    """Test that CACHE_FAILOVER=False preserves original behavior."""

    @override_settings(WAFFLE_CACHE_FAILOVER=False)
    def test_exception_propagates_when_failover_disabled(self):
        Flag.objects.create(name='test-flag', everyone=True)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.get.side_effect = TimeoutError('cache down')
            with self.assertRaises(TimeoutError):
                waffle.flag_is_active(get(), 'test-flag')

    @override_settings(WAFFLE_CACHE_FAILOVER=False)
    def test_switch_exception_propagates_when_failover_disabled(self):
        Switch.objects.create(name='test-switch', active=True)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.get.side_effect = TimeoutError('cache down')
            with self.assertRaises(TimeoutError):
                waffle.switch_is_active('test-switch')

    @override_settings(WAFFLE_CACHE_FAILOVER=False)
    def test_sample_exception_propagates_when_failover_disabled(self):
        Sample.objects.create(name='test-sample', percent=100.0)
        with mock.patch('waffle.models.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.get.side_effect = TimeoutError('cache down')
            with self.assertRaises(TimeoutError):
                waffle.sample_is_active('test-sample')


class CacheLoggingTests(TestCase):
    """Test that cache failures are logged."""

    def test_warning_logged_on_cache_get_failure(self):
        Flag.objects.create(name='log-flag', everyone=True)
        with self.assertLogs('waffle', level='WARNING') as cm:
            with mock.patch('waffle.models.get_cache') as mock_get_cache:
                cache = mock_get_cache.return_value
                cache.get.side_effect = TimeoutError('cache down')
                cache.add.side_effect = TimeoutError('cache down')
                waffle.flag_is_active(get(), 'log-flag')
        assert any('Cache get failed' in msg for msg in cm.output)

    def test_warning_logged_on_cache_set_failure(self):
        with self.assertLogs('waffle', level='WARNING') as cm:
            mock_cache = mock.MagicMock()
            mock_cache.set.side_effect = TimeoutError('cache down')
            from waffle.utils import cache_set
            cache_set(mock_cache, 'test-key', 'test-value')
        assert any('Cache set failed' in msg for msg in cm.output)

    def test_warning_logged_on_cache_delete_many_failure(self):
        flag = Flag.objects.create(name='log-flag', everyone=True)
        with self.assertLogs('waffle', level='WARNING') as cm:
            with mock.patch('waffle.models.get_cache') as mock_get_cache:
                cache = mock_get_cache.return_value
                cache.delete_many.side_effect = ConnectionError('cache down')
                flag.flush()
        assert any('Cache delete_many failed' in msg for msg in cm.output)


class ManagerCacheFaultToleranceTests(TestCase):
    """Test that Manager.create() survives cache failures."""

    def test_manager_create_survives_cache_delete_failure(self):
        with mock.patch('waffle.managers.get_cache') as mock_get_cache:
            cache = mock_get_cache.return_value
            cache.delete.side_effect = TimeoutError('cache down')
            # Should not raise — the flag should still be created in DB
            flag = Flag.objects.create(name='created-flag', everyone=True)
        assert flag.name == 'created-flag'
        assert Flag.objects.filter(name='created-flag').exists()
