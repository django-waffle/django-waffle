from unittest import skipUnless

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.template import Template
from django.template.base import VariableNode
from django.test import RequestFactory

from test_app import views
from waffle.middleware import WaffleMiddleware
from waffle.tests.base import TestCase
from waffle.testutils import override_switch, override_flag, override_sample


def get():
    request = RequestFactory().get('/foo')
    request.user = AnonymousUser()
    return request


def get_response(request):
    return 'hello'


def process_request(request, view):
    response = view(request)
    return WaffleMiddleware(get_response).process_response(request, response)


class WaffleTemplateTests(TestCase):
    def test_django_tags(self):
        request = get()
        response = process_request(request, views.flag_in_django)
        self.assertContains(response, 'flag off')
        self.assertContains(response, 'switch off')
        self.assertContains(response, 'sample')
        self.assertContains(response, 'flag_var off')
        self.assertContains(response, 'switch_var off')
        self.assertContains(response, 'sample_var')
        self.assertContains(response, 'window.waffle =')
        self.assertContains(response, 'flag_is_active off')
        self.assertContains(response, 'switch_is_active off')
        self.assertContains(response, 'sample_is_active off')

    @override_flag("flag", active=True)
    @override_sample("sample", active=True)
    @override_switch("switch", active=True)
    def test_django_tags_enabled(self):
        request = get()
        response = process_request(request, views.flag_in_django)
        self.assertContains(response, 'flag on')
        self.assertContains(response, 'switch on')
        self.assertContains(response, 'sample on')
        self.assertNotContains(response, 'flag off')
        self.assertNotContains(response, 'switch off')
        self.assertNotContains(response, 'sample off')
        self.assertContains(response, 'window.waffle =')
        self.assertContains(response, 'flag_is_active on')
        self.assertContains(response, 'switch_is_active on')
        self.assertContains(response, 'sample_is_active on')

    def test_get_nodes_by_type(self):
        """WaffleNode.get_nodes_by_type() should find all child nodes."""
        test_template = Template(
            '{% load waffle_tags %}'
            '{% switch "x" %}'
            '{{ a }}'
            '{% else %}'
            '{{ b }}'
            '{% endswitch %}'
        )
        children = test_template.nodelist.get_nodes_by_type(VariableNode)
        self.assertEqual(len(children), 2)

    def test_no_request_context(self):
        """Switches and Samples shouldn't require a request context."""
        request = get()
        content = process_request(request, views.no_request_context)
        assert 'switch off' in content
        assert 'sample' in content

    @skipUnless(
        settings.JINJA_INSTALLED,
        "django-jinja is currently unmaintained and uncompatible with django >= 3.0"
    )
    def test_jinja_tags(self):
        request = get()
        response = process_request(request, views.flag_in_jinja)
        self.assertContains(response, 'flag off')
        self.assertContains(response, 'switch off')
        self.assertContains(response, 'sample')
        self.assertContains(response, 'window.waffle =')
