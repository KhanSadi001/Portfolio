import hashlib
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.cache import cache

log = logging.getLogger(__name__)


def client_ip(request):
    # Vercel puts the real client IP first in X-Forwarded-For.
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def visitor_id(request):
    """A salted hash identifying a visitor without storing their IP address."""
    raw = f"{client_ip(request)}|{request.META.get('HTTP_USER_AGENT', '')[:200]}|{settings.SECRET_KEY}"
    return hashlib.sha256(raw.encode()).hexdigest()


def rate_limited(request, bucket, limit, window_seconds):
    """Return True if this visitor has gone over `limit` actions in the window."""
    key = f"rl:{bucket}:{visitor_id(request)[:32]}"
    if cache.add(key, 1, window_seconds):
        return False
    try:
        count = cache.incr(key)
    except ValueError:  # expired between add() and incr()
        cache.set(key, 1, window_seconds)
        return False
    return count > limit


def github_repos():
    """Public repos for the configured user, cached for an hour in the database cache.

    Returns {repo_name_lower: {"stars", "language", "pushed_at"}}; an empty dict if GitHub is unreachable.
    """
    key = f"github:repos:{settings.GITHUB_USERNAME}"
    data = cache.get(key)
    if data is not None:
        return data

    url = f"https://api.github.com/users/{settings.GITHUB_USERNAME}/repos?per_page=100&sort=pushed"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "sadi-portfolio"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=4) as resp:
            repos = json.load(resp)
        data = {
            r["name"].lower(): {
                "stars": r.get("stargazers_count", 0),
                "language": r.get("language") or "",
                "pushed_at": (r.get("pushed_at") or "")[:10],
            }
            for r in repos
        }
        cache.set(key, data, 60 * 60)
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        log.warning("GitHub fetch failed: %s", exc)
        data = {}
        cache.set(key, data, 60 * 5)  # retry in 5 minutes rather than on every request
    return data


def send_contact_email(message):
    """Email a new contact message via Resend, if an API key is configured."""
    if not settings.RESEND_API_KEY:
        return False
    payload = {
        "from": settings.CONTACT_FROM_EMAIL,
        "to": [settings.CONTACT_TO_EMAIL],
        "reply_to": message.email,
        "subject": f"Portfolio message from {message.name}",
        "text": f"From: {message.name} <{message.email}>\n\n{message.body}",
    }
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "sadi-portfolio",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError) as exc:
        log.warning("Contact email failed: %s", exc)
        return False
