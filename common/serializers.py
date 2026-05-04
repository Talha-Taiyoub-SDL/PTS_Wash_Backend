from rest_framework import serializers
from django.db import transaction
from .models import MasterPlan, RouteStep, SubRouteStep, GarmentUnit
from .utils import get_user_name

class SubRouteStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubRouteStep
        fields = ["id", "sequence", "stage"]

class RouteStepSerializer(serializers.ModelSerializer):
    sub_steps = SubRouteStepSerializer(many=True)
    class Meta:
        model = RouteStep
        fields = ["id", "sequence", "stage", "sub_steps"]
        
class MasterPlanSerializer(serializers.ModelSerializer):
    route_steps = RouteStepSerializer(many=True)
    class Meta:
        model = MasterPlan
        fields = ["id", "buyer", "style", "color", "last_update", "updated_by", "route_steps"]        

class SubRouteStepInputSerializer(serializers.Serializer):
    stage = serializers.CharField()

class RouteStepInputSerializer(serializers.Serializer):
    stage = serializers.CharField()
    sub_steps = SubRouteStepInputSerializer(many=True, required=False)

class CreateMasterPlanSerializer(serializers.ModelSerializer):
    route_steps = RouteStepInputSerializer(many=True)
    class Meta:
        model = MasterPlan
        fields = ["id", "buyer", "style", "color", "last_update", "updated_by", "route_steps"]
        read_only_fields = ["updated_by"]
        
    def create(self, validated_data):
        with transaction.atomic():
            route_steps = validated_data.pop("route_steps")
            master_plan = MasterPlan.objects.create(**validated_data, updated_by=get_user_name(self.context["request"]))
            
            for sequence, route_step in enumerate(route_steps, start=1):
                stage = route_step["stage"]
                sub_steps = route_step["sub_steps"]
                route_step = RouteStep.objects.create(master_plan=master_plan, sequence=sequence, stage=stage)
                
                for sequence, sub_step in enumerate(sub_steps, start=1):
                    SubRouteStep.objects.create(route_step=route_step, sequence=sequence, stage=sub_step["stage"])
                    
            return master_plan                    
                
class GarmentUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = GarmentUnit
        fields = ["id", "individual_barcode", "so", "mpo", "buyer", "style", "marker", "size", "shade", "color", "status", "received_at", "received_by"]                
                
    def create(self, validated_data):
        garment_unit = GarmentUnit.objects.create(**validated_data, received_by=get_user_name(self.context["request"]))
        return garment_unit            
                