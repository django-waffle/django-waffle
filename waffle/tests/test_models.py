from django.contrib.auth import get_user_model
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
        user = get_user_model()(username='john.doe')
        flag = get_waffle_flag_model().objects.create(name='test-flag')
        flag.everyone = True
        self.assertEqual(flag.is_active_for_user(user), True)

    def test_is_active_for_user_when_everyone_is_disabled(self):
        user = get_user_model()(username='john.doe')
        flag = get_waffle_flag_model().objects.create(name='test-flag')
        flag.everyone = False
        self.assertEqual(flag.is_active_for_user(user), False)
