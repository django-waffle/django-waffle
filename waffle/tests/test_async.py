"""Tests for async API (aflag_is_active, aswitch_is_active, asample_is_active) and async decorator support."""

import asyncio
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.http import Http404, HttpResponse
from django.test import RequestFactory
from django.test.utils import override_settings

from unittest import mock

import waffle
from waffle.decorators import waffle_flag, waffle_switch
from waffle.tests.base import TestCase


DATABASES = {'default', 'readonly'}


def get(**kw):
    request = RequestFactory().get('/foo', data=kw)
    request.user = AnonymousUser()
    return request


class AsyncWaffleTests(TestCase):
    """Async version of test_waffle.WaffleTests."""

    databases = DATABASES

    async def test_superuser(self):
        """Test the superuser switch."""
        await waffle.get_waffle_flag_model().objects.acreate(name='myflag', superusers=True)
        request = get()
        assert not await waffle.aflag_is_active(request, 'myflag')

        superuser = get_user_model()(username='foo', is_superuser=True)
        request.user = superuser
        assert await waffle.aflag_is_active(request, 'myflag')

    async def test_staff(self):
        """Test the staff switch."""
        await waffle.get_waffle_flag_model().objects.acreate(name='myflag', staff=True)
        request = get()
        assert not await waffle.aflag_is_active(request, 'myflag')

        staff = get_user_model()(username='foo', is_staff=True)
        request.user = staff
        assert await waffle.aflag_is_active(request, 'myflag')

    async def test_languages(self):
        await waffle.get_waffle_flag_model().objects.acreate(name='myflag', languages='en,fr')
        request = get()
        assert not await waffle.aflag_is_active(request, 'myflag')

        request.LANGUAGE_CODE = 'en'
        assert await waffle.aflag_is_active(request, 'myflag')

        request.LANGUAGE_CODE = 'de'
        assert not await waffle.aflag_is_active(request, 'myflag')

    async def test_user(self):
        """Test the per-user switch."""
        user = await get_user_model().objects.acreate(username='foo')
        flag = await waffle.get_waffle_flag_model().objects.acreate(name='myflag')
        await flag.users.aadd(user)

        request = get()
        request.user = user
        assert await waffle.aflag_is_active(request, 'myflag')

        request.user = await get_user_model().objects.acreate(username='someone_else')
        assert not await waffle.aflag_is_active(request, 'myflag')

    async def test_group(self):
        """Test the per-group switch."""
        group = await Group.objects.acreate(name='foo')
        user = await get_user_model().objects.acreate(username='bar')
        await user.groups.aadd(group)

        flag = await waffle.get_waffle_flag_model().objects.acreate(name='myflag')
        await flag.groups.aadd(group)

        request = get()
        request.user = user
        assert await waffle.aflag_is_active(request, 'myflag')

        request.user = await get_user_model().objects.acreate(username='someone_else')
        assert not await waffle.aflag_is_active(request, 'myflag')

    async def test_authenticated(self):
        """Test the authenticated/anonymous switch."""
        await waffle.get_waffle_flag_model().objects.acreate(name='myflag', authenticated=True)

        request = get()
        assert not await waffle.aflag_is_active(request, 'myflag')

        request.user = get_user_model()(username='foo')
        assert request.user.is_authenticated
        assert await waffle.aflag_is_active(request, 'myflag')

    async def test_everyone_on(self):
        """Test the 'everyone' switch on."""
        await waffle.get_waffle_flag_model().objects.acreate(name='myflag', everyone=True)

        request = get()
        request.COOKIES['dwf_myflag'] = 'False'
        assert await waffle.aflag_is_active(request, 'myflag')

        request.user = get_user_model()(username='foo')
        assert await waffle.aflag_is_active(request, 'myflag')

    async def test_everyone_off(self):
        """Test the 'everyone' switch off."""
        await waffle.get_waffle_flag_model().objects.acreate(
            name='myflag', everyone=False, authenticated=True
        )

        request = get()
        request.COOKIES['dwf_myflag'] = 'True'
        assert not await waffle.aflag_is_active(request, 'myflag')

        request.user = get_user_model()(username='foo')
        assert request.user.is_authenticated
        assert not await waffle.aflag_is_active(request, 'myflag')

    async def test_percent(self):
        await waffle.get_waffle_flag_model().objects.acreate(name='myflag', percent='50.0')
        request = get()
        # Just ensure it doesn't error; result is random
        await waffle.aflag_is_active(request, 'myflag')

    async def test_undefined(self):
        """Undefined flags are always false."""
        request = get()
        assert not await waffle.aflag_is_active(request, 'foo')

    @override_settings(WAFFLE_FLAG_DEFAULT=True)
    async def test_undefined_default(self):
        """WAFFLE_FLAG_DEFAULT controls undefined flags."""
        request = get()
        assert await waffle.aflag_is_active(request, 'foo')

    @override_settings(WAFFLE_OVERRIDE=True)
    async def test_override(self):
        request = get(foo='1')
        await waffle.get_waffle_flag_model().objects.acreate(name='foo')  # Off for everyone.
        assert await waffle.aflag_is_active(request, 'foo')

    async def test_testing_flag(self):
        await waffle.get_waffle_flag_model().objects.acreate(name='foo', testing=True)
        request = get(dwft_foo='1')
        assert await waffle.aflag_is_active(request, 'foo')
        assert 'foo' in request.waffle_tests
        assert request.waffle_tests['foo']

        # GET param should override cookie
        request = get(dwft_foo='0')
        request.COOKIES['dwft_foo'] = 'True'
        assert not await waffle.aflag_is_active(request, 'foo')
        assert 'foo' in request.waffle_tests
        assert not request.waffle_tests['foo']

    async def test_testing_flag_header(self):
        await waffle.get_waffle_flag_model().objects.acreate(name='foo', testing=True)
        request = RequestFactory().get('/foo', HTTP_DWFT_FOO='1')
        request.user = AnonymousUser()
        assert await waffle.aflag_is_active(request, 'foo')
        assert 'foo' in request.waffle_tests
        assert request.waffle_tests['foo']

        # header should override cookie
        request = RequestFactory().get('/foo', HTTP_DWFT_FOO='0')
        request.user = AnonymousUser()
        request.COOKIES['dwft_foo'] = 'True'
        assert not await waffle.aflag_is_active(request, 'foo')
        assert 'foo' in request.waffle_tests
        assert not request.waffle_tests['foo']

    @override_settings(WAFFLE_CREATE_MISSING_FLAGS=True, WAFFLE_FLAG_DEFAULT=False)
    async def test_flag_created_dynamically_default_false(self):
        flag_model = waffle.get_waffle_flag_model()
        assert await flag_model.objects.acount() == 0
        assert not await waffle.aflag_is_active(get(), 'my_dynamically_created_flag')
        assert await flag_model.objects.acount() == 1

    @override_settings(WAFFLE_CREATE_MISSING_FLAGS=True, WAFFLE_FLAG_DEFAULT=True)
    async def test_flag_created_dynamically_default_true(self):
        flag_model = waffle.get_waffle_flag_model()
        assert await flag_model.objects.acount() == 0
        assert await waffle.aflag_is_active(get(), 'my_dynamically_created_flag')
        assert await flag_model.objects.acount() == 1

    @mock.patch('waffle.models.logger')
    async def test_no_logging_missing_flag_by_default(self, mock_logger):
        request = get()
        await waffle.aflag_is_active(request, 'foo')
        mock_logger.log.assert_not_called()

    @override_settings(WAFFLE_LOG_MISSING_FLAGS=logging.WARNING)
    @mock.patch('waffle.models.logger')
    async def test_logging_missing_flag(self, mock_logger):
        request = get()
        await waffle.aflag_is_active(request, 'foo')
        mock_logger.log.assert_called_with(logging.WARNING, 'Flag %s not found', 'foo')

    async def test_testing_flag_cookie(self):
        await waffle.get_waffle_flag_model().objects.acreate(name='foo', testing=True)
        request = get()
        request.COOKIES['dwft_foo'] = 'True'
        assert await waffle.aflag_is_active(request, 'foo')

    async def test_no_user_on_request(self):
        await waffle.get_waffle_flag_model().objects.acreate(name='myflag', superusers=True)
        request = RequestFactory().get('/foo')
        # request has no user attribute
        assert not await waffle.aflag_is_active(request, 'myflag')

    @override_settings(DATABASE_ROUTERS=['waffle.tests.base.ReplicationRouter'])
    async def test_read_from_write_db(self):
        await waffle.get_waffle_flag_model().objects.acreate(name='myflag', everyone=True)

        request = get()
        # By default, aflag_is_active should hit whatever it configured as the
        # read DB (so values will be stale if replication is lagged).
        assert not await waffle.aflag_is_active(request, 'myflag')


