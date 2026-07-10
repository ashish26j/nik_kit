"""Seed the chef profile (Niketa + Instagram bstvaranasi) and a couple of example
per-recipe chef-style links. Idempotent. Run: manage.py seed_chef
"""
from django.core.management.base import BaseCommand

from apps.chef.models import ChefProfile, Platform, SocialLink
from apps.menu.models import Recipe

INSTAGRAM_HANDLE = "bstvaranasi"


class Command(BaseCommand):
    help = "Seed chef profile + Instagram + example recipe chef-style links."

    def handle(self, *args, **options):
        p = ChefProfile.get_solo()
        p.name = p.name or "Niketa"
        if not p.tagline:
            p.tagline = "Home-style Banarasi cooking"
        if not p.bio:
            p.bio = (
                "Niketa cooks the parathas, snacks and sweets she grew up with in "
                "Varanasi — small-batch, from scratch, and shared daily on Instagram."
            )
        p.save()

        SocialLink.objects.get_or_create(
            profile=p, platform=Platform.INSTAGRAM, handle=INSTAGRAM_HANDLE,
            defaults={"url": f"https://instagram.com/{INSTAGRAM_HANDLE}"},
        )

        # Example per-recipe "chef style" links (owner replaces with real post URLs).
        example_url = f"https://instagram.com/{INSTAGRAM_HANDLE}"
        for name in ("Aloo Paratha", "Paneer Paratha"):
            Recipe.objects.filter(name=name).update(
                chef_style_url=example_url, chef_style_platform=Platform.INSTAGRAM
            )

        self.stdout.write(self.style.SUCCESS("Seeded chef profile + example recipe links."))
