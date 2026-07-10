"""M09 — Business closures. Owner marks the shop closed for a day or a date range.

Store is closed if today falls within ANY closure range. Closures are additive
(overlaps are fine). Enforcement: M05 checkout is blocked while closed; browsing and
cart-building stay open (explore-first preserved).
"""
from django.db import models


class BusinessClosure(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()  # == start_date for a single day ("closed today")
    message = models.CharField(max_length=140, blank=True)  # optional banner text
    created_by = models.CharField(max_length=60, blank=True)  # admin label
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_date", "id"]

    def __str__(self):
        span = self.start_date.isoformat()
        if self.end_date != self.start_date:
            span += f" … {self.end_date.isoformat()}"
        return f"Closed {span}"
