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
        unique_together = ["buyer", "style", "color"]
    
class PlanningRouteStep(models.Model):
    master_plan = models.ForeignKey(
        MasterPlan,
        on_delete=models.CASCADE,
        related_name='route_steps'
    )
    sequence = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    stage = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ['master_plan', 'sequence']

    def __str__(self):
        return f"{self.master_plan.id} - {self.sequence} - {self.stage}"    