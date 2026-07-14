"""Idempotent sample data so P1 browse isn't empty. Run: manage.py seed_menu

Images are intentionally omitted — the owner adds real photos via Django admin.
"""
from django.core.management.base import BaseCommand

from apps.menu.models import (
    CustomizationGroup,
    CustomizationOption,
    Recipe,
    RecipeCustomization,
    RecipeMedia,
    Section,
)

SECTIONS = [
    ("Parathas", "parathas", 1, False, [
        ("Aloo Paratha", "60.00", "Stuffed potato flatbread, served with butter & pickle.", "AVAILABLE"),
        ("Paneer Paratha", "80.00", "Cottage-cheese stuffed paratha — rich and soft.", "AVAILABLE"),
        ("Gobi Paratha", "70.00", "Spiced cauliflower stuffed flatbread.", "UNAVAILABLE"),
    ]),
    ("Snacks", "snacks", 2, False, [
        ("Samosa", "20.00", "Crispy fried pastry with spiced potato filling.", "AVAILABLE"),
        ("Kachori", "25.00", "Flaky deep-fried snack with a savoury lentil core.", "AVAILABLE"),
    ]),
    ("Sweets", "sweets", 3, True, [
        ("Gulab Jamun", "40.00", "Soft milk-solid dumplings soaked in rose syrup.", "AVAILABLE"),
        ("Jalebi", "35.00", "Crisp spirals soaked in saffron syrup.", "AVAILABLE"),
    ]),
]


class Command(BaseCommand):
    help = "Seed sections, sample recipes, and customization (idempotent)."

    def handle(self, *args, **options):
        for name, slug, order, is_sweet, recipes in SECTIONS:
            section, _ = Section.objects.get_or_create(
                slug=slug, defaults={"name": name, "sort_order": order}
            )
            for rname, price, desc, status in recipes:
                Recipe.objects.get_or_create(
                    section=section,
                    name=rname,
                    defaults={
                        "price": price,
                        "description": desc,
                        "is_sweet": is_sweet,
                        "display_status": status,
                    },
                )

        # Customization catalog: Spice level (single/required) + Add-ons (multi).
        spice, _ = CustomizationGroup.objects.get_or_create(
            name="Spice level",
            defaults={"kind": "PREPARATION", "select_type": "SINGLE", "is_required": True, "sort_order": 1},
        )
        for label, default in [("Mild", True), ("Medium", False), ("Extra spicy", False)]:
            CustomizationOption.objects.get_or_create(
                group=spice, label=label, defaults={"is_default": default}
            )
        addons, _ = CustomizationGroup.objects.get_or_create(
            name="Add-ons",
            defaults={"kind": "INGREDIENT", "select_type": "MULTI", "is_required": False, "sort_order": 2},
        )
        for label, delta in [("Extra butter", "10.00"), ("Cheese", "20.00"), ("Raita", "40.00")]:
            CustomizationOption.objects.get_or_create(
                group=addons, label=label, defaults={"price_delta": delta}
            )

        # Attach both groups to savoury (non-sweet) recipes only.
        for recipe in Recipe.objects.filter(is_sweet=False):
            RecipeCustomization.objects.get_or_create(recipe=recipe, group=spice, defaults={"sort_order": 1})
            RecipeCustomization.objects.get_or_create(recipe=recipe, group=addons, defaults={"sort_order": 2})

        # Included, free default accompaniments (shown as "Served with …").
        Recipe.objects.filter(section__slug="parathas").update(default_accompaniment="Pickle")
        Recipe.objects.filter(section__slug="snacks").update(
            default_accompaniment="Hari & khatti-mithi chutney"
        )

        # Sample media gallery (placeholder images + a video link) — the owner
        # uploads real food photos via Django admin.
        media_seed = {
            "Aloo Paratha": [
                ("IMAGE", "https://picsum.photos/seed/aloo1/900/650", ""),
                ("IMAGE", "https://picsum.photos/seed/aloo2/900/650", ""),
                ("VIDEO", "https://instagram.com/bstvaranasi", "Watch on Instagram"),
            ],
            "Paneer Paratha": [
                ("IMAGE", "https://picsum.photos/seed/paneer1/900/650", ""),
                ("IMAGE", "https://picsum.photos/seed/paneer2/900/650", ""),
            ],
            "Samosa": [("IMAGE", "https://picsum.photos/seed/samosa1/900/650", "")],
        }
        for rname, items in media_seed.items():
            recipe = Recipe.objects.filter(name=rname).first()
            if recipe and not recipe.media.exists():
                for i, (kind, url, cap) in enumerate(items, start=1):
                    RecipeMedia.objects.create(recipe=recipe, kind=kind, url=url, caption=cap, sort_order=i)

        # Demo: one available item that's display-only (not orderable) — P6 toggle.
        Recipe.objects.filter(name="Kachori").update(ordering_enabled=False)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded: {Section.objects.count()} sections, {Recipe.objects.count()} recipes, "
            f"{CustomizationGroup.objects.count()} groups."
        ))
