from django.conf import settings
from django.contrib import admin
from django.urls import path

from core import views

admin.site.site_header = "Sadi Khan — site admin"
admin.site.site_title = "Portfolio admin"
admin.site.index_title = "Manage your portfolio"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("projects/", views.projects, name="projects"),
    path("blog/", views.blog, name="blog"),
    path("blog/<slug:slug>/", views.post_detail, name="post"),
    path("contact/", views.contact, name="contact"),
    path("play/", views.play, name="play"),
    path("go/<slug:slug>/", views.go, name="go"),

    path("api/posts/<slug:slug>/like/", views.api_like, name="api_like"),
    path("api/game/start/", views.api_game_start, name="api_game_start"),
    path("api/game/submit/", views.api_game_submit, name="api_game_submit"),
    path("api/game/leaderboard/", views.api_leaderboard, name="api_leaderboard"),

    path(settings.ADMIN_PATH, admin.site.urls),
]
