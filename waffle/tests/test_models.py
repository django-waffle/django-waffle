from unittest import mock

from django.contrib.auth.models import Group, User
from django.test import TestCase

from waffle import (
    get_waffle_flag_model,
    get_waffle_sample_model,
    get_waffle_switch_model,
)
from waffle.models import CACHE_EMPTY
from waffle.utils import get_cache, get_setting, keyfmt


class ModelsTests(TestCase):
    def test_natural_keys(self):
        flag = get_waffle_flag_model().objects.create(name='test-flag')
        switch = get_waffle_switch_model().objects.create(name='test-switch')
        sample = get_waffle_sample_model().objects.create(name='test-sample', percent=0)

        self.assertEqual(flag.natural_key(), ('test-flag',))
        self.assertEqual(switch.natural_key(), ('test-switch',))
        self.assertEqual(sample.natural_key(), ('test-sample',))

        self.assertEqual(
            get_waffle_flag_model().objects.get_by_natural_key("test-flag"), flag
        )
        self.assertEqual(
            get_waffle_switch_model().objects.get_by_natural_key("test-switch"), switch
        )
        self.assertEqual(
            get_waffle_sample_model().objects.get_by_natural_key("test-sample"), sample
        )

    def test_flag_is_not_active_for_none_requests(self):
        flag = get_waffle_flag_model().objects.create(name='test-flag')
        self.assertEqual(flag.is_active(None), False)

    def test_is_active_for_user_when_everyone_is_active(self):
        flag = get_waffle_flag_model().objects.create(name='test-flag')
        flag.everyone = True
        self.assertEqual(flag.is_active_for_user(User()), True)


class GetAllPrefetchTests(TestCase):
    """Tests for the N+1 fix: get_all() batch-fetches user/group cache keys."""

    def setUp(self):
        super().setUp()
        get_cache().clear()

    def _user_cache_key(self, flag_name):
        return keyfmt(get_setting('FLAG_USERS_CACHE_KEY'), flag_name)

    def _group_cache_key(self, flag_name):
        return keyfmt(get_setting('FLAG_GROUPS_CACHE_KEY'), flag_name)

    def test_get_all_prefetches_ids_from_cache(self):
        """After get_all(), _get_user_ids() and _get_group_ids() return correct ids without extra cache gets."""
        Flag = get_waffle_flag_model()
        user = User.objects.create_user(username='alice')
        group = Group.objects.create(name='editors')
        flag = Flag.objects.create(name='flag-a')
        flag.users.add(user)
        flag.groups.add(group)

        cache = get_cache()
        cache.set(self._user_cache_key('flag-a'), {user.pk})
        cache.set(self._group_cache_key('flag-a'), {group.pk})

        flags = Flag.get_all()
        self.assertEqual(len(flags), 1)

        with mock.patch.object(cache, 'get', wraps=cache.get) as spy:
            user_result = flags[0]._get_user_ids()
            group_result = flags[0]._get_group_ids()
            spy.assert_not_called()
        self.assertIn(user.pk, user_result)
        self.assertIn(group.pk, group_result)

    def test_get_all_prefetch_uses_get_many_not_individual_gets(self):
        """_prefetch_user_group_ids issues one cache.get_many call, not N individual gets."""
        Flag = get_waffle_flag_model()
        Flag.objects.create(name='flag-x')
        Flag.objects.create(name='flag-y')

        cache = get_cache()
        with mock.patch.object(cache, 'get_many', wraps=cache.get_many) as spy:
            Flag._prefetch_user_group_ids(Flag.objects.all())
            self.assertEqual(spy.call_count, 1)
            # Called with keys for both flags (users + groups = 4 keys total)
            called_keys = spy.call_args[0][0]
            self.assertEqual(len(called_keys), 4)

    def test_prefetched_ids_used_by_getters(self):
        """_get_user_ids() and _get_group_ids() return prefetched values without hitting the cache."""
        Flag = get_waffle_flag_model()
        flag = Flag.objects.create(name='flag-c')
        flag._prefetched_user_ids = {42, 99}
        flag._prefetched_group_ids = {7}

        cache = get_cache()
        with mock.patch.object(cache, 'get', wraps=cache.get) as spy:
            user_result = flag._get_user_ids()
            group_result = flag._get_group_ids()
            spy.assert_not_called()

        self.assertEqual(user_result, {42, 99})
        self.assertEqual(group_result, {7})

    def test_prefetch_empty_cache_skips_attribute(self):
        """When a flag's user/group keys are absent from cache, no prefetch attribute is set."""
        Flag = get_waffle_flag_model()
        Flag.objects.create(name='flag-e')

        # Don't prime the cache — keys are absent.
        cache = get_cache()
        cache.clear()

        flags = Flag.get_all()
        self.assertEqual(len(flags), 1)
        self.assertIsNone(flags[0]._prefetched_user_ids)
        self.assertIsNone(flags[0]._prefetched_group_ids)

    def test_prefetch_cache_empty_sentinel_yields_empty_set(self):
        """A CACHE_EMPTY sentinel in cache means no users/groups; attribute is an empty set."""
        Flag = get_waffle_flag_model()
        Flag.objects.create(name='flag-f')

        cache = get_cache()
        cache.set(self._user_cache_key('flag-f'), CACHE_EMPTY)
        cache.set(self._group_cache_key('flag-f'), CACHE_EMPTY)
        cache.delete(get_setting(Flag.ALL_CACHE_KEY))

        flags = Flag.get_all()
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]._prefetched_user_ids, set())
        self.assertEqual(flags[0]._prefetched_group_ids, set())

    def test_prefetch_empty_flags_list_is_no_op(self):
        """_prefetch_user_group_ids with an empty list does nothing (no cache calls)."""
        Flag = get_waffle_flag_model()
        cache = get_cache()
        with mock.patch.object(cache, 'get_many', wraps=cache.get_many) as spy:
            Flag._prefetch_user_group_ids([])
            spy.assert_not_called()
