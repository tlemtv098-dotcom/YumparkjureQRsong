"""
URL configuration for yum_jukebox project.
"""
import os

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.http import FileResponse, Http404


def _media_view(request, path):
    """Serve an uploaded file, but only from inside MEDIA_ROOT."""
    media_root = os.path.abspath(settings.MEDIA_ROOT)
    full_path = os.path.abspath(os.path.join(media_root, path))
    try:
        inside_media_root = os.path.commonpath([media_root, full_path]) == media_root
    except ValueError:
        # Raised when the paths sit on different drives or mix relative and
        # absolute forms. Deny rather than let it become a 500.
        inside_media_root = False
    if not inside_media_root:
        raise Http404("Invalid media path")
    if not os.path.isfile(full_path):
        raise Http404("Media file not found")
    return FileResponse(open(full_path, "rb"))


urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^media/(?P<path>.*)$", _media_view),
    path("", include("music.urls")),
]
