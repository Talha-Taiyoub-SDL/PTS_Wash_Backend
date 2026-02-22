from .models import BatchForFirstWash
from rest_framework import serializers

class BatchForFirstWashSerializer(serializers.ModelSerializer):
    source = serializers.CharField(max_length=50, write_only=True)
    class Meta:
        model = BatchForFirstWash
        fields = ["id","shade","created_at","created_by","total_quantity","status","source"]
        read_only_fields = ["created_by","total_quantity","status"]