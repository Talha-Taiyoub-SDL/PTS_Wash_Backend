from django.db import models

class Stage(models.TextChoices):
    WHISKER = "whisker", "Whisker"
    LASER_WHISKER = "laser_whisker", "Laser Whisker"
    BRUSH = "brush", "Brush"
    LASER_BRUSH = "laser_brush", "Laser Brush"
    WRINKLE = "wrinkle", "Wrinkle"
    TAG = "tag", "Tag"
    TIE = "tie", "Tie"
    
class Action(models.TextChoices):
    IN = "in", "In"
    OUT = "out", "Out"
    REJECTED = "rejected", "Rejected"    