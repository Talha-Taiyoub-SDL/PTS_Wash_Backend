from django.db import models, transaction
from django.utils import timezone
from django.core.validators import MinValueValidator
from .choices import (
    BatchStage,
    BatchType,
    BatchStatus,
    RejectionReason,
    DryerType,
)
from common.models import GarmentUnit


class BatchSequence(models.Model):
    year = models.PositiveIntegerField()
    stage = models.CharField(max_length=20, choices=BatchStage.choices)
    type = models.CharField(max_length=20, choices=BatchType.choices)
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["year", "stage", "type"], name="unique_year_stage_type"
            )
        ]

    def __str__(self):
        return str(self.year)


class Batch(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    buyer = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    shade = models.CharField(max_length=50)
    stage = models.CharField(max_length=20, choices=BatchStage.choices)
    type = models.CharField(max_length=20, choices=BatchType.choices)

    status = models.CharField(
        max_length=20, choices=BatchStatus.choices, default=BatchStatus.READY_TO_WASH
    )
    total_quantity = models.PositiveIntegerField(default=0)
    total_rewash_quantity = models.PositiveIntegerField(default=0)
    total_rejection_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    operator = models.CharField(max_length=100)

    def save(self, *args, **kwargs):

        # with tranction.atomic we're enabling that batch creation and batch sequence generation happens at once
        with transaction.atomic():
            if not self.id:
                self.id = self.generate_batch_id()

            super().save(*args, **kwargs)

    def generate_batch_id(self):
        current_year = timezone.now().year
        short_year = str(current_year)[-2:]

        plant_number = "W822"

        # select_for_update means lock this row until I finish my task/transaction
        sequence, _ = BatchSequence.objects.select_for_update().get_or_create(
            year=current_year, stage=self.stage, type=self.type
        )
        sequence.last_number += 1
        sequence.save(update_fields=["last_number"])
        sequence_number = str(sequence.last_number).zfill(7)

        stage_code = BatchStage.get_stage_map().get(self.stage)
        type_code = BatchType.get_type_map().get(self.type)

        return f"{plant_number}Y{short_year}W{stage_code}{type_code}{sequence_number}"

    def __str__(self):
        return f"{self.id}"


class BatchSource(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="sources")
    mpo = models.CharField(max_length=100)
    style = models.CharField(max_length=100)
    so = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    rewash_quantity = models.PositiveIntegerField(default=0)
    rejection_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["batch", "mpo"], name="unique_batch_mpo")
        ]

    def __str__(self):
        return f"{self.batch}-{self.mpo}"


class BatchSourcePiece(models.Model):
    batch_source = models.ForeignKey(
        BatchSource, on_delete=models.CASCADE, related_name="pieces"
    )
    garment_unit = models.ForeignKey(GarmentUnit, on_delete=models.CASCADE)

    class Meta:
        # To use piece in second wash or rewash just add batch_source in the fields as constraint
        constraints = [
            models.UniqueConstraint(
                fields=["garment_unit"],
                name="unique_garment_unit",
            )
        ]


class Machine(models.Model):
    machine_number = models.IntegerField(
        primary_key=True, validators=[MinValueValidator(1)]
    )
    SAP = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.machine_number}-{self.SAP}"


class Rejection(models.Model):
    garment_unit = models.OneToOneField(GarmentUnit, on_delete=models.CASCADE)
    batch_source = models.ForeignKey(
        BatchSource, on_delete=models.CASCADE, related_name="rejections"
    )
    rejection_reason = models.CharField(max_length=100, choices=RejectionReason.choices)
    rejected_at = models.DateTimeField(auto_now=True)
    operator = models.CharField(max_length=100)


class ProcessFirstWash(models.Model):
    batch = models.OneToOneField(
        Batch, on_delete=models.CASCADE, related_name="process_first_wash"
    )

    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    standard_time = models.DurationField()

    # Loading
    loading_start = models.DateTimeField(auto_now_add=True)
    loading_started_by = models.CharField(max_length=100)

    loading_finish = models.DateTimeField(null=True, blank=True)
    loading_finished_by = models.CharField(max_length=100, null=True, blank=True)

    # Loading is finished means process is automatically started
    process_finish = models.DateTimeField(null=True, blank=True)
    process_finished_by = models.CharField(max_length=100, null=True, blank=True)

    # Process is finished means unloading is automatically started
    unload_finish = models.DateTimeField(null=True, blank=True)
    unload_finished_by = models.CharField(max_length=100, null=True, blank=True)


