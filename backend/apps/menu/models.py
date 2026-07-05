"""Menu domain models — owns Section, Recipe (M03) and Customization (M04).

Contracts: docs/contracts/M03-recipes-admin.md, M04-customization.md.
Order snapshots (M05) will copy name/price/options at order time, so editing these
later never rewrites history.
"""
from django.db import models


class Section(models.Model):
    """Parathas / Snacks / Sweets (extensible). M03."""

    name = models.CharField(max_length=40)
    slug = models.SlugField(max_length=60, unique=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class CustomizationGroup(models.Model):
    """A set of choices for a recipe, e.g. 'Spice level' or 'Add-ons'. M04."""

    class Kind(models.TextChoices):
        INGREDIENT = "INGREDIENT", "Ingredient"
        PREPARATION = "PREPARATION", "Preparation"

    class SelectType(models.TextChoices):
        SINGLE = "SINGLE", "Single (radio)"
        MULTI = "MULTI", "Multi (checkbox)"

    name = models.CharField(max_length=60)
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.INGREDIENT)
    select_type = models.CharField(
        max_length=6, choices=SelectType.choices, default=SelectType.SINGLE
    )
    is_required = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class CustomizationOption(models.Model):
    """A single choice inside a group, with an optional price delta. M04."""

    group = models.ForeignKey(
        CustomizationGroup, on_delete=models.CASCADE, related_name="options"
    )
    label = models.CharField(max_length=60)
    price_delta = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_default = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.label} (+{self.price_delta})"


class Recipe(models.Model):
    """A menu item. M03. `display_status` drives visibility (contract M03 R7)."""

    class Display(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        UNAVAILABLE = "UNAVAILABLE", "Not available (shown greyed)"
        HIDDEN = "HIDDEN", "Hidden (blocked from menu)"

    section = models.ForeignKey(
        Section, on_delete=models.PROTECT, related_name="recipes"
    )
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    is_sweet = models.BooleanField(
        default=False, help_text="Sweets skip healthiness scoring (M11)."
    )
    display_status = models.CharField(
        max_length=12, choices=Display.choices, default=Display.AVAILABLE
    )
    customization_groups = models.ManyToManyField(
        CustomizationGroup,
        through="RecipeCustomization",
        related_name="recipes",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    @property
    def is_available(self):
        return self.display_status == self.Display.AVAILABLE

    def __str__(self):
        return self.name


class RecipeImage(models.Model):
    """Ordered images for a recipe; first (sort_order=0) is the thumbnail. M03."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="images")
    file = models.ImageField(upload_to="recipes/")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.recipe.name} image #{self.sort_order}"


class RecipeCustomization(models.Model):
    """Join: which customization groups apply to a recipe, and in what order. M04."""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipe_customizations"
    )
    group = models.ForeignKey(
        CustomizationGroup, on_delete=models.CASCADE, related_name="recipe_customizations"
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = [("recipe", "group")]

    def __str__(self):
        return f"{self.recipe.name} · {self.group.name}"
