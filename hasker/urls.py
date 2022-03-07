from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import RedirectView

from questions import views

urlpatterns = [
    path('', views.index, name='index'),
    path('questions/', include('questions.urls')),
    path('users/', include('users.urls')),
    path('admin/', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("img/favicon.ico")),
    ),
] + (
    static(settings.MEDIA_URL,
           document_root=settings.MEDIA_ROOT) +
    static(settings.STATIC_URL,
           document_root=settings.STATIC_ROOT)
)
urlpatterns += staticfiles_urlpatterns()
