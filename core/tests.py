import json
import time
from unittest import mock

from django.core import signing
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from . import game
from .models import Message, PageView, Post, PostLike, Project, Score


@mock.patch("core.views.github_repos", lambda: {})
class PageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("createcachetable", verbosity=0)

    def setUp(self):
        cache.clear()

    def test_pages_load(self):
        for name in ["home", "about", "projects", "blog", "contact", "play"]:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200, name)
            self.assertIn("Content-Security-Policy", r.headers)

    def test_seeded_content(self):
        self.assertEqual(Project.objects.count(), 10)
        self.assertEqual(Project.objects.filter(featured=True).count(), 3)
        self.assertEqual(Post.objects.count(), 2)

    def test_csp_blocks_inline_scripts(self):
        csp = self.client.get("/").headers["Content-Security-Policy"]
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("unsafe-inline", csp)

    def test_page_views_counted(self):
        self.client.get("/")
        self.client.get("/")
        self.assertEqual(PageView.objects.get(path="/").count, 2)

    def test_go_counts_and_redirects_only_to_stored_url(self):
        p = Project.objects.first()
        r = self.client.get(reverse("go", args=[p.slug]))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], p.url)
        p.refresh_from_db()
        self.assertEqual(p.clicks, 1)
        self.assertEqual(self.client.get("/go/not-a-project/").status_code, 404)

    def test_markdown_is_sanitized(self):
        post = Post.objects.create(slug="x", title="T", body="Hi <script>alert(1)</script> [a](javascript:alert(1))")
        html = post.body_html()
        self.assertNotIn("<script", html)
        self.assertNotIn("javascript:", html)


class ContactTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("createcachetable", verbosity=0)

    def setUp(self):
        cache.clear()

    def data(self, age=10, **extra):
        d = {"name": "Ali", "email": "ali@example.com", "body": "Hello, I'd like to work together.",
             "website": "", "ts": signing.dumps(time.time() - age, salt="contact-ts")}
        d.update(extra)
        return d

    def test_valid_message_saved(self):
        r = self.client.post(reverse("contact"), self.data())
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Message.objects.count(), 1)

    def test_honeypot_rejected(self):
        self.client.post(reverse("contact"), self.data(website="spam.com"))
        self.assertEqual(Message.objects.count(), 0)

    def test_too_fast_rejected(self):
        self.client.post(reverse("contact"), self.data(age=0))
        self.assertEqual(Message.objects.count(), 0)

    def test_forged_timestamp_rejected(self):
        self.client.post(reverse("contact"), self.data(ts="12345"))
        self.assertEqual(Message.objects.count(), 0)

    def test_rate_limit(self):
        for _ in range(5):
            self.client.post(reverse("contact"), self.data())
        self.assertEqual(Message.objects.count(), 3)


class LikeTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("createcachetable", verbosity=0)

    def setUp(self):
        cache.clear()

    def test_one_like_per_visitor(self):
        post = Post.objects.first()
        url = reverse("api_like", args=[post.slug])
        self.client.post(url)
        r = self.client.post(url)
        self.assertEqual(r.json()["count"], 1)
        self.assertEqual(PostLike.objects.count(), 1)

    def test_like_requires_post(self):
        self.assertEqual(self.client.get(reverse("api_like", args=[Post.objects.first().slug])).status_code, 405)


class GameTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("createcachetable", verbosity=0)

    def setUp(self):
        cache.clear()

    def old_token(self, seconds_ago=61):
        return signing.dumps({"sid": f"s{time.time()}", "t": time.time() - seconds_ago}, salt=game.SALT)

    def submit(self, token, solved, name="Tester"):
        return self.client.post(reverse("api_game_submit"), json.dumps({"token": token, "solved": solved, "name": name}),
                                content_type="application/json")

    def test_points(self):
        self.assertEqual(game.points_for(0), 0)
        self.assertEqual(game.points_for(5), 50)
        self.assertEqual(game.points_for(6), 70)
        self.assertEqual(game.points_for(13), 5 * 10 + 7 * 20 + 30)

    def test_start_returns_token(self):
        r = self.client.post(reverse("api_game_start"))
        self.assertIn("token", r.json())

    def test_valid_submission_scored_by_server(self):
        r = self.submit(self.old_token(), 6)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["score"], 70)
        self.assertEqual(Score.objects.get().score, 70)

    def test_early_submission_rejected(self):
        self.assertEqual(self.submit(self.old_token(seconds_ago=5), 3).status_code, 400)

    def test_impossible_score_rejected(self):
        self.assertEqual(self.submit(self.old_token(), game.MAX_SOLVED + 1).status_code, 400)

    def test_token_cannot_be_reused(self):
        t = self.old_token()
        self.assertEqual(self.submit(t, 3).status_code, 200)
        self.assertEqual(self.submit(t, 3).status_code, 400)

    def test_forged_token_rejected(self):
        self.assertEqual(self.submit("not-a-token", 3).status_code, 400)

    def test_bad_name_rejected(self):
        self.assertEqual(self.submit(self.old_token(), 3, name="<img src=x>").status_code, 400)

    def test_hidden_scores_not_on_leaderboard(self):
        Score.objects.create(name="Cheater", score=9999, solved=1, visitor="x", hidden=True)
        board = self.client.get(reverse("api_leaderboard")).json()["leaderboard"]
        self.assertNotIn("Cheater", [r["name"] for r in board])
