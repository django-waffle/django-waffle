from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.db import models

from waffle.utils import get_setting, get_cache


if TYPE_CHECKING:
    from waffle.models import _BaseModelType, AbstractBaseFlag, AbstractBaseSample, AbstractBaseSwitch  # noqa: F401,PLC0415
else:
    _BaseModelType = TypeVar("_BaseModelType")


class BaseManager(models.Manager, Generic[_BaseModelType]):
    KEY_SETTING = ''

    def get_by_natural_key(self, name: str) -> _BaseModelType:
        return self.get(name=name)

    def create(self, *args: Any, **kwargs: Any) -> _BaseModelType:
        cache = get_cache()
        ret = super().create(*args, **kwargs)
        cache_key = get_setting(self.KEY_SETTING)
        cache.delete(cache_key)
        return ret


class FlagManager(BaseManager['AbstractBaseFlag']):
    KEY_SETTING = 'ALL_FLAGS_CACHE_KEY'


class SwitchManager(BaseManager['AbstractBaseSwitch']):
    KEY_SETTING = 'ALL_SWITCHES_CACHE_KEY'


class SampleManager(BaseManager['AbstractBaseSample']):
    KEY_SETTING = 'ALL_SAMPLES_CACHE_KEY'
