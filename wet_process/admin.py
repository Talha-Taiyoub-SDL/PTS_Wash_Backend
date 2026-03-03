from django.contrib import admin
from . import models
# Register your models here.

@admin.register(models.BatchForFirstWash)
class BatchForFirstWashAdmin(admin.ModelAdmin):
    list_display = ["id","shade","created_at","created_by","total_quantity","status"]

@admin.register(models.FirstWashBatchSource)
class FirstWashBatchSourceAdmin(admin.ModelAdmin):
    list_display = ["id","batch_for_first_wash","batch","quantity"]
    
@admin.register(models.FirstWashBundleSource)
class FirstWashBundleSourceAdmin(admin.ModelAdmin):
    list_display = ["id","batch_for_first_wash","bundle","quantity"]
    
@admin.register(models.ProcessFirstWash)
class ProcessFirstWashAdmin(admin.ModelAdmin):
    list_display = ["id","batch_for_first_wash","machine","loading_start","loading_started_by"]   

@admin.register(models.Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display=["machine_number","SAP","added_at"]    
     