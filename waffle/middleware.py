from asgiref.sync import iscoroutinefunction, markcoroutinefunction

from django.http import HttpRequest, HttpResponse
from django.utils.encoding import smart_str

from waffle.utils import get_setting


class WaffleMiddleware:
    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        if get_response is None:
            raise ValueError("get_response must be provided.")
        self.get_response = get_response
        self.is_async = iscoroutinefunction(get_response)
        if self.is_async:
            markcoroutinefunction(self)
        super().__init__()

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

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if self.is_async:
            return self.__acall__(request)
        response = self.get_response(request)
        return self.process_response(request, response)

    async def __acall__(self, request: HttpRequest) -> HttpResponse:
        response = await self.get_response(request)
        return self.process_response(request, response)
