from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.contrib.admin.models import LogEntry, CHANGE, DELETION
from django.contrib.admin.widgets import ManyToManyRawIdWidget
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from waffle.models import Flag, Sample, Switch
from waffle.utils import get_setting


class BaseAdmin(admin.ModelAdmin):
    search_fields = ('name', 'note')

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


def _add_log_entry(user, model, description, action_flag):
    LogEntry.objects.create(
        user=user,
        content_type=ContentType.objects.get_for_model(type(model)),
        object_id=model.id,
        object_repr=model.name + " " + description,
        action_flag=action_flag
    )


@admin.action(
    description=_('Enable selected flags for everyone'),
    permissions=('change',),
)
def enable_for_all(ma, request, qs):
    # Iterate over all objects to cause cache invalidation.
    for f in qs.all():
        _add_log_entry(request.user, f, "on", CHANGE)
        f.everyone = True
        f.save()


@admin.action(
    description=_('Disable selected flags for everyone'),
    permissions=('change',),
)
def disable_for_all(ma, request, qs):
    # Iterate over all objects to cause cache invalidation.
    for f in qs.all():
        _add_log_entry(request.user, f, "off", CHANGE)
        f.everyone = False
        f.save()


@admin.action(
    description=_('Delete selected'),
    permissions=('delete',),
)
def delete_individually(ma, request, qs):
    # Iterate over all objects to cause cache invalidation.
    for f in qs.all():
        _add_log_entry(request.user, f, "deleted", DELETION)
        f.delete()


class InformativeManyToManyRawIdWidget(ManyToManyRawIdWidget):
    """Widget for ManyToManyField to Users.

    Will display the names of the users in a parenthesised list after the
    input field. This widget works with all models that have a "name" field.
    """
    def label_and_url_for_value(self, values: Any) -> tuple[str, str]:
        field = self.rel.get_related_field()
        clean_values = []
        for value in values:
            try:
                clean_values.append(field.clean(value, None))
            except ValidationError:
                clean_values.append(None)

        objects_dict = (
            self.rel.model._default_manager
                .using(self.db)
                .in_bulk(clean_values, field_name=field.name)
        )

        names = []
        for value in clean_values:
            if value in objects_dict:
                names.append(escape(str(objects_dict[value])))
            else:
                names.append("<missing>")
        return "(" + ", ".join(names) + ")", ""


class FlagAdmin(BaseAdmin):
    actions = [enable_for_all, disable_for_all, delete_individually]
    list_display = ('name', 'note', 'everyone', 'percent', 'superusers',
                    'staff', 'authenticated', 'languages')
    list_filter = ('everyone', 'superusers', 'staff', 'authenticated')
    raw_id_fields = ('users', )
    ordering = ('-id',)

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'users':
            kwargs.pop('request', None)
            kwargs['widget'] = \
                InformativeManyToManyRawIdWidget(db_field.remote_field,
                                                 self.admin_site,
                                                 using=kwargs.get("using"))
            return db_field.formfield(**kwargs)
        return super().formfield_for_dbfield(db_field, **kwargs)


@admin.action(
    description=_('Enable selected switches'),
    permissions=('change',),
)
def enable_switches(ma, request, qs):
    for switch in qs:
        _add_log_entry(request.user, switch, "on", CHANGE)
        switch.active = True
        switch.save()


@admin.action(
    description=_('Disable selected switches'),
    permissions=('change',),
)
def disable_switches(ma, request, qs):
    for switch in qs:
        _add_log_entry(request.user, switch, "off", CHANGE)
        switch.active = False
        switch.save()


class SwitchAdmin(BaseAdmin):
    actions = [enable_switches, disable_switches, delete_individually]
    list_display = ('name', 'active', 'note', 'created', 'modified')
    list_filter = ('active',)
    ordering = ('-id',)


class SampleAdmin(BaseAdmin):
    actions = [delete_individually]
    list_display = ('name', 'percent', 'note', 'created', 'modified')
    ordering = ('-id',)


if get_setting('ENABLE_ADMIN_PAGES'):
    admin.site.register(Flag, FlagAdmin)
    admin.site.register(Sample, SampleAdmin)
    admin.site.register(Switch, SwitchAdmin)
