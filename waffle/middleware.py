from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import smart_str
from waffle.utils import get_setting
from waffle import get_waffle_flag_model

WaffleFlag = get_waffle_flag_model()


class WaffleMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Ensure testing cookie are always set, even if Waffle isn't used"""
        for flag in WaffleFlag.objects.filter(testing=True):
            tc = get_setting("TEST_COOKIE") % flag.name
            if tc in request.GET:
                on = request.GET[tc] == "1"
                if not hasattr(request, "waffle_tests"):
                    request.waffle_tests = {}
                request.waffle_tests[flag.name] = on
        return self.process_response(request, self.get_response(request))

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        secure = get_setting('SECURE')
        max_age = get_setting('MAX_AGE')

        if hasattr(request, 'waffles'):
            for k in request.waffles:
                name = smart_str(get_setting('COOKIE') % k)
                active, rollout = request.waffles[k]
                if rollout and not active:
                    # "Inactive" is a session cookie during rollout mode.
                    age = None
                else:
                    age = max_age
                response.set_cookie(name, value=active, max_age=age,
                                    secure=secure)
        if hasattr(request, 'waffle_tests'):
            for k in request.waffle_tests:
                name = smart_str(get_setting('TEST_COOKIE') % k)
                value = request.waffle_tests[k]
                response.set_cookie(name, value=value)

        return response
