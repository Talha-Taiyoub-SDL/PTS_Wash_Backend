from django.db import models

class BatchForFirstWash(models.Model):
    shade = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    total_quantity = models.IntegerField(default=0)
    status  = models.CharField(max_length=100,null=True,blank=True) # If it's needed later
    
    