from django.contrib import admin

from .models import ChefProfile, SocialLink


class SocialLinkInline(admin.TabularInline):
    model = SocialLink
    extra = 1


@admin.register(ChefProfile)
class ChefProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "tagline", "updated_at")
    inlines = [SocialLinkInline]

    def has_add_permission(self, request):
        # Singleton — only one profile row allowed.
        return not ChefProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
