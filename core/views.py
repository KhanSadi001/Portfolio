import json
import re

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Count, F
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from . import game
from .forms import ContactForm
from .middleware import BOT_HINTS
from .models import Post, PostLike, Project, Score
from .utils import github_repos, rate_limited, send_contact_email, visitor_id


def _with_github(projects):
    repos = github_repos()
    for p in projects:
        p.gh = repos.get(p.github_repo.lower()) if p.github_repo else None
    return projects


# ---- pages ------------------------------------------------------------------

def home(request):
    featured = _with_github(list(Project.objects.filter(featured=True)[:3]))
    return render(request, "core/home.html", {"featured": featured, "nav": "home"})


def about(request):
    return render(request, "core/about.html", {"nav": "about"})


def projects(request):
    items = _with_github(list(Project.objects.all()))
    counts = {c: 0 for c, _ in Project.Category.choices}
    for p in items:
        counts[p.category] += 1
    filters = [("all", "All", len(items))] + [
        (value, label, counts[value]) for value, label in Project.Category.choices if counts[value]
    ]
    return render(request, "core/projects.html", {"projects": items, "filters": filters, "nav": "projects"})


def _posts_with_likes(request, qs):
    me = visitor_id(request)
    posts = list(qs.annotate(like_count=Count("likes")))
    liked = set(PostLike.objects.filter(visitor=me, post__in=posts).values_list("post_id", flat=True))
    for p in posts:
        p.liked = p.id in liked
    return posts


@ensure_csrf_cookie
def blog(request):
    posts = _posts_with_likes(request, Post.objects.filter(is_published=True))
    return render(request, "core/blog.html", {"posts": posts, "nav": "blog"})


@ensure_csrf_cookie
def post_detail(request, slug):
    posts = _posts_with_likes(request, Post.objects.filter(is_published=True, slug=slug))
    if not posts:
        raise Http404
    return render(request, "core/post.html", {"post": posts[0], "nav": "blog"})


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if rate_limited(request, "contact", limit=3, window_seconds=600):
            form.is_valid()
            form.add_error(None, "You've sent a few messages already. Try again in 10 minutes.")
        elif form.is_valid():
            message = form.save()
            if send_contact_email(message):
                type(message).objects.filter(pk=message.pk).update(emailed=True)
            messages.success(request, "Message sent. I'll reply to your email soon.")
            return redirect("contact")
    else:
        form = ContactForm()
    return render(request, "core/contact.html", {"form": form, "nav": "contact"})


@ensure_csrf_cookie
def play(request):
    return render(request, "core/play.html", {
        "nav": "play",
        "round_seconds": game.ROUND_SECONDS,
        "levels": game.LEVELS,
    })


@require_GET
def go(request, slug):
    """Count a click on a project link, then send the visitor on. Only stored URLs, so no open redirect."""
    project = get_object_or_404(Project, slug=slug)
    ua = request.META.get("HTTP_USER_AGENT", "").lower()
    if not any(h in ua for h in BOT_HINTS):
        Project.objects.filter(pk=project.pk).update(clicks=F("clicks") + 1)
    return HttpResponseRedirect(project.url)


# ---- JSON API -----------------------------------------------------------------

def _json_body(request):
    try:
        return json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return None


@require_POST
def api_like(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    if rate_limited(request, "like", limit=30, window_seconds=3600):
        return JsonResponse({"error": "Too many likes for now. Try again later."}, status=429)
    try:
        with transaction.atomic():
            PostLike.objects.create(post=post, visitor=visitor_id(request))
    except IntegrityError:
        pass  # already liked; the count below is still correct
    return JsonResponse({"count": post.likes.count(), "liked": True})


@require_POST
@never_cache
def api_game_start(request):
    if rate_limited(request, "game-start", limit=60, window_seconds=3600):
        return JsonResponse({"error": "Too many rounds started. Take a short break."}, status=429)
    return JsonResponse({"token": game.new_round_token(), "seconds": game.ROUND_SECONDS})


NAME_RE = re.compile(r"^[A-Za-z0-9 _.\-]{1,20}$")


@require_POST
@never_cache
def api_game_submit(request):
    data = _json_body(request)
    if data is None:
        return JsonResponse({"error": "Send JSON."}, status=400)
    name = str(data.get("name", "")).strip()
    if not NAME_RE.match(name):
        return JsonResponse({"error": "Use 1–20 letters, numbers, spaces, dots, dashes or underscores."}, status=400)
    if rate_limited(request, "game-submit", limit=15, window_seconds=3600):
        return JsonResponse({"error": "Too many scores submitted. Try again later."}, status=429)
    try:
        score = game.validate_round(str(data.get("token", "")), data.get("solved"))
    except game.RoundError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    entry = Score.objects.create(name=name, score=score, solved=data["solved"], visitor=visitor_id(request))
    rank = Score.objects.filter(hidden=False, score__gt=score).count() + 1
    return JsonResponse({"score": score, "rank": rank, "id": entry.id, "leaderboard": _leaderboard()})


def _leaderboard():
    return [
        {"name": s.name, "score": s.score, "solved": s.solved}
        for s in Score.objects.filter(hidden=False)[:10]
    ]


@require_GET
@never_cache
def api_leaderboard(request):
    return JsonResponse({"leaderboard": _leaderboard()})
