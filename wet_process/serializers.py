from django.db import transaction
from django.utils import timezone
from production.models import Batch,ReceivedBundle
from production.serializers import get_user_name,ReceivedBundleSerializer,SimpleBatchSerializer
from .models import BatchForFirstWash,FirstWashBundleSource,Machine,ProcessFirstWash, ProcessFirstWashHydro, ProcessFirstWashDryer
from rest_framework import serializers


class BatchSourceItemSerializer(serializers.Serializer):
    batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all()
    )
    quantity = serializers.IntegerField(min_value=1)
    
class BundleSourceItemSerializer(serializers.Serializer):
    bundle = serializers.PrimaryKeyRelatedField(
        queryset=ReceivedBundle.objects.all()
    )
    quantity = serializers.IntegerField(min_value=1)
    
# class FirstWashBatchSourceSerializer(serializers.ModelSerializer):
#     class Meta:
#         # model = FirstWashBatchSource
#         fields = ["batch","quantity"]
            
class FirstWashBundleSourceSerializer(serializers.ModelSerializer):
    bundle = ReceivedBundleSerializer()
    class Meta:
        model = FirstWashBundleSource
        fields = ["bundle","quantity"]    
    
class BatchForFirstWashSerializer(serializers.ModelSerializer):
    # source_batches = FirstWashBatchSourceSerializer(many=True,read_only=True)
    source_bundles = FirstWashBundleSourceSerializer(many=True, read_only=True)
    batch_source = BatchSourceItemSerializer(many=True, write_only=True, required = False)
    bundle_source = BundleSourceItemSerializer(
        many=True, write_only=True, required=False
    )
    
    class Meta:
        model = BatchForFirstWash
        fields = ["id","shade","created_at","created_by","total_quantity","status","batch_source","bundle_source","source_batches","source_bundles"]
        read_only_fields = ["created_by","total_quantity","status"]
       
    def validate(self, attrs):
        batch_source = attrs.get("batch_source")
        bundle_source = attrs.get("bundle_source")

         # validate that only one source is provided 
        if batch_source and bundle_source:
            raise serializers.ValidationError(
                "Provide either batch_source or bundle_source, not both."
            )

         # validate that at least one source is provided 
        if not batch_source and not bundle_source:
            raise serializers.ValidationError(
                "You must provide either batch_source or bundle_source."
            )

        return attrs    
        
    # def create(self, validated_data):
    #     batch_source_data = validated_data.pop("batch_source", None)
    #     bundle_source_data = validated_data.pop("bundle_source", None)

    #     created_by = get_user_name(self.context["request"])
    #     total_quantity = 0
        
    #     with transaction.atomic():
    #         # create the batch
    #         batch_for_first_wash = BatchForFirstWash.objects.create(
    #             created_by=created_by,
    #             **validated_data
    #         )

    #         #  when the source is batch
    #         if batch_source_data:
    #             total_quantity = sum(item["quantity"] for item in batch_source_data)

    #             for item in batch_source_data:
    #                 FirstWashBatchSource.objects.create(
    #                     batch_for_first_wash=batch_for_first_wash,
    #                     batch=item["batch"],
    #                     quantity=item["quantity"],
    #                 )

    #         # when the source is bundle
    #         if bundle_source_data:
    #             total_quantity = sum(item["quantity"] for item in bundle_source_data)

    #             for item in bundle_source_data:
    #                 received_bundle = item["bundle"]
    #                 # Check if the bundle is already allocated
    #                 if received_bundle.status=="allocated":
    #                     raise serializers.ValidationError(f"Bundle {received_bundle.id} is already allocated")
                    
    #                 FirstWashBundleSource.objects.create(
    #                     batch_for_first_wash=batch_for_first_wash,
    #                     bundle=received_bundle,
    #                     quantity=item["quantity"],
    #                 )
                    
    #                 # update the received bundle's status
    #                 received_bundle.status = "allocated"
    #                 received_bundle.save(update_fields=["status"])

    #         batch_for_first_wash.total_quantity = total_quantity
    #         batch_for_first_wash.save()

    #         return batch_for_first_wash    

class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ["machine_number","SAP","added_at"]

# class SimpleFirstWashBatchSourceSerializer(FirstWashBatchSourceSerializer):
#     batch = SimpleBatchSerializer(read_only=True)        
 
# class SimpleBatchForFirstWashSerializer(serializers.ModelSerializer):
#     source_batches = SimpleFirstWashBatchSourceSerializer(many=True, read_only=True)
#     source_bundles = FirstWashBundleSourceSerializer(many=True,read_only=True)
#     class Meta:
#         model = BatchForFirstWash
#         fields = ["id","shade","total_quantity","status","source_batches","source_bundles"] 
        
