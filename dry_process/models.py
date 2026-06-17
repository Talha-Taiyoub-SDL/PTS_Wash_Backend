from django.db import models
from django.core.validators import MinValueValidator
from common.models import GarmentUnit
from .choices import Stage, Action


# Create your models here.
class Planning(models.Model):
    mpo = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    updated_by = models.CharField(max_length=100)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["mpo", "color"], name="unique_mpo_color")
        ]

    def __str__(self):
        return self.mpo


class PlanningRouteStep(models.Model):
    planning = models.ForeignKey(
        Planning, on_delete=models.CASCADE, related_name="route_steps"
    )
    sequence = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    stage = models.CharField(max_length=100, choices=Stage.choices)

    class Meta:
        unique_together = [
            ("planning", "sequence"),
            ("planning", "stage"),
        ]
        ordering = ["sequence"]

    def __str__(self):
        return f"{self.planning_id} - {self.sequence} - {self.stage}"


class TrackingHistory(models.Model):
    garment_unit = models.ForeignKey(
        GarmentUnit, on_delete=models.CASCADE, related_name="histories"
    )
    stage = models.CharField(max_length=100, choices=Stage.choices)
    action = models.CharField(max_length=100, choices=Action.choices)
    rejection_reason = models.CharField(max_length=100, null=True, blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)
    operator = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["garment_unit", "stage", "action"],
                name="unique_garment_unit_stage_action",
            )
        ]
        ordering = ["scanned_at"]
