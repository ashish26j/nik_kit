"""Server-authoritative pricing + option validation (M04 R1/R2, M05 R1)."""
from decimal import Decimal

from rest_framework.exceptions import ValidationError


def _recipe_option_maps(recipe):
    """Return (groups_by_id, valid_option_by_id) for a recipe's attached groups."""
    groups, valid = {}, {}
    for rc in recipe.recipe_customizations.select_related("group").prefetch_related(
        "group__options"
    ):
        g = rc.group
        groups[g.id] = g
        for o in g.options.all():
            valid[o.id] = o
    return groups, valid


def validate_and_price(recipe, option_ids):
    """Validate chosen options for a recipe and compute the unit price.

    Returns (unit_price: Decimal, chosen_options: list). Raises ValidationError.
    """
    # de-dupe while preserving order
    ids = list(dict.fromkeys(int(x) for x in (option_ids or [])))
    groups, valid = _recipe_option_maps(recipe)

    chosen = []
    for oid in ids:
        if oid not in valid:
            raise ValidationError(f"option {oid} is not valid for this recipe")
        chosen.append(valid[oid])

    for gid, g in groups.items():
        in_group = [o for o in chosen if o.group_id == gid]
        if g.select_type == "SINGLE" and len(in_group) > 1:
            raise ValidationError(f"{g.name}: choose only one")
        if g.is_required and not in_group:
            raise ValidationError(f"{g.name} is required")

    unit = recipe.price + sum((o.price_delta for o in chosen), Decimal("0.00"))
    return unit, chosen


def option_labels(recipe, option_ids):
    """[{label, price_delta}] snapshot for the given option ids on a recipe."""
    _, valid = _recipe_option_maps(recipe)
    out = []
    for oid in option_ids or []:
        o = valid.get(int(oid))
        if o:
            out.append({"label": o.label, "price_delta": str(o.price_delta)})
    return out
