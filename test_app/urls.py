from django.urls import include, path
from django.contrib import admin
from django.http import HttpResponseNotFound, HttpResponseServerError

from test_app import views


def handler404(r, exception=None):
    return HttpResponseNotFound()


def handler500(r, exception=None):
    return HttpResponseServerError()


admin.autodiscover()

urlpatterns = [
    path('flag_in_view', views.flag_in_view, name='flag_in_view'),
    path('flag_in_view_readonly', views.flag_in_view_readonly, name='flag_in_view_readonly'),
    path('switch-on', views.switched_view),
    path('switch-streaming', views.switched_streaming_view),
    path('switch-off', views.switched_off_view),
    path('flag-on', views.flagged_view),
    path('flag-streaming', views.flagged_streaming_view),
    path('foo_view', views.foo_view, name='foo_view'),
    path('foo_view_with_args/<int:some_number>/', views.foo_view_with_args, name='foo_view_with_args'),
    path('switched_view_with_valid_redirect',
         views.switched_view_with_valid_redirect),
    path('switched_view_with_valid_url_name',
         views.switched_view_with_valid_url_name),
    path('switched_view_with_args_with_valid_redirect/<int:some_number>/',
         views.switched_view_with_args_with_valid_redirect),
    path('switched_view_with_args_with_valid_url_name/<int:some_number>/',
         views.switched_view_with_args_with_valid_url_name),
    path('switched_view_with_invalid_redirect',
         views.switched_view_with_invalid_redirect),
    path('flagged_view_with_valid_redirect',
         views.flagged_view_with_valid_redirect),
    path('flagged_view_with_valid_url_name',
         views.flagged_view_with_valid_url_name),
    path('flagged_view_with_args_with_valid_redirect/<int:some_number>/',
         views.flagged_view_with_args_with_valid_redirect),
    path('flagged_view_with_args_with_valid_url_name/<int:some_number>/',
         views.flagged_view_with_args_with_valid_url_name),
    path('flagged_view_with_invalid_redirect',
         views.flagged_view_with_invalid_redirect),
    path('flag-off', views.flagged_off_view),
    path('', include('waffle.urls')),
    path('admin/', admin.site.urls),
]
