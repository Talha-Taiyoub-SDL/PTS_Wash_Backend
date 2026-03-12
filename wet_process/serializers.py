from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from production.models import Batch,ReceivedBundle
from production.serializers import get_user_name,ReceivedBundleSerializer,SimpleBatchSerializer
from .models import BatchForFirstWash,FirstWashBundleSource,Machine,ProcessFirstWash, ProcessFirstWashHydro, ProcessFirstWashDryer,  FirstWashBatchSource, WashLog, Rejection
from rest_framework import serializers
    
class FirstWashBatchSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirstWashBatchSource
        fields = ["id","mpo","style","so","quantity"]
        read_only_fields = ["batch_for_first_wash"]
            
class FirstWashBundleSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirstWashBundleSource
        fields = ["id","received","quantity"]
        read_only_fields = ["batch_for_first_wash"]
        
    # Allowing received as an id when it's taken as input, providing details when it's sent back as a response
    def to_representation(self, instance:FirstWashBundleSource):
        representation = super().to_representation(instance)
        representation["received"] = ReceivedBundleSerializer(
            instance.received
        ).data
        return representation        
    
class BatchForFirstWashSerializer(serializers.ModelSerializer):
    source_batches = FirstWashBatchSourceSerializer(many=True, required=False)
    source_bundles = FirstWashBundleSourceSerializer(many=True, required=False)
    total_quantity = serializers.SerializerMethodField(method_name="get_total_quantity",read_only=True)
    
    class Meta:
        model = BatchForFirstWash
        fields = ["id","buyer","color","shade","total_quantity","source_batches","source_bundles","created_at","created_by"]
        read_only_fields = ["created_by"]
        
    def get_total_quantity(self,instance:BatchForFirstWash):
        if instance.source_batches.exists():
            total_quantity = sum(item.quantity for item in instance.source_batches.all())
        else:
            total_quantity = sum(item.quantity for item in instance.source_bundles.all())

        return total_quantity
               
    def validate(self, attrs):
        source_batches = attrs.get("source_batches")
        source_bundles = attrs.get("source_bundles")

         # validate that only one source is provided 
        if source_batches and source_bundles:
            raise serializers.ValidationError(
                "Provide either source_batches or source_bundles, not both."
            )

         # validate that at least one source is provided 
        if not source_batches and not source_bundles:
            raise serializers.ValidationError(
                "You must provide either source_batches or source_bundles."
            )

        return attrs    
        
    def create(self, validated_data):
        source_batches_data = validated_data.pop("source_batches", None)
        source_bundles_data = validated_data.pop("source_bundles", None)

        created_by = get_user_name(self.context["request"])
        total_quantity = 0
        
        with transaction.atomic():
            # create the batch
            batch_for_first_wash = BatchForFirstWash.objects.create(
                created_by=created_by,
                **validated_data
            )

            #  when the source is batch
            if source_batches_data:
                total_quantity = sum(item["quantity"] for item in source_batches_data)

                for item in source_batches_data:
                    FirstWashBatchSource.objects.create(
                        batch_for_first_wash = batch_for_first_wash,
                        mpo = item["mpo"],
                        style = item["style"],
                        so = item["so"],
                        quantity = item["quantity"],
                    )

            # when the source is bundle
            if source_bundles_data:
                total_quantity = sum(item["quantity"] for item in source_bundles_data)

                for item in source_bundles_data:
                    received_bundle = item["received"]
                    
                    # Check if the bundle is already allocated
                    if received_bundle.status=="allocated":
                        raise serializers.ValidationError(f"Bundle {received_bundle.id} is already allocated")
                    
                    FirstWashBundleSource.objects.create(
                        batch_for_first_wash=batch_for_first_wash,
                        received = received_bundle,
                        quantity=item["quantity"],
                    )
                    
                    # update the received bundle's status
                    received_bundle.status = "allocated"
                    received_bundle.save(update_fields=["status"])

            # Create the log object for this batch
            content_type = ContentType.objects.get_for_model(batch_for_first_wash)
            WashLog.objects.create(content_type=content_type, object_id=batch_for_first_wash.id, total_quantity=total_quantity)
            
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
    batch_for_first_wash = SimpleBatchForFirstWashSerializer(read_only=True)
    
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
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["batch_for_first_wash"] = SimpleBatchForFirstWashSerializer(
            instance.batch_for_first_wash
        ).data
        return representation
    
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
                        
class RejectionSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField(max_length=100)
    class Meta:
        model = Rejection
        fields = ["id","individual_barcode","reason","stage","rejected_at","rejected_by","content_type","object_id"]
        read_only_fields = ["rejected_by", "source_batch"]
    
    def to_representation(self, instance:Rejection):
        representation= super().to_representation(instance)
        representation["content_type"] = instance.content_type.model
        return representation
        
    def create(self, validated_data):
        content_type = ContentType.objects.get(model=validated_data.pop("content_type", None))
        
        rejection = Rejection.objects.create(**validated_data, rejected_by=get_user_name(self.context["request"]),content_type=content_type)
        
        #update the rejection quantity in the wash log
        rejection.source_batch.logs.update(rejections=F("rejections") + 1)
        return rejection
                                    