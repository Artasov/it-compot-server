from django.contrib import admin

from apps.link_shorter.models import ShortLink


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_short_url', 'original_url', 'created_at')