class AsyncBaseModelTests(TestCase):
    """Tests for async BaseModel methods (aget, aget_all, aflush) that aren't
    exercised through the public API tests above."""

    databases = DATABASES

    async def test_aget_cache_empty_branch(self):
        """Second call for a nonexistent key should hit CACHE_EMPTY."""
        model = waffle.get_waffle_switch_model()
        await waffle.aswitch_is_active('nonexistent')
        # Second call hits the CACHE_EMPTY branch
        result = await model.aget('nonexistent')
        assert result.pk is None

    async def test_aget_all(self):
        await waffle.get_waffle_switch_model().objects.acreate(name='s1', active=True)
        await waffle.get_waffle_switch_model().objects.acreate(name='s2', active=False)
        result = await waffle.get_waffle_switch_model().aget_all()
        assert len(result) == 2
        names = {s.name for s in result}
        assert names == {'s1', 's2'}

    async def test_aget_all_from_db(self):
        await waffle.get_waffle_switch_model().objects.acreate(name='s1', active=True)
        result = await waffle.get_waffle_switch_model().aget_all_from_db()
        assert len(result) == 1

    async def test_aget_all_cache_hit(self):
        await waffle.get_waffle_switch_model().objects.acreate(name='s1', active=True)
        await waffle.get_waffle_switch_model().aget_all()
        # Second call should hit cache
        result = await waffle.get_waffle_switch_model().aget_all()
        assert len(result) == 1

    async def test_aget_all_empty(self):
        result = await waffle.get_waffle_switch_model().aget_all()
        assert result == []

    async def test_aget_all_empty_cached(self):
        # First call sets CACHE_EMPTY
        await waffle.get_waffle_switch_model().aget_all()
        # Second call hits CACHE_EMPTY branch
        result = await waffle.get_waffle_switch_model().aget_all()
        assert result == []

    async def test_aflush(self):
        await waffle.get_waffle_switch_model().objects.acreate(name='flush_me', active=True)
        fetched = await waffle.get_waffle_switch_model().aget('flush_me')
        await fetched.aflush()
        # After flush, should still be fetchable from DB
        fetched2 = await waffle.get_waffle_switch_model().aget('flush_me')
        assert fetched2.pk == fetched.pk

    async def test_aflush_flag(self):
        await waffle.get_waffle_flag_model().objects.acreate(name='myflag', everyone=True)
        fetched = await waffle.get_waffle_flag_model().aget('myflag')
        await fetched.aflush()
        fetched2 = await waffle.get_waffle_flag_model().aget('myflag')
        assert fetched2.pk == fetched.pk


