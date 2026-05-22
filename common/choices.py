from django.db import models


class GarmentUnitStatus(models.TextChoices):
    RECEIVED = "received", "Received"
    REJECTED = "rejected", "Rejected"
    WHISKER_IN = "whisker_in", "Whisker In"
    WHISKER_OUT = "whisker_out", "Whisker Out"
    BRUSH_IN = "brush_in", "Brush In"
    BRUSH_OUT = "brush_out", "Brush Out"
    DRY_COMPLETE = "dry_complete", "Dry Complete"
