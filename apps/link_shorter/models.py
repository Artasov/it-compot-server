from django.conf import settings
from django.db import models
from django.urls import reverse


class ShortLink(models.Model):
    original_url = models.URLField()
    short_code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_url

    def get_short_url(self):
        return f"http{'s' if settings.HTTPS else ''}://" \
               f"{settings.MAIN_DOMAIN}{':8000' if settings.DEV else ''}" \
               f"{reverse('link_shorter:redirect_to_full_link', kwargs={'short_code': self.short_code})}"
