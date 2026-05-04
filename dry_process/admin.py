from django.contrib import admin
from . import models
# Register your models here.

@admin.register(models.TrackingHistory)
class TrackingHistoryAdmin(admin.ModelAdmin):
    list_display = ["garment_unit", "stage", "action", "rejection_reason", "scanned_at", "operator"]