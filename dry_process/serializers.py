from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from .models import TrackingHistory
from .choices import Action
from rest_framework import serializers
from common.utils import get_user_name
from production.models import Planning, PlanningRouteStep

class TrackingHistorySerializer(serializers.ModelSerializer): 
    class Meta:
        model = TrackingHistory
        fields = ["id", "garment_unit", "stage", "action", "rejection_reason", "scanned_at", "operator"]
        validators = []
    
    # Remove rejection_reason from the response if the action is not "rejected"    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.action != Action.REJECTED:
            data.pop("rejection_reason", None)

        return data    
    
    def validate(self, data):
        garment_unit = data.get("garment_unit")
        
        # Check already rejected
        if garment_unit.status == Action.REJECTED:
            raise serializers.ValidationError({
                "garment_unit": "This garment is already rejected"
            })
        
        # Check if planning exist for the MPO the garment belongs to
        try:
            planning = Planning.objects.get(mpo=garment_unit.mpo)
            
            # Check if this is a valid stage.
            try:
                route_step = planning.route_steps.get(stage=data.get("stage"))
                # We've to start again from this place  
                
            except PlanningRouteStep.DoesNotExist:
                raise serializers.ValidationError({
                    "stage": "This stage does not exist for the MPO this garment belongs to"            
                    })
        
        except Planning.DoesNotExist:
            raise serializers.ValidationError({"garment_unit": "Planning does not exist for the MPO this garment belongs to"})    
        
        # Check if this stage is already completed    
        if TrackingHistory.objects.filter(
            garment_unit=garment_unit,
            stage=data.get("stage"),
            action=data.get("action")
        ).exists():
            raise serializers.ValidationError({
                "non_field_errors": "This action already exists for this garment at this stage."
            })    
        
        # If the action is "rejected", rejection_reason must be included, otherwise not
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
            # Create history for the action specified in the data sent by the user    
            history = TrackingHistory.objects.create(**validated_data, operator=get_user_name(self.context["request"]))
            
            # Update garment_unit's status
            garment_unit = validated_data["garment_unit"]
            
            if validated_data["action"] == Action.REJECTED:
                status = Action.REJECTED
            else:
                status = validated_data["stage"] + "_" + validated_data["action"]
                    
            garment_unit.status = status
            garment_unit.save(update_fields=["status"])
            
            return history    