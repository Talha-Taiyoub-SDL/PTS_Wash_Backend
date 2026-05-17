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
    
class RejectionReason(models.TextChoices):
    COLOR_MISMATCH = "color_mismatch", "Color Mismatch"
    SHADE_VARIATION = "shade_variation", "Shade Variation"
    STAIN = "stain", "Stain"
    DAMAGE = "damage", "Damage"
    MEASUREMENT_ISSUE = "measurement_issue", "Measurement Issue"
    FABRIC_DEFECT = "fabric_defect", "Fabric Defect"
    PRINT_DEFECT = "print_defect", "Print Defect"
    SEWING_DEFECT = "sewing_defect", "Sewing Defect"
    OTHER = "other", "Other"
        