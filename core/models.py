import markdown as md
import nh3
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe


class Project(models.Model):
    class Category(models.TextChoices):
        ML = "ml", "Data science & ML"
        PYTHON = "python", "Python & Django"
        HARDWARE = "hardware", "Hardware"

    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, help_text="Used in the tracking link /go/<slug>/")
    category = models.CharField(max_length=20, choices=Category.choices)
    tag = models.CharField(max_length=40, help_text="Short label, e.g. 'Machine learning'")
    where = models.CharField("Made at", max_length=120, blank=True)
    year = models.PositiveSmallIntegerField()
    description = models.CharField(max_length=200, blank=True)
    url = models.URLField(help_text="Where the button goes (GitHub repo or other page)")
    github_repo = models.CharField(
        max_length=120, blank=True,
        help_text="Repo name on GitHub, e.g. Asteroid-Threat-Predictor. Pulls live stars/language.",
    )
    featured = models.BooleanField(default=False, help_text="Show on the home page (up to 3)")
    order = models.PositiveSmallIntegerField(default=0, help_text="Lower comes first within a year")
    clicks = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["-year", "order", "title"]

    def __str__(self):
        return self.title

    @property
    def is_github(self):
        return "github.com" in self.url


ALLOWED_TAGS = {"p", "a", "strong", "em", "code", "pre", "ul", "ol", "li", "blockquote", "h2", "h3", "br", "hr"}


class Post(models.Model):
    title = models.CharField(max_length=160, blank=True, help_text="Optional. Short posts can skip it.")
    slug = models.SlugField(unique=True)
    body = models.TextField(help_text="Markdown is supported.")
    published_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title or self.body[:60]

    def get_absolute_url(self):
        return reverse("post", args=[self.slug])

    @property
    def is_short(self):
        return not self.title and len(self.body) < 280

    def body_html(self):
        # Render Markdown, then sanitize so nothing in a post can run script.
        html = md.markdown(self.body, extensions=["fenced_code"])
        clean = nh3.clean(html, tags=ALLOWED_TAGS, attributes={"a": {"href", "title"}}, link_rel="noopener nofollow")
        return mark_safe(clean)


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    visitor = models.CharField(max_length=64, help_text="Salted hash, not an IP address")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["post", "visitor"], name="one_like_per_visitor")]


class Message(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    body = models.TextField("Message", max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    emailed = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


class PageView(models.Model):
    """One row per page per day, so the table stays small."""
    path = models.CharField(max_length=200)
    day = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-day", "-count"]
        constraints = [models.UniqueConstraint(fields=["path", "day"], name="one_row_per_path_per_day")]

    def __str__(self):
        return f"{self.path} on {self.day}: {self.count}"


class Score(models.Model):
    name = models.CharField(max_length=20)
    score = models.PositiveIntegerField()
    solved = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    visitor = models.CharField(max_length=64, editable=False)
    hidden = models.BooleanField(default=False, help_text="Hide from the leaderboard")

    class Meta:
        ordering = ["-score", "created_at"]

    def __str__(self):
        return f"{self.name}: {self.score}"
