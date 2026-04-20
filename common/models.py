from django.db import models
from django.core.validators import MinValueValidator

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
                name="unique_planning_sequence"
            )
        ]
        ordering = ["sequence"]

    def __str__(self):
        return f"{self.master_plan.id} - {self.sequence} - {self.stage}"
    
class WetProcessStep(models.Model):
    planning = models.ForeignKey(RouteStep,on_delete=models.CASCADE,related_name="wet_process_steps")
    sequence = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    stage = models.CharField(max_length=100)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["planning", "sequence"],
                name = "unique_wet_process_sequence"
            )    
        ] 
        ordering = ["sequence"]
        
        def __str__(self):
            return f"{self.planning.id} - {self.sequence} - {self.stage}"       