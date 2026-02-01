from django.contrib import admin
from . import models
# Register your models here.

@admin.register(models.StageName)
class StageNameAdmin(admin.ModelAdmin):
    list_display = ["id","stage","last_update"]

@admin.register(models.Planning)
class PlanningAdmin(admin.ModelAdmin):
    list_display = ["id","mpo","updated_by","last_update"]

@admin.register(models.PlanningRouteStep)
class PlanningRouteStepAdmin(admin.ModelAdmin):
    list_display = ["id","planning","sequence","stage"]
    ordering = ["planning","sequence","stage"]
    search_fields = ["planning__mpo"]
    
@admin.register(models.ReceivedBundle)
class ReceivedBundleAdmin(admin.ModelAdmin):
    list_display = ["id","mpo","buyer","style","marker","bundle_no","bundle_barcode","size","shade","color","quantity","received_at","received_by","status"]   
    
@admin.register(models.Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ["id","mpo","size","color","updated_at","updated_by"]     

@admin.register(models.BatchBundle)
class BatchBundleAdmin(admin.ModelAdmin):
    list_display = ["id","batch_id","received_id"]    
    
@admin.register(models.BatchStage)
class BatchStageAdmin(admin.ModelAdmin):
    list_display = ["batch_id","current_stage","sequence","current_status","production_status"]    
    
@admin.register(models.BatchStageHistory)
class BatchStageHistoryAdmin(admin.ModelAdmin):
    list_display = ["id","batch_id","stage","sequence","entered_at","closed_at","entered_by","closed_by"] 
    
@admin.register(models.Rejection)
class RejectionAdmin(admin.ModelAdmin):
    list_display = ["id", "individual_barcode", "batch_id", "stage", "reason", "rejected_at", "rejected_by"]        
    
@admin.register(models.BatchQcStageSummary)
class BatchQcStageSummaryAdmin(admin.ModelAdmin):
    list_display = ["id","batch_id","stage","rejection_count","last_update"]    