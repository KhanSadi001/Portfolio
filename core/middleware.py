from django.conf import settings
from django.db import DatabaseError
from django.db.models import F
from django.utils import timezone

from .models import PageView

TRACKED_PREFIXES = ("/static/", "/api/", "/go/", "/favicon")
BOT_HINTS = ("bot", "spider", "crawl", "slurp", "preview", "monitor", "curl", "python-requests")


class PageViewMiddleware:
    """Counts successful page views per day. No cookies, no IPs, no third parties."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path
        ua = request.META.get("HTTP_USER_AGENT", "").lower()
        if (
            request.method == "GET"
            and response.status_code == 200
            and not path.startswith(TRACKED_PREFIXES)
            and not path.startswith("/" + settings.ADMIN_PATH)
            and not any(hint in ua for hint in BOT_HINTS)
        ):
            try:
                day = timezone.localdate()
                updated = PageView.objects.filter(path=path[:200], day=day).update(count=F("count") + 1)
                if not updated:
                    obj, created = PageView.objects.get_or_create(path=path[:200], day=day, defaults={"count": 1})
                    if not created:
                        PageView.objects.filter(pk=obj.pk).update(count=F("count") + 1)
            except DatabaseError:
                pass  # never break a page because stats failed
        return response
