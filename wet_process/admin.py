from django.contrib import admin
from . import models
# Register your models here.


@admin.register(models.Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ["machine_number", "SAP", "added_at"]


@admin.register(models.Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "buyer",
        "color",
        "shade",
        "stage",
        "type",
        "status",
        "total_quantity",
        "total_rewash_quantity",
        "total_rejection_quantity",
    ]

    list_editable = [
        "status",
        "total_quantity",
        "total_rewash_quantity",
        "total_rejection_quantity",
    ]


@admin.register(models.BatchSource)
class BatchSourceAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "batch",
        "mpo",
        "style",
        "so",
        "quantity",
        "rewash_quantity",
        "rejection_quantity",
    ]

    list_editable = ["rewash_quantity", "rejection_quantity"]


@admin.register(models.BatchSourcePiece)
class BatchSourcePieceAdmin(admin.ModelAdmin):
    list_display = ["id", "batch_source", "garment_unit"]


@admin.register(models.WashProcess)
class WashProcessAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "batch",
        "machine",
        "standard_time",
        "loading_start",
        "loading_started_by",
        "loading_finish",
        "loading_finished_by",
        "process_finish",
        "process_finished_by",
        "unloading_finish",
        "unloading_finished_by",
    ]


@admin.register(models.Rejection)
class RejectionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "garment_unit",
        "batch_source",
        "rejection_reason",
        "rejected_at",
        "operator",
    ]
