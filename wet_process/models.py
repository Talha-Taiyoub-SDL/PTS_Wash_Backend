from django.db import models
from production.models import Batch, ReceivedBundle

class BatchForFirstWash(models.Model):
    shade = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    total_quantity = models.IntegerField(default=0)
    status  = models.CharField(max_length=100,null=True,blank=True) # If it's needed later
    
    def __str__(self):
        return f"{self.id}"

# When the source is created batches from dry process    
class FirstWashBatchSource(models.Model):
    batch_for_first_wash = models.ForeignKey(
        BatchForFirstWash,
        on_delete=models.CASCADE,
        related_name="source_batches"
    )
    batch = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT
    )
    quantity = models.IntegerField()
    
# When the source is the bundles
class FirstWashBundleSource(models.Model):
    batch_for_first_wash = models.ForeignKey(
        BatchForFirstWash,
        on_delete=models.CASCADE,
        related_name="source_bundles"
    )
    bundle = models.ForeignKey(
        ReceivedBundle,
        on_delete=models.PROTECT
    )
    quantity = models.IntegerField()        