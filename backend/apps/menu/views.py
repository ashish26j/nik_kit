"""Public browse endpoints (M02). All read-only, no auth (explore-first)."""
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Recipe, Section
from .serializers import (
    RecipeDetailSerializer,
    RecipeListSerializer,
    SectionSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def sections(request):
    qs = Section.objects.filter(is_active=True)
    return Response(SectionSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def section_recipes(request, slug):
    section = get_object_or_404(Section, slug=slug, is_active=True)
    # Show AVAILABLE + UNAVAILABLE (greyed), exclude HIDDEN (M02 R1).
    qs = section.recipes.exclude(display_status=Recipe.Display.HIDDEN)
    q = request.query_params.get("q")
    if q:
        qs = qs.filter(name__icontains=q)
    data = RecipeListSerializer(qs, many=True, context={"request": request}).data
    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def recipe_detail(request, pk):
    recipe = get_object_or_404(
        Recipe.objects.exclude(display_status=Recipe.Display.HIDDEN), pk=pk
    )
    return Response(RecipeDetailSerializer(recipe, context={"request": request}).data)
