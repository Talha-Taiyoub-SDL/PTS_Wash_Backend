from django.db import models

class BatchStage(models.TextChoices):
    FIRST_WASH = "first_wash", "First Wash"
    SECOND_WASH = "second_wash", "Second Wash"

class BatchType(models.TextChoices):
    NORMAL_WASH = "normal_wash", "Normal Wash"
    REWASH = "rewash", "Rewash"

