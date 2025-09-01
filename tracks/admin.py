from django.contrib import admin

from .models import Track, Inquiry, Genre


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ("title", "is_featured", "view_count", "order_clicks", "created_at")
    list_filter = ("is_featured", "genres")
    search_fields = ("title", "description", "youtube_url")
    ordering = ("-view_count", "-order_clicks", "-created_at")
    readonly_fields = ("view_count", "order_clicks")
    exclude = ("genres",)  # ← поле не показуємо
    # filter_horizontal = ("genres",)  # можна прибрати


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "license_type", "track", "created_at", "status")
    list_filter = ("license_type", "status", "created_at")
    search_fields = ("name", "contact", "message")
