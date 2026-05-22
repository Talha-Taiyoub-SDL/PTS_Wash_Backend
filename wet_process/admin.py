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

    list_editable = ["status"]


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


@admin.register(models.BatchSourcePiece)
class BatchSourcePieceAdmin(admin.ModelAdmin):
    list_display = ["id", "batch_source", "garment_unit"]


# @admin.register(models.WashLog)
# class WashLogAdmin(admin.ModelAdmin):
#     list_display = ["id","content_type","object_id","total_quantity","rejections","rewash_quantity","remaining_rewash_quantity","status"]


@admin.register(models.ProcessFirstWash)
class ProcessFirstWashAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "batch",
        "machine",
        "standard_time",
        "loading_start",
        "loading_started_by",
    ]


@admin.register(models.ProcessFirstWashHydro)
class ProcessFirstWashHydroAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "batch",
        "machine",
        "standard_time",
        "hydro_in",
        "hydro_in_by",
        "hydro_out",
        "hydro_out_by",
    ]


@admin.register(models.ProcessFirstWashDryer)
class ProcessFirstWashDryerAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "batch",
        "machine",
        "standard_time",
        "type",
        "dryer_in",
        "dryer_in_by",
        "dryer_out",
        "dryer_out_by",
    ]


@admin.register(models.Rejection)
class RejectionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "individual_barcode",
        "batch",
        "reason",
        "rejected_at",
        "rejected_by",
    ]