class AsyncSwitchTests(TestCase):
    """Async version of test_waffle.SwitchTests."""

    databases = DATABASES

    async def test_switch_active(self):
        switch = await waffle.get_waffle_switch_model().objects.acreate(
            name='myswitch', active=True
        )
        assert await waffle.aswitch_is_active(switch.name)

    async def test_switch_inactive(self):
        switch = await waffle.get_waffle_switch_model().objects.acreate(
            name='myswitch', active=False
        )
        assert not await waffle.aswitch_is_active(switch.name)

    async def test_undefined(self):
        assert not await waffle.aswitch_is_active('foo')

    @override_settings(WAFFLE_SWITCH_DEFAULT=True)
    async def test_undefined_default(self):
        assert await waffle.aswitch_is_active('foo')

    @override_settings(DATABASE_ROUTERS=['waffle.tests.base.ReplicationRouter'])
    async def test_read_from_write_db(self):
        switch = await waffle.get_waffle_switch_model().objects.acreate(
            name='switch', active=True
        )

        # By default, aswitch_is_active should hit whatever it configured as the
        # read DB (so values will be stale if replication is lagged).
        assert not await waffle.aswitch_is_active(switch.name)

    @override_settings(WAFFLE_CREATE_MISSING_SWITCHES=True, WAFFLE_SWITCH_DEFAULT=False)
    async def test_switch_created_dynamically_false(self):
        assert await waffle.get_waffle_switch_model().objects.acount() == 0
        assert not await waffle.aswitch_is_active('my_dynamically_created_switch')
        assert await waffle.get_waffle_switch_model().objects.acount() == 1

        switch = await waffle.get_waffle_switch_model().objects.aget(name='my_dynamically_created_switch')
        assert switch.name == 'my_dynamically_created_switch'
        assert not switch.active

    @override_settings(WAFFLE_CREATE_MISSING_SWITCHES=True, WAFFLE_SWITCH_DEFAULT=True)
    async def test_switch_created_dynamically_true(self):
        assert await waffle.get_waffle_switch_model().objects.acount() == 0
        assert await waffle.aswitch_is_active('my_dynamically_created_switch')
        assert await waffle.get_waffle_switch_model().objects.acount() == 1

        switch = await waffle.get_waffle_switch_model().objects.aget(name='my_dynamically_created_switch')
        assert switch.name == 'my_dynamically_created_switch'
        assert switch.active

    @mock.patch('waffle.models.logger')
    async def test_no_logging_missing_switch_by_default(self, mock_logger):
        await waffle.aswitch_is_active('foo')
        mock_logger.log.assert_not_called()

    @override_settings(WAFFLE_LOG_MISSING_SWITCHES=logging.WARNING)
    @mock.patch('waffle.models.logger')
    async def test_logging_missing_switch(self, mock_logger):
        await waffle.aswitch_is_active('foo')
        mock_logger.log.assert_called_with(
            logging.WARNING, 'Switch %s not found', 'foo'
        )


