from django.contrib import admin
from django.db.models import Count, Sum

from .models import Message, PageView, Post, Project, Score


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "short_body", "created_at", "is_read", "emailed")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "body")
    readonly_fields = ("name", "email", "body", "created_at", "emailed")
    actions = ["mark_read"]

    @admin.display(description="Message")
    def short_body(self, obj):
        return obj.body[:80]

    @admin.action(description="Mark selected as read")
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    def has_add_permission(self, request):
        return False


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("__str__", "published_at", "is_published", "like_total")
    list_filter = ("is_published",)
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_likes=Count("likes"))

    @admin.display(description="Likes", ordering="_likes")
    def like_total(self, obj):
        return obj._likes


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "year", "featured", "clicks")
    list_filter = ("category", "featured")
    list_editable = ("featured",)
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("clicks",)


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ("day", "path", "count")
    list_filter = ("day", "path")
    date_hierarchy = "day"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data["cl"].queryset
            response.context_data["title"] = f"Page views — {qs.aggregate(t=Sum('count'))['t'] or 0} total in this view"
        except (AttributeError, KeyError):
            pass
        return response

    def has_add_permission(self, request):
        return False


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("name", "score", "solved", "created_at", "hidden")
    list_editable = ("hidden",)
    list_filter = ("hidden",)
    search_fields = ("name",)
