from django.db import models
from common.models import GarmentUnit
from .choices import Stage, Action

# Create your models here.
class TrackingHistory(models.Model):
    garment_unit = models.ForeignKey(GarmentUnit, on_delete=models.CASCADE, related_name="histories")
    stage = models.CharField(max_length=100, choices=Stage.choices)
    action = models.CharField(max_length=100, choices=Action.choices)
    rejection_reason = models.CharField(max_length=100, null=True, blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)
    operator = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["garment_unit", "stage", "action"],
                name = "unique_garment_unit_stage_action"
            )    
        ] 
        ordering = ["scanned_at"]