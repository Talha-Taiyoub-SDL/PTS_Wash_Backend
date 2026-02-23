from django.db import models
from django.core.validators import MinValueValidator

# Create your models here.

class StageName(models.Model):
    stage = models.CharField(max_length=200, unique = True)
    last_update = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.stage

class Planning(models.Model):
    mpo = models.CharField(max_length=100, unique=True)
    updated_by = models.CharField(max_length=100)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpo
    
class PlanningRouteStep(models.Model):
    planning = models.ForeignKey(
        Planning,
        on_delete=models.CASCADE,
        related_name='route_steps'
    )
    sequence = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    stage = models.CharField(max_length=100)

    class Meta:
        unique_together = [
            ('planning', 'sequence'),
            ('planning', 'stage'),
        ]
        ordering = ['sequence']

    def __str__(self):
        return f"{self.planning_id} - {self.sequence} - {self.stage}"

class ReceivedBundle(models.Model):
    STATUS_RECEIVED = "received"
    STATUS_ALLOCATED = "allocated"

    STATUS_CHOICES = [
        (STATUS_RECEIVED, "Received"),
        (STATUS_ALLOCATED, "Allocated"),
    ]

    mpo = models.CharField(max_length=100)
    buyer = models.CharField(max_length=100)
    style = models.CharField(max_length=100)
    marker = models.CharField(max_length=100)
    bundle_no = models.PositiveIntegerField()
    bundle_barcode = models.CharField(max_length=100,unique=True)
    size = models.CharField(max_length=50)
    shade = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    received_at = models.DateTimeField(auto_now_add=True)
    received_by = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_RECEIVED,
    )

    class Meta:
        unique_together = ["mpo", "marker","bundle_no"]

    def __str__(self):
        return f"{self.mpo} - {self.marker} - {self.bundle_no}"


class Batch(models.Model):
    STATUS_IN = "in"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_IN, "In"),
        (STATUS_CLOSED, "Closed"),
    ]
    
    mpo = models.CharField(max_length=50)
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=20)
    planning = models.ForeignKey(Planning, on_delete=models.CASCADE, related_name="batches")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default = STATUS_IN)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.id}"

class BatchBundle(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="batch_bundles")
    received = models.OneToOneField("ReceivedBundle", on_delete=models.CASCADE,related_name="batch_bundle")
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [("batch", "received")]   

class BatchStage(models.Model):
    STATUS_IN = "in"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_IN, "In"),
        (STATUS_CLOSED, "Closed"),
    ]

    batch = models.OneToOneField(
        Batch,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="stage"
    )

    current_stage = models.CharField(max_length=100)
    sequence = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    current_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )
    
    def __str__(self):
        return f"Batch {self.batch_id} - {self.current_stage}"
    
class BatchStageHistory(models.Model):
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="stage_history"
    )

    stage = models.CharField(max_length=100)
    sequence = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    entered_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)
    entered_by = models.CharField(max_length=100)
    closed_by = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        unique_together = [
            ('batch', 'sequence'),
            ('batch', 'stage'),
        ]
        ordering = ["entered_at"]
    
    def __str__(self):
        return f"Batch {self.batch_id} - {self.stage}"                   


class Rejection(models.Model):
    DEFECT_STITCHING = "stitching_defect"
    DEFECT_FABRIC = "fabric_defect"
    DEFECT_MEASUREMENT = "measurement_issue"
    DEFECT_COLOR = "color_mismatch"
    DEFECT_DAMAGE = "physical_damage"
    DEFECT_FINISHING = "finishing_issue"
    DEFECT_MISSING = "missing_part"
    DEFECT_OTHER = "other"

    REASON_CHOICES = [
        (DEFECT_STITCHING, "Stitching defect"),
        (DEFECT_FABRIC, "Fabric defect"),
        (DEFECT_MEASUREMENT, "Measurement issue"),
        (DEFECT_COLOR, "Color mismatch"),
        (DEFECT_DAMAGE, "Physical damage"),
        (DEFECT_FINISHING, "Finishing issue"),
        (DEFECT_MISSING, "Missing part"),
        (DEFECT_OTHER, "Other"),
    ]
    
    # Copy the barcode of the individual garment
    individual_barcode = models.CharField(max_length=100, unique=True)
    
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="rejections")
    stage = models.CharField(max_length=100)
    reason = models.CharField(max_length=100, choices=REASON_CHOICES)
    rejected_at = models.DateTimeField(auto_now=True)
    rejected_by = models.CharField(max_length=100)
    
# We're using BatchQcStageSummary so that we can quickly get how many rejections are there of a batch(per stage)    
class BatchQcStageSummary(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="qc_stage_summaries")
    stage = models.CharField(max_length=100)
    rejection_count = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    last_update = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ('batch','stage')
        ]