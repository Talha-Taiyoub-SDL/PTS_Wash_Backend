from django.db import models


class BatchStage(models.TextChoices):
    FIRST_WASH = "first_wash", "First Wash"
    SECOND_WASH = "second_wash", "Second Wash"
    THIRD_WASH = "third_wash", "Third Wash"
    FINAL_WASH = "final_wash", "Final Wash"

    @classmethod
    def get_stage_map(cls):
        stage_map = {
            cls.FIRST_WASH: "01",
            cls.SECOND_WASH: "02",
            cls.THIRD_WASH: "03",
            cls.FINAL_WASH: "0F",
        }

        return stage_map


class BatchType(models.TextChoices):
    NORMAL_WASH = "normal_wash", "Normal Wash"
    REWASH = "rewash", "Rewash"

    @classmethod
    def get_type_map(cls):
        type_map = {cls.NORMAL_WASH: "N", cls.REWASH: "R"}

        return type_map


class BatchStatus(models.TextChoices):
    READY_TO_WASH = "ready_to_wash", "Ready To Wash"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"


class BatchInputType(models.TextChoices):
    AGGREGATE = "aggregate", "Aggregate"
    PIECES = "pieces", "Pieces"