class ProcessFirstWashSerializer(serializers.ModelSerializer):
    # batch_for_first_wash = SimpleBatchForFirstWashSerializer(read_only=True)
    machine = MachineSerializer(read_only=True)
    
    class Meta:
        model = ProcessFirstWash
        fields = ["id","batch_for_first_wash","machine","loading_start","loading_started_by","loading_finish","loading_finished_by","process_finish","process_finished_by","unload_finish","unload_finished_by"]

class CreateProcessFirstWashSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessFirstWash   
        fields = ["batch_for_first_wash","machine"]
        
    def create(self, validated_data):
        first_wash = ProcessFirstWash.objects.create(**validated_data,loading_started_by = get_user_name(self.context["request"]))
        return first_wash
    
class UpdateProcessFirstWashSerializer(serializers.ModelSerializer):
    state = serializers.CharField(max_length=100, write_only=True)
    
    class Meta:
        model = ProcessFirstWash
        fields = ["state"]
        
    def update(self, instance: ProcessFirstWash, validated_data):
        # Map of timestamp fields to the user field who completed them
        timestamp_to_user_field = {
            "loading_finish": "loading_finished_by",
            "process_finish": "process_finished_by",
            "unload_finish": "unload_finished_by"
        }

        state_field = validated_data.get("state")
        if state_field not in timestamp_to_user_field:
            raise serializers.ValidationError("You have to provide a validated state")

        # Check if the state has already been completed
        if getattr(instance, state_field) is not None:
            raise serializers.ValidationError("You've already completed this state")

        # Get the corresponding "finished by" field
        finished_by_field = timestamp_to_user_field[state_field]

        # Update timestamp and user who finished it
        setattr(instance, state_field, timezone.now())
        setattr(instance, finished_by_field, get_user_name(self.context["request"]))
        instance.save(update_fields=[state_field, finished_by_field])

        return instance
        
class ProcessFirstWashHydroSerializer(serializers.ModelSerializer):
    # batch_for_first_wash = SimpleBatchForFirstWashSerializer(read_only=True)
    
    class Meta:
        model = ProcessFirstWashHydro
        fields = ["id","batch_for_first_wash","machine","hydro_in","hydro_in_by","hydro_out","hydro_out_by"]
        
class CreateProcessFirstWashHydroSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessFirstWashHydro
        fields = ["batch_for_first_wash","machine"]       
    
    def create(self, validated_data):
        first_wash_hydro = ProcessFirstWashHydro.objects.create(**validated_data,hydro_in_by=get_user_name(self.context["request"]))            
        return first_wash_hydro                               

class UpdateProcessFirstWashHydroSerializer(serializers.ModelSerializer):
    state = serializers.CharField(max_length=100)
    class Meta:
        model = ProcessFirstWashHydro
        fields = ["state"]    
    
    def update(self, instance:ProcessFirstWashHydro, validated_data):
        state = validated_data["state"]
        
        if state != "hydro_out":
            raise serializers.ValidationError("You have to provide validated state")
        
        if getattr(instance,state) is not None:
            raise serializers.ValidationError("You've already completed this state")
    
        instance.hydro_out = timezone.now()
        instance.hydro_out_by = get_user_name(self.context["request"])
        instance.save(update_fields=["hydro_out","hydro_out_by"])
        
        return instance
    
class ProcessFirstWashDryerSerializer(serializers.ModelSerializer):
    # We will not take input for this field from the frontend.
    dryer_in_by = serializers.CharField(max_length=100, read_only=True)
    
    class Meta:
        model = ProcessFirstWashDryer
        fields = ["id","batch_for_first_wash","machine","type","dryer_in","dryer_in_by","dryer_out","dryer_out_by"]
        
    # Replace the batch_for_first_wash ID with its nested serialized data in responses,
    # while still allowing it to be written as a primary key during create.
    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     representation["batch_for_first_wash"] = SimpleBatchForFirstWashSerializer(
    #         instance.batch_for_first_wash
    #     ).data
    #     return representation
    
    def create(self, validated_data):
        first_wash_dryer = ProcessFirstWashDryer.objects.create(**validated_data, dryer_in_by = get_user_name(self.context["request"]))
        return first_wash_dryer        
   
class UpdateProcessFirstWashDryerSerializer(serializers.ModelSerializer):
    state = serializers.CharField(max_length=100)
    
    class Meta:
        model= ProcessFirstWashDryer
        fields = ["state"]
        
    def update(self, instance:ProcessFirstWashDryer, validated_data):
        state = validated_data["state"]
        
        if state != "dryer_out":
            raise serializers.ValidationError("You have to provide validated state")
        
        if getattr(instance,state) is not None:
            raise serializers.ValidationError("You've already completed this state")
    
        instance.dryer_out = timezone.now()
        instance.dryer_out_by = get_user_name(self.context["request"])
        instance.save(update_fields=["dryer_out","dryer_out_by"])
        
        return instance
                        