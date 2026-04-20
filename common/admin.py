from django.contrib import admin
from . import models

# Register your models here.
@admin.register(models.MasterPlan)
class MasterPlanAdmin(admin.ModelAdmin):
    list_display = ["id", "buyer", "style", "color", "last_update", "updated_by"]

@admin.register(models.RouteStep)
class RouteStepAdmin(admin.ModelAdmin):
    list_display = ["id","master_plan", "sequence", "stage"]
    
@admin.register(models.SubRouteStep)
class SubRouteStepAdmin(admin.ModelAdmin):
    list_display = ["id", "route_step", "sequence", "stage"]        