class AsyncSampleTests(TestCase):
    """Async version of test_waffle.SampleTests."""

    databases = DATABASES

    async def test_sample_100(self):
        sample = await waffle.get_waffle_sample_model().objects.acreate(
            name='sample', percent='100.0'
        )
        assert await waffle.asample_is_active(sample.name)

    async def test_sample_0(self):
        sample = await waffle.get_waffle_sample_model().objects.acreate(
            name='sample', percent='0.0'
        )
        assert not await waffle.asample_is_active(sample.name)

    async def test_undefined(self):
        assert not await waffle.asample_is_active('foo')

    @override_settings(WAFFLE_SAMPLE_DEFAULT=True)
    async def test_undefined_default(self):
        assert await waffle.asample_is_active('foo')

    @override_settings(DATABASE_ROUTERS=['waffle.tests.base.ReplicationRouter'])
    async def test_read_from_write_db(self):
        sample = await waffle.get_waffle_sample_model().objects.acreate(
            name='sample', percent='100.0'
        )

        # By default, asample_is_active should hit whatever it configured as the
        # read DB (so values will be stale if replication is lagged).
        assert not await waffle.asample_is_active(sample.name)

    @override_settings(WAFFLE_CREATE_MISSING_SAMPLES=True, WAFFLE_SAMPLE_DEFAULT=False)
    async def test_sample_created_dynamically_default_false(self):
        assert await waffle.get_waffle_sample_model().objects.acount() == 0
        assert not await waffle.asample_is_active('my_dynamically_created_sample')
        assert await waffle.get_waffle_sample_model().objects.acount() == 1

        sample = await waffle.get_waffle_sample_model().objects.aget(name='my_dynamically_created_sample')
        assert sample.percent == 0.0

    @override_settings(WAFFLE_CREATE_MISSING_SAMPLES=True, WAFFLE_SAMPLE_DEFAULT=True)
    async def test_sample_created_dynamically_default_true(self):
        assert await waffle.get_waffle_sample_model().objects.acount() == 0
        assert await waffle.asample_is_active('my_dynamically_created_sample')
        assert await waffle.get_waffle_sample_model().objects.acount() == 1

        sample = await waffle.get_waffle_sample_model().objects.aget(name='my_dynamically_created_sample')
        assert sample.percent == 100.0

    @mock.patch('waffle.models.logger')
    async def test_no_logging_missing_sample_by_default(self, mock_logger):
        await waffle.asample_is_active('foo')
        mock_logger.log.assert_not_called()

    @override_settings(WAFFLE_LOG_MISSING_SAMPLES=logging.WARNING)
    @mock.patch('waffle.models.logger')
    async def test_logging_missing_sample(self, mock_logger):
        await waffle.asample_is_active('foo')
        mock_logger.log.assert_called_with(logging.WARNING, 'Sample %s not found', 'foo')


