from django.db import models
from django.core.validators import MinValueValidator
from .choices import GarmentUnitStatus

# Create your models here.
class MasterPlan(models.Model):
    buyer = models.CharField(max_length=100)
    style = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    updated_by = models.CharField(max_length=100)
    last_update = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["buyer","style","color"],
                name="unique_master_plan"
            )
        ]
        
    def __str__(self):
        return f"{self.buyer}-{self.style}-{self.color}"    
    
class RouteStep(models.Model):
    master_plan = models.ForeignKey(
        MasterPlan,
        on_delete=models.CASCADE,
        related_name='route_steps'
    )
    sequence = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    stage = models.CharField(max_length=100)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["master_plan", "sequence"],
                name="unique_route_sequence"
            )
        ]
        ordering = ["sequence"]

    def __str__(self):
        return f"{self.master_plan.id} - {self.sequence} - {self.stage}"
    
class SubRouteStep(models.Model):
    route_step = models.ForeignKey(RouteStep,on_delete=models.CASCADE,related_name="sub_steps")
    sequence = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    stage = models.CharField(max_length=100)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["route_step", "sequence"],
                name = "unique_sub_route_sequence"
            )    
        ] 
        ordering = ["sequence"]
        
        def __str__(self):
            return f"{self.route_step.id} - {self.sequence} - {self.stage}"       
        
class GarmentUnit(models.Model):
    individual_barcode = models.CharField(max_length=100, unique=True)
    so = models.CharField(max_length=100)
    mpo = models.CharField(max_length=100)
    buyer = models.CharField(max_length=100)
    style = models.CharField(max_length=100)
    marker = models.CharField(max_length=100)
    size = models.CharField(max_length=50)
    shade = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    
    status = models.CharField(
        max_length=100,
        choices=GarmentUnitStatus.choices,
        default=GarmentUnitStatus.RECEIVED,
    )
    received_at = models.DateTimeField(auto_now_add=True)
    received_by = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.individual_barcode} - {self.mpo} - {self.color}"
                    