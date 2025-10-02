from typing import Optional
from django import template
from django.http import HttpRequest
from django.template.base import VariableDoesNotExist

from waffle import (
    flag_is_active as waffle_flag_is_active,
    sample_is_active as waffle_sample_is_active,
    switch_is_active as waffle_switch_is_active
    )
from waffle.views import _generate_waffle_js


register = template.Library()


class WaffleNode(template.Node):
    child_nodelists = ('nodelist_true', 'nodelist_false')

    def __init__(self, nodelist_true, nodelist_false, condition, name,
                 compiled_name):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.condition = condition
        self.name = name
        self.compiled_name = compiled_name

    def __repr__(self):
        return f'<Waffle node: {self.name}>'

    def __iter__(self):
        yield from self.nodelist_true
        yield from self.nodelist_false

    def render(self, context):
        try:
            name = self.compiled_name.resolve(context)
        except VariableDoesNotExist:
            name = self.name
        if not name:
            name = self.name
        if self.condition(context.get('request', None), name):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)

    @classmethod
    def handle_token(cls, parser, token, kind, condition):
        bits = token.split_contents()
        if len(bits) < 2:
            raise template.TemplateSyntaxError(f"{bits[0]!r} tag requires an argument")

        name = bits[1]
        compiled_name = parser.compile_filter(name)

        nodelist_true = parser.parse(('else', f'end{kind}'))
        token = parser.next_token()
        if token.contents == 'else':
            nodelist_false = parser.parse((f'end{kind}',))
            parser.delete_first_token()
        else:
            nodelist_false = template.NodeList()

        return cls(nodelist_true, nodelist_false, condition,
                   name, compiled_name)


@register.tag
def flag(parser, token):
    return WaffleNode.handle_token(parser, token, 'flag', waffle_flag_is_active)


@register.tag
def switch(parser, token):
    return WaffleNode.handle_token(parser, token, 'switch', lambda request, name: waffle_switch_is_active(name))


@register.tag
def sample(parser, token):
    return WaffleNode.handle_token(parser, token, 'sample', lambda request, name: waffle_sample_is_active(name))


class InlineWaffleJSNode(template.Node):
    def render(self, context):
        return _generate_waffle_js(context['request'])


@register.tag
def wafflejs(parser, token):
    return InlineWaffleJSNode()


@register.filter(name="switch_is_active")  # type: ignore[misc]
def switch_is_active(switch_name: str) -> bool:
    """
    This template filter works like the switch tag, but you can use it within
    if statement conditions in Django templates. Example: `{% if "switch_name"|switch_is_active %}`.
    """
    return waffle_switch_is_active(switch_name)


@register.simple_tag  # type: ignore[misc]
def flag_is_active(flag_name: str, request: HttpRequest, read_only: bool = False) -> Optional[bool]:
    """
    This template filter works like the flag tag, but you can use it within
    if statement conditions in Django templates. Example:
    `{% flag_is_active "flag_name" request True as is_flag_active %}`
    `{% if is_flag_active %}`.
    """
    return waffle_flag_is_active(request=request, flag_name=flag_name, read_only=read_only)


@register.filter(name="sample_is_active")  # type: ignore[misc]
def sample_is_active(sample_name: str) -> bool:
    """
    This template filter works like the sample tag, but you can use it within if
    statement conditions in Django templates. Example: `{% if "sample_name"|sample_is_active %}`.
    """
    return waffle_sample_is_active(sample_name)