class AsyncDecoratorTests(TestCase):
    """Async view support for decorators (no sync equivalent)."""

    databases = DATABASES

    async def test_waffle_switch_async_view_active(self):
        await waffle.get_waffle_switch_model().objects.acreate(name='foo', active=True)

        @waffle_switch('foo')
        async def my_view(request):
            return HttpResponse('foo')

        request = get()
        response = await my_view(request)
        self.assertEqual(response.status_code, 200)

    async def test_waffle_switch_async_view_inactive(self):
        await waffle.get_waffle_switch_model().objects.acreate(name='foo', active=False)

        @waffle_switch('foo')
        async def my_view(request):
            return HttpResponse('foo')

        request = get()
        with self.assertRaises(Http404):
            await my_view(request)

    async def test_waffle_switch_async_view_negated(self):
        await waffle.get_waffle_switch_model().objects.acreate(name='foo', active=False)

        @waffle_switch('!foo')
        async def my_view(request):
            return HttpResponse('foo')

        request = get()
        response = await my_view(request)
        self.assertEqual(response.status_code, 200)

    async def test_waffle_flag_async_view_active(self):
        await waffle.get_waffle_flag_model().objects.acreate(name='foo', everyone=True)

        @waffle_flag('foo')
        async def my_view(request):
            return HttpResponse('foo')

        request = get()
        response = await my_view(request)
        self.assertEqual(response.status_code, 200)

    async def test_waffle_flag_async_view_inactive(self):
        await waffle.get_waffle_flag_model().objects.acreate(name='foo', everyone=False)

        @waffle_flag('foo')
        async def my_view(request):
            return HttpResponse('foo')

        request = get()
        with self.assertRaises(Http404):
            await my_view(request)

    async def test_waffle_flag_async_view_negated(self):
        await waffle.get_waffle_flag_model().objects.acreate(name='foo', everyone=False)

        @waffle_flag('!foo')
        async def my_view(request):
            return HttpResponse('foo')

        request = get()
        response = await my_view(request)
        self.assertEqual(response.status_code, 200)

    def test_decorator_preserves_coroutine_status(self):
        """Decorated async views should remain coroutine functions."""
        @waffle_flag('foo')
        async def async_flag_view(request):
            pass

        @waffle_switch('bar')
        async def async_switch_view(request):
            pass

        assert asyncio.iscoroutinefunction(async_flag_view)
        assert asyncio.iscoroutinefunction(async_switch_view)

    def test_decorator_preserves_sync_status(self):
        """Decorated sync views should remain non-coroutine functions."""
        @waffle_flag('foo')
        def sync_flag_view(request):
            pass

        @waffle_switch('bar')
        def sync_switch_view(request):
            pass

        assert not asyncio.iscoroutinefunction(sync_flag_view)
        assert not asyncio.iscoroutinefunction(sync_switch_view)
