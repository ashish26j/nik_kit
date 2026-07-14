"""Public (M02) read serializers. No write serializers here — authoring is Django admin."""
from rest_framework import serializers

from .models import CustomizationGroup, CustomizationOption, Recipe, Section


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "name", "slug", "sort_order"]


def _abs(request, url):
    return request.build_absolute_uri(url) if request else url


class RecipeListSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(read_only=True)
    is_orderable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "price",
            "thumbnail",
            "display_status",
            "is_available",
            "is_orderable",
            "is_sweet",
        ]

    def get_thumbnail(self, obj):
        first = obj.media.filter(kind="IMAGE").first()
        return first.resolved_url(self.context.get("request")) if first else None


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizationOption
        fields = ["id", "label", "price_delta", "is_default"]


class GroupSerializer(serializers.ModelSerializer):
    group_id = serializers.IntegerField(source="id", read_only=True)
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = CustomizationGroup
        fields = ["group_id", "name", "kind", "select_type", "is_required", "options"]


class RecipeDetailSerializer(serializers.ModelSerializer):
    section = serializers.CharField(source="section.name", read_only=True)
    media = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(read_only=True)
    is_orderable = serializers.BooleanField(read_only=True)
    chef_style = serializers.SerializerMethodField()
    customization = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "section",
            "name",
            "price",
            "description",
            "media",
            "is_sweet",
            "default_accompaniment",
            "display_status",
            "is_available",
            "is_orderable",
            "chef_style",
            "customization",
        ]

    def get_chef_style(self, obj):
        # M02 R4a — present only when the recipe has a chef-style link set.
        if obj.chef_style_url:
            return {"platform": obj.chef_style_platform, "url": obj.chef_style_url}
        return None

    def get_media(self, obj):
        request = self.context.get("request")
        return [
            {"kind": m.kind, "url": m.resolved_url(request), "caption": m.caption}
            for m in obj.media.all()
        ]

    def get_customization(self, obj):
        groups = [
            rc.group
            for rc in obj.recipe_customizations.select_related("group").all()
        ]
        return GroupSerializer(groups, many=True, context=self.context).data
