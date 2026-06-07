from __future__ import annotations

import asyncio
from functools import wraps, WRAPPER_ASSIGNMENTS
from typing import Any, Callable

from django.http import Http404, HttpRequest, HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch

from waffle import aflag_is_active, aswitch_is_active, flag_is_active, switch_is_active


def waffle_flag(
    flag_name: str, redirect_to: Callable | str | None = None,
) -> Callable[[Callable[[HttpRequest], HttpResponse]], Callable[[HttpRequest], HttpResponse]]:
    def decorator(view: Callable[[HttpRequest], HttpResponse]) -> Callable[[HttpRequest], HttpResponse]:
        if asyncio.iscoroutinefunction(view):
            @wraps(view, assigned=WRAPPER_ASSIGNMENTS)
            async def _async_wrapped_view(request, *args, **kwargs):
                if flag_name.startswith('!'):
                    active = not await aflag_is_active(request, flag_name[1:])
                else:
                    active = await aflag_is_active(request, flag_name)

                if not active:
                    response_to_redirect_to = get_response_to_redirect(redirect_to, *args, **kwargs)
                    if response_to_redirect_to:
                        return response_to_redirect_to
                    else:
                        raise Http404

                return await view(request, *args, **kwargs)
            return _async_wrapped_view
        else:
            @wraps(view, assigned=WRAPPER_ASSIGNMENTS)
            def _wrapped_view(request, *args, **kwargs):
                if flag_name.startswith('!'):
                    active = not flag_is_active(request, flag_name[1:])
                else:
                    active = flag_is_active(request, flag_name)

                if not active:
                    response_to_redirect_to = get_response_to_redirect(redirect_to, *args, **kwargs)
                    if response_to_redirect_to:
                        return response_to_redirect_to
                    else:
                        raise Http404

                return view(request, *args, **kwargs)
            return _wrapped_view
    return decorator


def waffle_switch(
    switch_name: str, redirect_to: Callable | str | None = None,
) -> Callable[[Callable[[HttpRequest], HttpResponse]], Callable[[HttpRequest], HttpResponse]]:
    def decorator(view: Callable[[HttpRequest], HttpResponse]) -> Callable[[HttpRequest], HttpResponse]:
        if asyncio.iscoroutinefunction(view):
            @wraps(view, assigned=WRAPPER_ASSIGNMENTS)
            async def _async_wrapped_view(request, *args, **kwargs):
                if switch_name.startswith('!'):
                    active = not await aswitch_is_active(switch_name[1:])
                else:
                    active = await aswitch_is_active(switch_name)

                if not active:
                    response_to_redirect_to = get_response_to_redirect(redirect_to, *args, **kwargs)
                    if response_to_redirect_to:
                        return response_to_redirect_to
                    else:
                        raise Http404

                return await view(request, *args, **kwargs)
            return _async_wrapped_view
        else:
            @wraps(view, assigned=WRAPPER_ASSIGNMENTS)
            def _wrapped_view(request, *args, **kwargs):
                if switch_name.startswith('!'):
                    active = not switch_is_active(switch_name[1:])
                else:
                    active = switch_is_active(switch_name)

                if not active:
                    response_to_redirect_to = get_response_to_redirect(redirect_to, *args, **kwargs)
                    if response_to_redirect_to:
                        return response_to_redirect_to
                    else:
                        raise Http404

                return view(request, *args, **kwargs)
            return _wrapped_view
    return decorator


def get_response_to_redirect(
    view: Callable | str | None, *args: Any, **kwargs: Any,
) -> HttpResponseRedirect | HttpResponsePermanentRedirect | None:
    try:
        return redirect(reverse(view, args=args, kwargs=kwargs)) if view else None
    except NoReverseMatch:
        return None
