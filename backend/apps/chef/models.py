"""M12 — Chef profile & social presence.

`ChefProfile` is a singleton (the About-Chef content). `SocialLink` is the reusable
shape (platform + handle/url) — v1 Instagram only, enum reserved for more platforms.
The same shape describes a recipe's per-dish "chef style" link (fields live on Recipe).
"""
from django.db import models


class Platform(models.TextChoices):
    INSTAGRAM = "INSTAGRAM", "Instagram"
    # reserved for later: FACEBOOK, YOUTUBE, WHATSAPP, …


class ChefProfile(models.Model):
    name = models.CharField(max_length=80, default="Niketa")
    tagline = models.CharField(max_length=140, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="chef/", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chef profile"
        verbose_name_plural = "Chef profile"

    @classmethod
    def get_solo(cls):
        """Singleton accessor — one profile row for the whole app."""
        obj = cls.objects.first()
        if obj is None:
            obj = cls.objects.create()
        return obj

    def __str__(self):
        return self.name


class SocialLink(models.Model):
    profile = models.ForeignKey(ChefProfile, on_delete=models.CASCADE, related_name="socials")
    platform = models.CharField(max_length=12, choices=Platform.choices, default=Platform.INSTAGRAM)
    handle = models.CharField(max_length=60)
    url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    @property
    def resolved_url(self):
        # M12 R2: derive the URL from the handle if not explicitly set.
        if self.url:
            return self.url
        return f"https://instagram.com/{self.handle}"

    def __str__(self):
        return f"{self.platform}:{self.handle}"
