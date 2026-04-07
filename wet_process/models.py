from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.core.validators import MinValueValidator
from production.models import ReceivedBundle
from .choices import BatchStage, BatchType

# New batches are started from this place.
class Batch(models.Model):
    buyer = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    shade = models.CharField(max_length=50)
    stage = models.CharField(max_length=20, choices=BatchStage.choices)
    type = models.CharField(max_length=20, choices=BatchType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    
    # Implementing reverse relationship so that it behaves similar to related_name of a normal ForeignKey.
    # rejections = GenericRelation(
    #     Rejection,
    #     related_query_name="batch" # It will work like Rejection.objects.filter(batch_for_first_wash=1)
    # )
    
    # logs = GenericRelation(WashLog, related_query_name="batch") 
    
    def __str__(self):
        return f"{self.id}"  
    
class InternalBatch(models.Model):
    mpo = models.CharField(max_length=100)
    style = models.CharField(max_length=100)
    so = models.CharField(max_length=100)      
    
    class Meta:
        unique_together = ["mpo","style","so"]
    
class BatchSource(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="sources")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE) 
    object_id = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    source_object = GenericForeignKey(
        "content_type",
        "object_id"
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    rewash_quantity = models.PositiveIntegerField(default=0)

class Machine(models.Model):
    machine_number = models.IntegerField(
        primary_key=True,
        validators=[MinValueValidator(1)]
    )
    SAP = models.CharField(max_length=100)
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.machine_number}-{self.SAP}"
    
class Rejection(models.Model):
    # Copy the barcode of the individual garment
    individual_barcode = models.CharField(max_length=100, unique=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="rejections")
    reason = models.CharField(max_length=100)
    rejected_at = models.DateTimeField(auto_now=True)
    rejected_by = models.CharField(max_length=100)  
        
# class WashLog(models.Model):
#     content_type = models.ForeignKey(
#         ContentType,
#         on_delete=models.PROTECT
#     )
#     object_id = models.PositiveIntegerField()
    
#     # As source batch, either batch_for_first_wash or batch_for_rewash will be placed (up to this point)
#     source_batch = GenericForeignKey(
#         "content_type",
#         "object_id"
#     )
#     total_quantity = models.PositiveIntegerField()
#     rejections = models.PositiveIntegerField(default=0)
#     rewash_quantity = models.PositiveIntegerField(default=0)
#     remaining_rewash_quantity = models.PositiveIntegerField(default=0)
#     status = models.CharField(max_length=100, null=True, blank=True)
    
#     class Meta:
#         unique_together = [("content_type","object_id")]
             
# class ProcessFirstWash(models.Model):
#     batch = models.OneToOneField(
#         Batch,
#         on_delete=models.CASCADE,
#         related_name="first_wash_process"
#     )

#     machine = models.ForeignKey(
#         Machine,
#         on_delete=models.PROTECT,
#         related_name="first_wash_processes"
#     )

#     # Loading
#     loading_start = models.DateTimeField(auto_now_add=True)
#     loading_started_by = models.CharField(max_length=100)

#     loading_finish = models.DateTimeField(null=True, blank=True)
#     loading_finished_by = models.CharField(max_length=100, null=True, blank=True)

#     # Loading is finished means process is automatically started 
#     process_finish = models.DateTimeField(null=True, blank=True)
#     process_finished_by = models.CharField(max_length=100, null=True, blank=True)

#     # Process is finished means unloading is automatically started
#     unload_finish = models.DateTimeField(null=True, blank=True)
#     unload_finished_by = models.CharField(max_length=100, null=True, blank=True)
   
# class ProcessFirstWashHydro(models.Model):
#     batch = models.OneToOneField(Batch, on_delete=models.CASCADE, related_name="process_first_wash_hydro")
#     machine = models.ForeignKey(Machine, on_delete=models.PROTECT, related_name="first_wash_hydro_processes")
    
#     # Hydro In
#     hydro_in = models.DateTimeField(auto_now_add=True)
#     hydro_in_by = models.CharField(max_length=100)
    
#     #Hydro Out
#     hydro_out = models.DateTimeField(null=True,blank=True)
#     hydro_out_by = models.CharField(max_length=100, null=True,blank=True)

# class ProcessFirstWashDryer(models.Model):
#     CONVEYOR = "conveyor"
#     OVEN = "oven"
#     TUMBLE = "tumble"
    
#     TYPE_CHOICES = [(CONVEYOR,"Conveyor"),(OVEN,"Oven"),(TUMBLE,"Tumble")]
    
#     batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="first_wash_dryer_processes")
#     machine  = models.ForeignKey(Machine,on_delete=models.PROTECT, related_name = "first_wash_dryer_processes")
    
#     type = models.CharField(max_length=10, choices=TYPE_CHOICES)
#     dryer_in = models.DateTimeField(auto_now_add=True)
#     dryer_in_by = models.CharField(max_length=100)
#     dryer_out = models.DateTimeField(null=True,blank=True)
#     dryer_out_by = models.CharField(max_length=100,null=True,blank=True)
    
#     class Meta:
#         unique_together = [("batch","type")]



    
    

                          
           