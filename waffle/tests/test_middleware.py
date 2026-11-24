from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from waffle.middleware import WaffleMiddleware


get = RequestFactory().get('/foo')


def test_set_cookies():
    get.waffles = {'foo': [True, False], 'bar': [False, False]}
    resp = HttpResponse()
    assert 'dwf_foo' not in resp.cookies
    assert 'dwf_bar' not in resp.cookies

    resp = WaffleMiddleware().process_response(get, resp)
    assert 'dwf_foo' in resp.cookies
    assert 'dwf_bar' in resp.cookies

    assert 'True' == resp.cookies['dwf_foo'].value
    assert 'False' == resp.cookies['dwf_bar'].value


def test_rollout_cookies():
    get.waffles = {'foo': [True, True],
                   'bar': [False, True],
                   'baz': [True, False],
                   'qux': [False, False]}
    resp = HttpResponse()
    resp = WaffleMiddleware().process_response(get, resp)
    for k in get.waffles:
        cookie = f'dwf_{k}'
        assert cookie in resp.cookies
        assert str(get.waffles[k][0]) == resp.cookies[cookie].value
        if get.waffles[k][1]:
            assert bool(resp.cookies[cookie]['max-age']) == get.waffles[k][0]
        else:
            assert resp.cookies[cookie]['max-age']


def test_testing_cookies():
    get.waffles = {}
    get.waffle_tests = {'foo': True, 'bar': False}
    resp = HttpResponse()
    resp = WaffleMiddleware().process_response(get, resp)
    for k in get.waffle_tests:
        cookie = f'dwft_{k}'
        assert str(get.waffle_tests[k]) == resp.cookies[cookie].value
        assert not resp.cookies[cookie]['max-age']


class TestCookieSecureTests(SimpleTestCase):
    def process(self):
        request = RequestFactory().get('/foo')
        request.waffle_tests = {'foo': True}
        return WaffleMiddleware(lambda r: HttpResponse()).process_response(
            request, HttpResponse())

    def test_testing_cookie_secure_by_default(self):
        resp = self.process()
        assert resp.cookies['dwft_foo']['secure'] is True

    @override_settings(WAFFLE_SECURE=False)
    def test_testing_cookie_secure_opt_out(self):
        resp = self.process()
        assert not resp.cookies['dwft_foo']['secure']
