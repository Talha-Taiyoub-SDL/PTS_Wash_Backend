from django.db import transaction
from production.models import Batch,ReceivedBundle
from production.serializers import get_user_name,ReceivedBundleSerializer,SimpleBatchSerializer
from .models import BatchForFirstWash,FirstWashBatchSource,FirstWashBundleSource,Machine,ProcessFirstWash, ProcessFirstWashHydro, ProcessFirstWashDryer
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
    
class FirstWashBatchSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirstWashBatchSource
        fields = ["batch","quantity"]
            
class FirstWashBundleSourceSerializer(serializers.ModelSerializer):
    bundle = ReceivedBundleSerializer()
    class Meta:
        model = FirstWashBundleSource
        fields = ["bundle","quantity"]    
    
class BatchForFirstWashSerializer(serializers.ModelSerializer):
    source_batches = FirstWashBatchSourceSerializer(many=True,read_only=True)
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
        
    def create(self, validated_data):
        batch_source_data = validated_data.pop("batch_source", None)
        bundle_source_data = validated_data.pop("bundle_source", None)

        created_by = get_user_name(self.context["request"])
        total_quantity = 0
        
        with transaction.atomic():
            # create the batch
            batch_for_first_wash = BatchForFirstWash.objects.create(
                created_by=created_by,
                **validated_data
            )

            #  when the source is batch
            if batch_source_data:
                total_quantity = sum(item["quantity"] for item in batch_source_data)

                for item in batch_source_data:
                    FirstWashBatchSource.objects.create(
                        batch_for_first_wash=batch_for_first_wash,
                        batch=item["batch"],
                        quantity=item["quantity"],
                    )

            # when the source is bundle
            if bundle_source_data:
                total_quantity = sum(item["quantity"] for item in bundle_source_data)

                for item in bundle_source_data:
                    received_bundle = item["bundle"]
                    # Check if the bundle is already allocated
                    if received_bundle.status=="allocated":
                        raise serializers.ValidationError(f"Bundle {received_bundle.id} is already allocated")
                    
                    FirstWashBundleSource.objects.create(
                        batch_for_first_wash=batch_for_first_wash,
                        bundle=received_bundle,
                        quantity=item["quantity"],
                    )
                    
                    # update the received bundle's status
                    received_bundle.status = "allocated"
                    received_bundle.save(update_fields=["status"])

            batch_for_first_wash.total_quantity = total_quantity
            batch_for_first_wash.save()

            return batch_for_first_wash    

class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ["machine_number","SAP","added_at"]

class SimpleFirstWashBatchSourceSerializer(FirstWashBatchSourceSerializer):
    batch = SimpleBatchSerializer(read_only=True)        
 
class SimpleBatchForFirstWashSerializer(serializers.ModelSerializer):
    source_batches = SimpleFirstWashBatchSourceSerializer(many=True, read_only=True)
    source_bundles = FirstWashBundleSourceSerializer(many=True,read_only=True)
    class Meta:
        model = BatchForFirstWash
        fields = ["id","shade","total_quantity","status","source_batches","source_bundles"] 
        
class ProcessFirstWashSerializer(serializers.ModelSerializer):
    batch_for_first_wash = SimpleBatchForFirstWashSerializer(read_only=True)
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
    
                       