class ProcessFirstWashHydro(models.Model):
    batch = models.OneToOneField(
        Batch, on_delete=models.CASCADE, related_name="process_first_wash_hydro"
    )
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    standard_time = models.DurationField()

    # Hydro In
    hydro_in = models.DateTimeField(auto_now_add=True)
    hydro_in_by = models.CharField(max_length=100)

    # Hydro Out
    hydro_out = models.DateTimeField(null=True, blank=True)
    hydro_out_by = models.CharField(max_length=100, null=True, blank=True)


class ProcessFirstWashDryer(models.Model):
    CONVEYOR = "conveyor"
    OVEN = "oven"
    TUMBLE = "tumble"

    TYPE_CHOICES = [(CONVEYOR, "Conveyor"), (OVEN, "Oven"), (TUMBLE, "Tumble")]

    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="first_wash_dryer_processes"
    )
    machine = models.ForeignKey(
        Machine, on_delete=models.PROTECT, related_name="first_wash_dryer_processes"
    )
    standard_time = models.DurationField()

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    dryer_in = models.DateTimeField(auto_now_add=True)
    dryer_in_by = models.CharField(max_length=100)
    dryer_out = models.DateTimeField(null=True, blank=True)
    dryer_out_by = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        unique_together = [("batch", "type")]


class ProcessSecondWash(models.Model):
    batch = models.OneToOneField(
        Batch, on_delete=models.CASCADE, related_name="process_second_wash"
    )

    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    standard_time = models.DurationField()

    # Loading
    loading_start = models.DateTimeField(auto_now_add=True)
    loading_started_by = models.CharField(max_length=100)

    loading_finish = models.DateTimeField(null=True, blank=True)
    loading_finished_by = models.CharField(max_length=100, null=True, blank=True)

    # Loading is finished means process is automatically started
    process_finish = models.DateTimeField(null=True, blank=True)
    process_finished_by = models.CharField(max_length=100, null=True, blank=True)

    # Process is finished means unloading is automatically started
    unload_finish = models.DateTimeField(null=True, blank=True)
    unload_finished_by = models.CharField(max_length=100, null=True, blank=True)


class ProcessSecondWashHydro(models.Model):
    batch = models.OneToOneField(
        Batch, on_delete=models.CASCADE, related_name="process_second_wash_hydro"
    )
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    standard_time = models.DurationField()

    # Hydro In
    hydro_in = models.DateTimeField(auto_now_add=True)
    hydro_in_by = models.CharField(max_length=100)

    # Hydro Out
    hydro_out = models.DateTimeField(null=True, blank=True)
    hydro_out_by = models.CharField(max_length=100, null=True, blank=True)


class ProcessSecondWashDryer(models.Model):
    CONVEYOR = "conveyor"
    OVEN = "oven"
    TUMBLE = "tumble"

    TYPE_CHOICES = [(CONVEYOR, "Conveyor"), (OVEN, "Oven"), (TUMBLE, "Tumble")]

    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="second_wash_dryer_processes"
    )
    machine = models.ForeignKey(
        Machine, on_delete=models.PROTECT, related_name="second_wash_dryer_processes"
    )
    standard_time = models.DurationField()

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    dryer_in = models.DateTimeField(auto_now_add=True)
    dryer_in_by = models.CharField(max_length=100)
    dryer_out = models.DateTimeField(null=True, blank=True)
    dryer_out_by = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        unique_together = [("batch", "type")]


class MachineProcessBase(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    standard_time = models.DurationField()

    class Meta:
        abstract = True


class ExecutionBase(MachineProcessBase):
    start_time = models.DateTimeField(auto_now_add=True)
    started_by = models.CharField(max_length=100)
    finish_time = models.DateTimeField(null=True, blank=True)
    finished_by = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        abstract = True


class WashProcess(MachineProcessBase):
    batch = models.OneToOneField(
        Batch, on_delete=models.CASCADE, related_name="wash_process"
    )

    # Loading
    loading_start = models.DateTimeField(auto_now_add=True)
    loading_started_by = models.CharField(max_length=100)

    loading_finish = models.DateTimeField(null=True, blank=True)
    loading_finished_by = models.CharField(max_length=100, null=True, blank=True)

    # Loading is finished means process is automatically started
    process_finish = models.DateTimeField(null=True, blank=True)
    process_finished_by = models.CharField(max_length=100, null=True, blank=True)

    # Process is finished means unloading is automatically started
    unloading_finish = models.DateTimeField(null=True, blank=True)
    unloading_finished_by = models.CharField(max_length=100, null=True, blank=True)


class HydroProcess(ExecutionBase):
    batch = models.OneToOneField(
        Batch, on_delete=models.CASCADE, related_name="hydro_process"
    )


class DryerProcess(ExecutionBase):
    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="dryer_processes"
    )
    type = models.CharField(max_length=10, choices=DryerType.choices)

    class Meta:
        unique_together = [("batch", "type")]
