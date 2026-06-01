from django.contrib.auth.models import Group, User
from django.db import models
from django.test import TestCase

from waffle import (
    get_waffle_flag_model,
    get_waffle_sample_model,
    get_waffle_switch_model,
)


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

    def test_get_all_queryset_returns_queryset(self):
        Flag = get_waffle_flag_model()
        Flag.objects.create(name='test-flag')
        self.assertIsInstance(Flag._get_all_queryset(), models.QuerySet)

    def test_get_all_from_db_returns_list(self):
        Flag = get_waffle_flag_model()
        Flag.objects.create(name='test-flag')
        result = Flag.get_all_from_db()
        self.assertIsInstance(result, list)

    def test_flag_get_all_from_db_prefetches_users_and_groups(self):
        Flag = get_waffle_flag_model()
        flag = Flag.objects.create(name='test-flag')
        user = User.objects.create_user(username='waffle-user')
        group = Group.objects.create(name='waffle-group')
        flag.users.add(user)
        flag.groups.add(group)

        flags = Flag.get_all_from_db()
        self.assertEqual(len(flags), 1)

        # users and groups should already be cached — no extra queries needed
        with self.assertNumQueries(0):
            list(flags[0].users.all())
            list(flags[0].groups.all())

    def test_flag_get_all_from_db_get_user_group_ids_no_extra_queries(self):
        """_get_user_ids / _get_group_ids must use the prefetch cache, not re-query."""
        Flag = get_waffle_flag_model()
        flag = Flag.objects.create(name='test-flag')
        user = User.objects.create_user(username='waffle-user')
        group = Group.objects.create(name='waffle-group')
        flag.users.add(user)
        flag.groups.add(group)

        flags = Flag.get_all_from_db()
        self.assertEqual(len(flags), 1)

        with self.assertNumQueries(0):
            user_ids = flags[0]._get_user_ids()
            group_ids = flags[0]._get_group_ids()

        self.assertEqual(user_ids, {user.pk})
        self.assertEqual(group_ids, {group.pk})

    def test_flag_get_all_prefetch_survives_cache(self):
        Flag = get_waffle_flag_model()
        flag = Flag.objects.create(name='test-flag')
        user = User.objects.create_user(username='waffle-user')
        group = Group.objects.create(name='waffle-group')
        flag.users.add(user)
        flag.groups.add(group)

        # Warm the cache via get_all()
        Flag.get_all()

        # Second call hits the cache; prefetch data must survive serialization
        flags = Flag.get_all()
        self.assertEqual(len(flags), 1)

        with self.assertNumQueries(0):
            user_ids = flags[0]._get_user_ids()
            group_ids = flags[0]._get_group_ids()

        self.assertEqual(user_ids, {user.pk})
        self.assertEqual(group_ids, {group.pk})

    def test_switch_get_all_from_db_returns_list(self):
        Switch = get_waffle_switch_model()
        Switch.objects.create(name='test-switch')
        result = Switch.get_all_from_db()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    def test_sample_get_all_from_db_returns_list(self):
        Sample = get_waffle_sample_model()
        Sample.objects.create(name='test-sample', percent=50)
        result = Sample.get_all_from_db()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
