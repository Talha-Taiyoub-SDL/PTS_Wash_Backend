from django.db import transaction
from .models import TrackingHistory
from .choices import Action
from rest_framework import serializers
from common.models import GarmentUnit
from common.utils import get_user_name

class TrackingHistorySerializer(serializers.ModelSerializer): 
    class Meta:
        model = TrackingHistory
        fields = ["id", "garment_unit", "stage", "action", "rejection_reason", "scanned_at", "operator"]
        
    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.action != Action.REJECTED:
            data.pop("rejection_reason", None)

        return data    
    
    def validate(self, data):
        action = data.get("action")
        rejection_reason = data.get("rejection_reason")

        if action == Action.REJECTED and not rejection_reason:
            raise serializers.ValidationError({
                "rejection_reason": "This field is required when action is REJECTED."
            })

        if action != Action.REJECTED and rejection_reason:
            raise serializers.ValidationError({
                "rejection_reason": "Should be empty unless action is REJECTED."
            })

        return data
        
    def create(self, validated_data):    
        with transaction.atomic():
            garment_unit = validated_data["garment_unit"]
            
            if garment_unit.status == Action.REJECTED:
                raise serializers.ValidationError({"garment_unit": "This garment is already rejected"})
                
            history = TrackingHistory.objects.create(**validated_data, operator=get_user_name(self.context["request"]))
            
            # Update garment_unit's status
            if validated_data["action"] == Action.REJECTED:
                status = Action.REJECTED
            else:
                status = validated_data["stage"] + "_" + validated_data["action"]
                    
            garment_unit.status = status
            garment_unit.save(update_fields=["status"])
            
            return history    