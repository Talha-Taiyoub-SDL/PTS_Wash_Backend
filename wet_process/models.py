from django.db import models
from django.core.validators import MinValueValidator
from production.models import Batch, ReceivedBundle

class Machine(models.Model):
    machine_number = models.IntegerField(
        primary_key=True,
        validators=[MinValueValidator(1)]
    )
    SAP = models.CharField(max_length=100)
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.machine_number}-{self.SAP}"

class BatchForFirstWash(models.Model):
    shade = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    total_quantity = models.IntegerField(default=0)
    status  = models.CharField(max_length=100,null=True,blank=True) # If it's needed later
    
    def __str__(self):
        return f"{self.id}"

# When the source is "created batches" from dry process    
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
        
class ProcessFirstWash(models.Model):
    batch_for_first_wash = models.OneToOneField(
        BatchForFirstWash,
        on_delete=models.CASCADE,
        related_name="first_wash_process"
    )

    machine = models.ForeignKey(
        Machine,
        on_delete=models.PROTECT,
        related_name="first_wash_processes"
    )

    # Loading
    loading_start = models.DateTimeField(auto_now_add=True)
    loading_started_by = models.CharField(max_length=100)

    loading_finish = models.DateTimeField(null=True, blank=True)
    loading_finished_by = models.CharField(max_length=100, null=True, blank=True)

    # Loading is finished means process is automatically started 
    process_finish = models.DateTimeField(null=True, blank=True)
    process_finished_by = models.CharField(max_length=100, null=True, blank=True)

    # Process is finished means unloading is automatically started
    unload_finish = models.DateTimeField(null=True, blank=True)
    unload_finished_by = models.CharField(max_length=100, null=True, blank=True)
   
class ProcessFirstWashHydro(models.Model):
    batch_for_first_wash = models.OneToOneField(BatchForFirstWash, on_delete=models.CASCADE, related_name="process_first_wash_hydro")
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, related_name="first_wash_hydro_processes")
    
    # Hydro In
    hydro_in = models.DateTimeField(auto_now_add=True)
    hydro_in_by = models.CharField(max_length=100)
    
    #Hydro Out
    hydro_out = models.DateTimeField(null=True,blank=True)
    hydro_out_by = models.CharField(max_length=100, null=True,blank=True)

class ProcessFirstWashDryer(models.Model):
    CONVEYOR = "conveyor"
    OVEN = "oven"
    TUMBLE = "tumble"
    
    TYPE_CHOICES = [(CONVEYOR,"Conveyor"),(OVEN,"Oven"),(TUMBLE,"Tumble")]
    
    batch_for_first_wash = models.ForeignKey(BatchForFirstWash,on_delete=models.CASCADE, related_name="first_wash_dryer_processes")
    machine  = models.ForeignKey(Machine,on_delete=models.PROTECT, related_name = "first_wash_dryer_processes")
    
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    dryer_in = models.DateTimeField(auto_now_add=True)
    dryer_in_by = models.CharField(max_length=100)
    dryer_out = models.DateTimeField(null=True,blank=True)
    dryer_out_by = models.CharField(max_length=100,null=True,blank=True)
    
    class Meta:
        unique_together = [("batch_for_first_wash","type")]