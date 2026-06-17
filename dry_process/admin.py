from django.contrib import admin
from . import models
# Register your models here.


@admin.register(models.Planning)
class PlanningAdmin(admin.ModelAdmin):
    list_display = ["id", "mpo", "color", "updated_by", "last_update"]
    search_fields = ["mpo"]


@admin.register(models.PlanningRouteStep)
class PlanningRouteStepAdmin(admin.ModelAdmin):
    list_display = ["id", "planning", "sequence", "stage"]
    search_fields = ["planning__mpo"]


@admin.register(models.TrackingHistory)
class TrackingHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "garment_unit",
        "stage",
        "action",
        "rejection_reason",
        "scanned_at",
        "operator",
    ]
