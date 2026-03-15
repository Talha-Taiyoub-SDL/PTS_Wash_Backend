from django.contrib import admin
from . import models
# Register your models here.

@admin.register(models.Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display=["machine_number","SAP","added_at"] 

@admin.register(models.BatchForFirstWash)
class BatchForFirstWashAdmin(admin.ModelAdmin):
    list_display = ["id","buyer","color","shade","created_at","created_by"]

@admin.register(models.FirstWashBatchSource)
class FirstWashBatchSourceAdmin(admin.ModelAdmin):
    list_display = ["id","batch_for_first_wash","mpo","style","so","quantity"]
    
@admin.register(models.FirstWashBundleSource)
class FirstWashBundleSourceAdmin(admin.ModelAdmin):
    list_display = ["id","batch_for_first_wash","received","quantity"]
    
@admin.register(models.WashLog) 
class WashLogAdmin(admin.ModelAdmin):
    list_display = ["id","content_type","object_id","total_quantity","rejections","rewash_quantity","remaining_rewash_quantity","status"]      
    
@admin.register(models.ProcessFirstWash)
class ProcessFirstWashAdmin(admin.ModelAdmin):
    list_display = ["id","batch_for_first_wash","machine","loading_start","loading_started_by"]   

@admin.register(models.ProcessFirstWashHydro)
class ProcessFirstWashHydroAdmin(admin.ModelAdmin):
    list_display = ["id","batch_for_first_wash","machine","hydro_in","hydro_in_by","hydro_out","hydro_out_by"] 
      
@admin.register(models.ProcessFirstWashDryer)
class ProcessFirstWashHydroAdmin(admin.ModelAdmin):
    list_display = ["id","batch_for_first_wash","machine","type","dryer_in","dryer_in_by","dryer_out","dryer_out_by"]  
    
@admin.register(models.Rejection)
class RejectionAdmin(admin.ModelAdmin):
    list_display = ["id","individual_barcode","reason","stage","content_type","object_id","rejected_at", "rejected_by"]     
    
@admin.register(models.BatchForRewash)
class BatchForRewashAdmin(admin.ModelAdmin):
    list_display = ["id","buyer","color","shade","created_at","created_by"]
    
@admin.register(models.RewashBatchSource)
class RewashBatchSourceAdmin(admin.ModelAdmin):
    list_display = ["id", "content_type", "object_id", "quantity", "batch_for_rewash"]        
     