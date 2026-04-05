from django.contrib import admin
from . import models
# Register your models here.

@admin.register(models.Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display=["machine_number","SAP","added_at"] 
    
# @admin.register(models.WashLog) 
# class WashLogAdmin(admin.ModelAdmin):
#     list_display = ["id","content_type","object_id","total_quantity","rejections","rewash_quantity","remaining_rewash_quantity","status"]      
    
# @admin.register(models.ProcessFirstWash)
# class ProcessFirstWashAdmin(admin.ModelAdmin):
#     list_display = ["id","batch","machine","loading_start","loading_started_by"]   

# @admin.register(models.ProcessFirstWashHydro)
# class ProcessFirstWashHydroAdmin(admin.ModelAdmin):
#     list_display = ["id","batch","machine","hydro_in","hydro_in_by","hydro_out","hydro_out_by"] 
      
# @admin.register(models.ProcessFirstWashDryer)
# class ProcessFirstWashDryerAdmin(admin.ModelAdmin):
#     list_display = ["id","batch","machine","type","dryer_in","dryer_in_by","dryer_out","dryer_out_by"]  
    
# @admin.register(models.Rejection)
# class RejectionAdmin(admin.ModelAdmin):
#     list_display = ["id","individual_barcode","reason","stage","content_type","object_id","rejected_at", "rejected_by"]      
    
@admin.register(models.InternalBatch)
class InternalBatchAdmin(admin.ModelAdmin):
    list_display = ["id", "mpo", "style", "so"]          
     