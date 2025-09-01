from django.contrib.sitemaps import Sitemap

from .models import Track


class TrackSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Track.objects.all()

    def location(self, obj):
        # якщо вже є get_absolute_url у моделі — можна лишити тільки return obj
        return f"/track/{obj.slug}/"
