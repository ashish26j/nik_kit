"""Django admin = the owner's P1 authoring surface (interim; custom console = M09)."""
from django.contrib import admin

from .models import (
    CustomizationGroup,
    CustomizationOption,
    Recipe,
    RecipeCustomization,
    RecipeMedia,
    Section,
)


class RecipeMediaInline(admin.TabularInline):
    model = RecipeMedia
    extra = 1
    fields = ("kind", "file", "url", "caption", "sort_order")


class RecipeCustomizationInline(admin.TabularInline):
    model = RecipeCustomization
    extra = 1
    autocomplete_fields = ["group"]


class CustomizationOptionInline(admin.TabularInline):
    model = CustomizationOption
    extra = 2


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "price", "display_status", "is_sweet")
    list_filter = ("section", "display_status", "is_sweet")
    list_editable = ("price", "display_status")
    search_fields = ("name", "description")
    inlines = [RecipeMediaInline, RecipeCustomizationInline]


@admin.register(CustomizationGroup)
class CustomizationGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "select_type", "is_required", "sort_order")
    list_editable = ("sort_order",)
    search_fields = ("name",)
    inlines = [CustomizationOptionInline]
