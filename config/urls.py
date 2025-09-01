from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.generic import TemplateView
from tracks.sitemaps import TrackSitemap

sitemaps = {
    "tracks": TrackSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tracks.urls')),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", TemplateView.as_view(
        template_name="robots.txt", content_type="text/plain"
    )),
]
